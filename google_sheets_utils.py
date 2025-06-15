
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def connect_to_sheet(sheet_url, sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_url(sheet_url).worksheet(sheet_name)
