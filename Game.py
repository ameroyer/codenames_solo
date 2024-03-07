import random
from functools import partial

import streamlit as st

from engine import (
    generate_board,
    get_default_words_list,
    get_openai_client,
    init_spymaster,
)
from persistent_state import (
    BOARD_LANG_KEY,
    BOARD_WORDS_KEY,
    SPYMASTER_BEHAVIOR_KEY,
    SPYMASTER_INSTRUCT_KEY,
    SPYMASTER_PROMPT_KEY,
    persist_key,
    persist_session_state,
)
from styling import TEAM_TO_STYLE, set_game_style

__PAGE_NAME__ = "Game"
st.set_page_config(layout="wide")

# Random seed
# will only be updated when rerunning the game
if f"{__PAGE_NAME__}_random_seed" not in st.session_state:
    st.session_state[f"{__PAGE_NAME__}_random_seed"] = random.randint(0, 1000)

# API parameters
openai_api_key = persist_key(f"{__PAGE_NAME__}_api_key")
openai_model_key = persist_key(f"{__PAGE_NAME__}_model_name")

api_choice = f"{__PAGE_NAME__}_has_chosen_API"
if api_choice not in st.session_state:
    st.session_state[api_choice] = False

model_choice = f"{__PAGE_NAME__}_has_chosen_model"
if model_choice not in st.session_state:
    st.session_state[model_choice] = False

if not (st.session_state[api_choice] and st.session_state[model_choice]):
    # OpenAI API key
    st.subheader("OpenAI API")
    openai_api = st.text_input(
        label="Enter a valid OpenAI API key",
        value="",
        key=openai_api_key,
        disabled=st.session_state[api_choice],
    )

    def _on_click_():
        st.session_state[api_choice] = True

    st.button("Next", on_click=_on_click_)

    if st.session_state[api_choice]:
        openai_client, available_models = get_openai_client(openai_api)
        try:
            if openai_model_key in st.session_state:
                index = available_models.index(st.session_state[openai_model_key])
            else:
                index = available_models.index("gpt-3.5-turbo-0125")
        except ValueError:
            index = 0
        st.selectbox(
            label="Select an OpenAI model",
            options=available_models,
            index=index,
            key=openai_model_key,
        )

        def _on_click_():
            st.session_state[model_choice] = True

        st.button("Start", on_click=_on_click_)


else:
    set_game_style()

    # Init game state and spymaster
    side_length = 5
    if BOARD_WORDS_KEY not in st.session_state:
        st.session_state[BOARD_WORDS_KEY] = get_default_words_list(
            st.session_state.get(BOARD_LANG_KEY, "en")
        )

    words, team_assignment = generate_board(
        words_list=st.session_state[BOARD_WORDS_KEY],
        side_length=side_length,
        random_seed=st.session_state[f"{__PAGE_NAME__}_random_seed"],
    )
    openai_client, available_models = get_openai_client(
        st.session_state[openai_api_key]
    )
    spymaster = init_spymaster(
        openai_client, st.session_state[openai_model_key], words, team_assignment
    )
    if SPYMASTER_PROMPT_KEY in st.session_state:
        spymaster.update_prompt(st.session_state[SPYMASTER_PROMPT_KEY])

    if SPYMASTER_INSTRUCT_KEY in st.session_state:
        spymaster.update_instruct(st.session_state[SPYMASTER_INSTRUCT_KEY])

    if SPYMASTER_BEHAVIOR_KEY in st.session_state:
        spymaster.use_whole_history(st.session_state[SPYMASTER_BEHAVIOR_KEY])

    # Generate board
    columns = st.columns(side_length)
    for i, c in enumerate(columns):
        for j in range(side_length):
            idx = i * side_length + j
            key = persist_key(f"{__PAGE_NAME__}_word_{idx:02d}")

            def __on_click__(button_key: str, word: str, team: int) -> None:
                spymaster.remove(word, team)
                st.session_state[button_key] = True

            # already pressed
            if st.session_state.get(key, False):
                columns[i].markdown(
                    f'<span class="card {TEAM_TO_STYLE[team_assignment[idx]]}"></span>',
                    unsafe_allow_html=True,
                )
                columns[i].button(words[idx], disabled=True)
            # not pressed
            else:
                columns[i].markdown(
                    f'<span class="card"></span>', unsafe_allow_html=True
                )
                columns[i].button(
                    words[idx],
                    on_click=partial(
                        __on_click__,
                        button_key=key,
                        word=words[idx],
                        team=team_assignment[idx],
                    ),
                )

    # generate prompt
    hint, game_end = spymaster.play()

    # Celebrate upon win !
    if game_end == 1:
        st.balloons()

    # Show history of each team
    columns = st.columns((0.3, 0.1, 0.2, 0.1, 0.3))
    for col_idx, team in [(0, 0), (-1, 1)]:
        with columns[col_idx]:
            st.markdown(hint if spymaster.current_team == team else """|""")
            with st.expander("Show History"):
                st.markdown(spymaster.get_history(team))

    for col_idx, team in [(1, 0), (-2, 1)]:
        with columns[col_idx]:
            st.markdown(
                f'<span class="{TEAM_TO_STYLE[team + 1]}"></span>',
                unsafe_allow_html=True,
            )
            st.button(
                f"{len(spymaster.words(team))}", disabled=True, key=f"counter_{team}"
            )

    # Interaction
    with columns[2]:
        if game_end != 0:
            if st.button("Restart"):
                keys = list(st.session_state.keys())
                for key in keys:
                    if not key in [
                        api_choice,
                        model_choice,
                        openai_model_key,
                        openai_api_key,
                    ]:
                        st.session_state.pop(key)
                    else:
                        st.session_state[key] = st.session_state[key]
                st.cache_resource.clear()
                st.cache_data.clear()
                st.session_state[f"{__PAGE_NAME__}_random_seed"] = random.randint(
                    0, 1000
                )
                persist_session_state(__PAGE_NAME__)
                st.rerun()

        else:
            st.markdown(
                f'<span class="beige"></span>',
                unsafe_allow_html=True,
            )
            st.button(
                "Pass your turn",
                on_click=lambda spymaster=spymaster: spymaster.end_turn(),
                disabled=game_end,
            )

# Alwyays carry session state across pages
# We need to carry the value of the widgets that were not visible
# In this case, this means the widgets from other pages + the OpenAI API
# settings as they are only displayed once
persist_session_state(__PAGE_NAME__)
if st.session_state[api_choice] and st.session_state[model_choice]:
    st.session_state[openai_api_key] = st.session_state[openai_api_key]
    st.session_state[openai_model_key] = st.session_state[openai_model_key]
