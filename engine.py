import os
import random
from enum import Enum
from typing import List, Tuple

import streamlit as st
from openai import OpenAI

DEFAULT_SPYMASTER_PROMPT = """The words to guess on your team are: {SLF}.
The words on your opponent's team NOT to guess are: {NTR}.
The neutral words not to guess are: {OPP}.
The forbidden word  REALLY NOT to guess is: {KLL}.

Give me your best hint."""


DEFAULT_SPYMASTER_INSTRUCT = """You are playing your favorite game, Codenames, as the spymaster giving hints.
Your answers should be in the format WORD - NUMBER."""

FULL_LANGUAGES = {
    "cz": "Czech",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "Fremnh",
    "it": "Italian",
}


@st.cache_data
def get_lang_options() -> List[str]:
    """Get available language options"""
    return [x[:-4] for x in os.listdir("words_lists") if x.endswith(".txt")]


@st.cache_data
def get_default_words_list(lang: str = "en") -> List[str]:
    """Returns the default list of words for the given language"""
    with open(os.path.join("words_lists", f"{lang}.txt"), "r") as open_file:
        words_list = open_file.read().upper()
    return words_list


@st.cache_resource
def get_openai_client(api_key: str) -> OpenAI:
    """Returns an OpenAI client"""
    client = OpenAI(api_key=api_key)
    available_models = [x.id for x in client.models.list()]
    return client, available_models


@st.cache_data
def generate_board(
    words_list: List[str], side_length: int = 5, random_seed: int = 42
) -> Tuple[List[str], List[int]]:
    """Generate a board of `side_length**2` words"""
    words_list = [x.strip() for x in words_list.splitlines() if len(x.strip())]
    random.seed(random_seed)
    random.shuffle(words_list)
    # TODO: Adapt number of cards to larger board
    team_assignment = [-1] * 1 + [0] * 7 + [1] * 8 + [2] * (side_length**2 - 16)
    random.shuffle(team_assignment)
    return words_list[: side_length**2], team_assignment


