import streamlit as st
import pandas as pd
import hmac
from datetime import datetime

def check_password():

    def login_form():
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Login", on_click=password_entered)
    
    def password_entered():
        if st.session_state["username"] in st.secrets["password"] and hmac.compare_digest(st.session_state["password"], st.secrets["password"][st.session_state["username"]]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
    
    if st.session_state.get("password_correct", False):
        return True
    
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 Incorrect username or password.")
    return False

if not check_password():
    st.stop()
            
st.set_page_config(
    page_title="Predict CRRT for Kids",
    page_icon=":hospital:",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': "mailto:zulfanzidni@gmail.com",
        'About': None
    }
)

#AppVersion: 3.0

# Page Setup
home_page = st.Page(
    page="views/home.py",
    title="Home",
    icon="🏠",
    default=True
)

view_data_page = st.Page(
    page="views/view_data.py",
    title="View Data",
    icon="📊",
)

pg = st.navigation(
    pages=[home_page, view_data_page])

with st.sidebar:
    # build the sidebar content
    st.write("Credits")
    st.write("Developed by: **Zulfan Zidni Ilhama** [LinkedIn](https://www.linkedin.com/in/zulfanzidni/)")
    st.write("Supervised by: **Retno Aulia Vinarti, M.Kom., Ph.D.** [Email](ra_vinarti@its.ac.id)")
    st.write("Expert: **dr. Reza Fahlevi, Sp.A (RSCM UI)**")
    # st.download_button("Download Data", data=df.to_csv(), file_name="data.csv", mime="text/csv", use_container_width=True, icon=":material/download:")

pg.run()