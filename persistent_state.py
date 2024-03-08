from typing import Optional

import streamlit as st

__PERSISTENT_KEYS__ = set()


def persist_key(key: str) -> str:
    """Mark widget key as persistent"""
    global __PERSISTENT_KEYS__
    __PERSISTENT_KEYS__.add(key)
    return key


"""Define Settings keys that will be used by both the Settings and Game page"""
SETTINGS_PAGE_NAME = "Settings"
SPYMASTER_TEMP_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_temperature")
SPYMASTER_PROMPT_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_spymaster_prompt")
SPYMASTER_INSTRUCT_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_spymaster_instruct")
SPYMASTER_BEHAVIOR_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_spymaster_behavior")
BOARD_WORDS_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_word_list")
BOARD_LANG_KEY = persist_key(f"{SETTINGS_PAGE_NAME}_word_lang")


def persist_session_state(page_name: Optional[str] = None) -> None:
    """Force storage of all persistent keys from other papges in session state"""
    for k, v in st.session_state.items():
        if (
            k in __PERSISTENT_KEYS__
            and isinstance(k, str)
            and (page_name is None or not k.startswith(page_name))
        ):
            st.session_state[k] = v
