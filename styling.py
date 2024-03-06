import streamlit as st

TEAM_TO_STYLE = {-1: "black", 0: "beige", 1: "red", 2: "blue"}


def set_game_style():
    st.markdown(
        """
        <style>
            .element-container:has(.card) + div button {
                height: 60px;
                width: 130px;
                margin: 3px
            }

            .element-container:has(.blue) + div button {
                &,
                &:hover {
                    background-color: DodgerBlue
                }
            }

            .element-container:has(.red) + div button {
                &,
                &:hover {
                    background-color: FireBrick
                }
            }

            .element-container:has(.beige) + div button {
                &,
                &:hover {
                    background-color: BlanchedAlmond;
                    color: Brown
                }
            }

            .element-container:has(.black) + div button {
                &,
                &:hover {
                    background-color: Black
                }
            }

            .stButton button:hover {
                border: 2px solid white;
                text-color: white;
                color: white;
            }

            .stButton button:focus, .stButton button:active {
                border: 2px solid white
                text-color: white;
                color: white;
                background-color: white
            }

            div[data-testid="column"] p {
                text-align: center;
            }

            div[data-testid="column"] button {
                text-align: center;
                width:100%
            }
        </style>""",
        unsafe_allow_html=True,
    )
