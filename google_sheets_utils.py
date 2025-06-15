import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open("attendance-shared")
