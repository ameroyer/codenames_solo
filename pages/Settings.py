import sys

import streamlit as st

sys.path.append("..")
from engine import (
    DEFAULT_SPYMASTER_INSTRUCT,
    DEFAULT_SPYMASTER_PROMPT,
    get_default_words_list,
    get_lang_options,
)
from persistent_state import BOARD_LANG_KEY, BOARD_WORDS_KEY
from persistent_state import SETTINGS_PAGE_NAME as __PAGE_NAME__
from persistent_state import (
    SPYMASTER_BEHAVIOR_KEY,
    SPYMASTER_INSTRUCT_KEY,
    SPYMASTER_PROMPT_KEY,
    persist_session_state,
)

# Configure OpenAI Assistant for the spymaster role
st.subheader("Spymaster parameters")
st.markdown(
    "*Note that these parameters will start taking effect at the next hint given*"
)

st.checkbox(
    label="Use the whole history when prompting", value=True, key=SPYMASTER_BEHAVIOR_KEY
)

st.text_area(
    label="System Instruction",
    value=st.session_state.get(SPYMASTER_INSTRUCT_KEY, DEFAULT_SPYMASTER_INSTRUCT),
    key=SPYMASTER_INSTRUCT_KEY,
)

spymaster_prompt = st.text_area(
    label="Spymaster Prompt :green[(Ctrl + Enter to refresh preview)]",
    value=st.session_state.get(SPYMASTER_PROMPT_KEY, DEFAULT_SPYMASTER_PROMPT),
    key=SPYMASTER_PROMPT_KEY,
)

st.markdown(":green[Preview]")
st.text(
    spymaster_prompt.format(
        SLF="<King, Apple, Bank>",
        OPP="<Octopus, Frankenstein, Eagle>",
        NTR="<Slip, Bee, Ivory>",
        KLL="<Platypus>",
    )
)


# Configure the list of words to build the board
st.subheader("Word List")
options = get_lang_options()
try:
    default_index = options.index("en")
except ValueError:
    default_index = 0


def __update_lang__() -> None:
    del st.session_state[BOARD_WORDS_KEY]


lang = st.selectbox(
    label="Select Language",
    options=options,
    index=options.index(st.session_state[BOARD_LANG_KEY])
    if BOARD_LANG_KEY in st.session_state
    else default_index,
    key=BOARD_LANG_KEY,
    on_change=__update_lang__,
)

st.text_area(
    label="Edit words list",
    value=st.session_state.get(BOARD_WORDS_KEY, get_default_words_list(lang)),
    key=BOARD_WORDS_KEY,
)

# Persist session state across pages
persist_session_state(__PAGE_NAME__)