def generate_spymaster_prompt(
    words: List[str], team_assignment: List[int]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """ "Separate words on the board in their respective teams"""
    SLF, OPP, NTR, KLL = [], [], [], []
    for idx, (w, a) in enumerate(zip(words, team_assignment)):
        if a == -1:
            KLL.append(w)
        elif a == 0:
            NTR.append(w)
        elif a == 1:
            OPP.append(w)
        elif a == 2:
            SLF.append(w)
    return SLF, OPP, NTR, KLL


class MessageType(Enum):
    """Type of messages added to the chat history during conversation with the Spymaster"""

    Prompt = 0
    Guess = 1
    Hint = 2
    Instruct = 3


class Spymaster:
    """Base Spymaster type"""

    def __init__(
        self, client, model_name: str, use_last_prompt_only: bool = False
    ) -> None:
        self.client = client
        self.model_name = model_name
        self._prompt = DEFAULT_SPYMASTER_PROMPT
        self.current_hint_word = None
        self.og_hint_num = 0
        self.current_hint_num = 0
        self.chat_history = [
            [
                (
                    MessageType.Instruct,
                    {"role": "system", "content": DEFAULT_SPYMASTER_INSTRUCT},
                ),
            ]
            for _ in range(2)
        ]
        self.use_last_prompt_only = use_last_prompt_only
        self.current_team = 1

    def words(self, team: int) -> List[str]:
        """Return words belonging to the given team and still on the board"""
        return self.slf if team == 1 else self.opp

    def get_history(self, team: int) -> str:
        """Return chat history for the given team with markdown formatting"""
        return "\n\n".join(
            f"**{x['content']}**"
            if msg_type == MessageType.Hint
            else f"  * {x['content']}"
            for msg_type, x in self.chat_history[team]
            if msg_type in [MessageType.Guess, MessageType.Hint]
        )

    def update_words(self, words: List[str], team_assignment: List[int]) -> None:
        """Update the words and team assignments"""
        self.slf, self.opp, self.ntr, self.kll = generate_spymaster_prompt(
            words, team_assignment
        )

    def update_prompt(self, prompt: str) -> None:
        """Update the prompt template"""
        self._prompt = prompt

    def update_instruct(self, instruct: str) -> None:
        """Update the base system instruct"""
        for lst in self.chat_history:
            lst[0][1]["content"] = instruct

    def use_whole_history(self, enabled: bool) -> None:
        """Whether to use the whole chat history or not"""
        self.use_last_prompt_only = not enabled

    @property
    def prompt(self) -> str:
        """Format prompt with the current words"""
        return self._prompt.format(
            SLF=", ".join(self.words(self.current_team)),
            OPP=", ".join(self.words(1 - self.current_team)),
            NTR=", ".join(self.ntr),
            KLL=", ".join(self.kll),
        )

    def remove(self, word: str, team: int) -> None:
        """Action of guessing the given `word` which is assigned to the given `team`

        :param word: Word clicked on the board
        :param team: Word's team assignment. -1 for the killer card (instant loss),
            0 for neutral card, 1 and 2 for either the blue or red team
        """
        self.chat_history[self.current_team].append(
            (
                MessageType.Guess,
                {"role": "user", "content": f"Your teammate picked {word}"},
            ),
        )

        # Guessed the killer card :(
        if team == -1:
            self.kll.remove(word)

        # Guessed a neutral or opponent : end turn
        elif team == 0 or team != (self.current_team + 1):
            (self.ntr if team == 0 else self.words(1 - self.current_team)).remove(word)
            self.end_turn()

        # Guessed a correct word: we only continue if we have left over guesses + 1
        else:
            self.current_hint_num -= 1
            self.words(self.current_team).remove(word)
            if self.current_hint_num < 0:
                self.end_turn()

    def end_turn(self) -> None:
        """End turn immediately"""
        self.current_hint_word = None
        self.current_team = 1 - self.current_team

    def give_hint(self, num_retries: int = 2, debug: bool = True) -> None:
        """Generates hint by prompting the language model

        :param num_retries: Number of retries in case the generated hint is
            badly formatted
        :param debug: If True, print more verbose output
        """
        self.chat_history[self.current_team].append(
            (MessageType.Prompt, {"role": "user", "content": self.prompt})
        )

        if debug:
            print(
                "\n\n".join(
                    f"{msg_type} - {x['content']}"
                    for msg_type, x in self.chat_history[self.current_team]
                )
            )

        self.current_hint_num = -1
        while self.current_hint_num < 1 and num_retries >= 0:
            try:
                # Prompt assistant
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        self.chat_history[self.current_team][0][1],
                        self.chat_history[self.current_team][-1][1],
                    ]
                    if self.use_last_prompt_only
                    else [x[1] for x in self.chat_history[self.current_team]],
                )
                out = completion.choices[0].message.content.split("-")

                # Parse response until we get a valid hint
                hint_word, self.current_hint_num = out[0].strip().upper(), int(
                    out[-1].strip().replace(".", "")
                )
                if self.current_hint_num >= 1:
                    self.current_hint_word = hint_word
                    self.og_hint_num = self.current_hint_num
                    self.chat_history[self.current_team].append(
                        (
                            MessageType.Hint,
                            {
                                "role": "assistant",
                                "content": f"{self.current_hint_word} - {self.current_hint_num}",
                            },
                        )
                    )
            except ValueError:
                pass
            num_retries -= 1
        if num_retries == 0:
            raise ValueError

    def play(self) -> Tuple[str, int]:
        """Display action in the hint box based on the current game's state"""
        fmt = ":blue[{}]" if self.current_team == 1 else ":red[{}]"

        # Check if we lost by guessing the killer card in the previous action
        if len(self.kll) == 0:
            return (
                fmt.format("You found the killer. You lost ☠️"),
                -1,
            )

        # Check if we lost by guessing the opponent's last word
        if len(self.words(1 - self.current_team)) == 0:
            return (
                fmt.format("You guessed for the other team.You lost ☠️"),
                -1,
            )

        # Check if we won
        if len(self.words(self.current_team)) == 0:
            return fmt.format("You guessed all your cards. You win 🪩 !"), 1

        # Otherwise, give a hint and continue
        if self.current_hint_word is None:
            self.give_hint()
        return (
            fmt.format(f"{self.current_hint_word} - {self.og_hint_num}")
            + "   \n"
            + fmt.format(f"({self.current_hint_num+ 1} guesses left)"),
            0,
        )


@st.cache_resource
def init_spymaster(
    _client: OpenAI, model_name: str, words: List[str], team_assignment: List[int]
) -> Spymaster:
    """Init the spymaster object"""
    spymaster = Spymaster(_client, model_name)
    spymaster.update_words(words, team_assignment)
    return spymaster
