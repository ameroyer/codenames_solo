import sys

import streamlit as st

sys.path.append("..")
from engine import DEFAULT_SPYMASTER_INSTRUCT, DEFAULT_SPYMASTER_PROMPT
from persistent_state import SETTINGS_PAGE_NAME as __PAGE_NAME__
from persistent_state import (
    SPYMASTER_INSTRUCT_KEY,
    SPYMASTER_PROMPT_KEY,
    persist_key,
    persist_session_state,
)

# Configure OpenAI Assistant for the spymaster role
st.subheader("Spymaster")
spymaster_assistant_instruct = st.text_area(
    label="Assistant Instruction",
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

# Persist session state across pages
persist_session_state(__PAGE_NAME__)
