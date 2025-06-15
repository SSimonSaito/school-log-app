import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def connect_to_sheet(sheet_id, tab_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(sheet_id)
    return sheet.worksheet(tab_name)

def write_attendance(sheet, *args):
    # 書き込みロジック（省略）
    pass
