from typing import Tuple

import numpy as np
import streamlit as st
from openai import OpenAI

DEFAULT_SPYMASTER_PROMPT = """The words to guess on your team are: {SLF}.
The words on your opponent's team NOT to guess are: {NTR}.
The neutral words not to guess are: {OPP}.
The forbidden word  REALLY NOT to guess is: {KLL}.

Give me your best hint."""


DEFAULT_SPYMASTER_INSTRUCT = """You are playing the game Codenames as a great spymaster giving hints.
Your answers should be in the format WORD - NUMBER."""


@st.cache_resource
def get_openai_client(api_key: str):
    client = OpenAI(api_key=api_key)
    available_models = [x.id for x in client.models.list()]
    return client, available_models


@st.cache_data
def generate_board(side_length: int = 5):
    with open("words.txt", "r") as open_file:
        words_list = open_file.read().splitlines()

    side_length = 5
    words = np.random.choice(words_list, side_length**2, replace=False)
    team_assignment = [-1] * 1 + [0] * 7 + [1] * 8 + [2] * 9
    team_assignment = np.random.permutation(team_assignment)
    return words, team_assignment


def generate_spymaster_prompt(words, team_assignment):
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


class Spymaster:
    def __init__(self, client, model_name: str, use_last_prompt_only: bool = False):
        self.client = client
        self.model_name = model_name
        self._prompt = DEFAULT_SPYMASTER_PROMPT
        self.instruct = DEFAULT_SPYMASTER_INSTRUCT
        self.current_hint_word = None
        self.current_hint_num = 0
        self.chat_history = [
            [
                {"role": "system", "content": self.instruct},
            ]
            for _ in range(2)
        ]
        self.use_last_prompt_only = use_last_prompt_only
        self.current_team = 1

    def get_history(self, team: int):
        return "\n\n".join(
            x["content"] for x in self.chat_history[team] if x["role"] == "assistant"
        )

    def update_words(self, words, team_assignment):
        self.slf, self.opp, self.ntr, self.kll = generate_spymaster_prompt(
            words, team_assignment
        )

    def update_prompt(self, prompt: str):
        self._prompt = prompt

    @property
    def prompt(self):
        return self._prompt.format(
            SLF=", ".join(self.slf if self.current_team == 1 else self.opp),
            OPP=", ".join(self.opp if self.current_team == 1 else self.slf),
            NTR=", ".join(self.ntr),
            KLL=", ".join(self.kll),
        )

    def remove(self, word, team):
        self.chat_history[self.current_team].append(
            {"role": "user", "content": f"Your teammates guessed the word {word}"},
        )
        # Guessed the killer card :(
        if team == -1:
            self.kll.remove(word)
        # Guessed a neutral or opponent : end turn
        elif team == 0 or team != (self.current_team + 1):
            self.current_hint_word = None
            (
                self.ntr
                if team == 0
                else self.opp
                if self.current_team == 1
                else self.slf
            ).remove(word)
            self.current_team = 1 - self.current_team
        # Guessed a correct work: we only continue if we have left over guesses
        else:
            self.current_hint_num -= 1
            if self.current_hint_num < 0:
                self.current_hint_word = None
                self.current_team = 1 - self.current_team
            (self.slf if self.current_team == 1 else self.opp).remove(word)

    def end_turn(self):
        self.current_hint_word = None
        self.current_team = 1 - self.current_team

    def give_hint(self, num_trials=2):
        self.chat_history[self.current_team].append(
            {"role": "user", "content": self.prompt}
        )
        self.current_hint_num = -1
        while self.current_hint_num < 1 and num_trials >= 0:
            try:
                # Prompt assistant
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        self.chat_history[self.current_team][0],
                        self.chat_history[self.current_team][-1],
                    ]
                    if self.use_last_prompt_only
                    else self.chat_history[self.current_team],
                )
                out = completion.choices[0].message.content.split("-")

                # Parse response until we get a valid hint
                hint_word, self.current_hint_num = out[0].strip().upper(), int(
                    out[-1].strip().replace(".", "")
                )
                if self.current_hint_num >= 1:
                    self.current_hint_word = hint_word
                    self.chat_history[self.current_team].append(
                        {
                            "role": "assistant",
                            "content": f"{self.current_hint_word} - {self.current_hint_num}",
                        }
                    )
            except ValueError:
                pass
            num_trials -= 1
        if num_trials == 0:
            raise ValueError

    def play(self) -> Tuple[str, bool]:
        fmt = (
            ":blue[{word} - {num}]"
            if self.current_team == 1
            else ":red[{word} - {num}]"
        )
        # Check if we lost by guessing the killer card in the previous action
        if len(self.kll) == 0:
            return (
                fmt.format(word="Your guessed the killer card.", num="You lost ☠️"),
                True,
            )

        # Give a hint
        if self.current_hint_word is None:
            self.give_hint()

        if (self.current_team == 1 and len(self.slf) == 0) or (
            self.current_team == 2 and len(self.opp) == 0
        ):
            return fmt.format(word="You found all your cards.", num="You win 🪩 !"), True
        return fmt.format(word=self.current_hint_word, num=self.current_hint_num), False


@st.cache_resource
def init_spymaster(_client, model_name, words, team_assignment):
    spymaster = Spymaster(_client, model_name)
    spymaster.update_words(words, team_assignment)
    return spymaster
