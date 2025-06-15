import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def connect_to_sheet():
    scopes = st.secrets["gcp"]["scopes"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["gcp"]["spreadsheet_id"])
