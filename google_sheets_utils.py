import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def connect_to_sheet_by_url(sheet_url: str):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_url(sheet_url)

def get_existing_attendance(book):
    sheet = book.worksheet("attendance_log")
    df = pd.DataFrame(sheet.get_all_records())
    return df