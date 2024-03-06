from typing import Optional

import streamlit as st

__PERSISTENT_KEYS__ = set()


def persist_key(key: str) -> str:
    """Mark widget key as persistent"""
    __PERSISTENT_KEYS__.add(key)
    return key


SETTINGS_PAGE_NAME = "Settings"
SPYMASTER_PROMPT_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_spymaster_prompt")

DEFAULT_SPYMASTER_PROMPT = """Your words to guess are: {SLF}.
Your opponent's words to avoid are: {OPP}.
The neutral words to avoid are: {NTR}.
The forbidden word to really avoid is: {KLL}.

Give a hint."""

SPYMASTER_INSTRUCT_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_spymaster_instruct")

DEFAULT_SPYMASTER_INSTRUCT = """You are playing the game Codenames as the spymaster to give hints.
Your answers should be in the format WORD - NUMBER."""


def persist_session_state(page_name: Optional[str] = None) -> None:
    """Force storage of all persistent keys in session state"""
    for k, v in st.session_state.items():
        if (
            k in __PERSISTENT_KEYS__
            and isinstance(k, str)
            and (page_name is None or not k.startswith(page_name))
        ):
            st.session_state[k] = v
