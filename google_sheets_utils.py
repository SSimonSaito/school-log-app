import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open(sheet_name)

def get_existing_attendance(book):
    try:
        sheet = book.worksheet("attendance_log")
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except Exception:
        return pd.DataFrame()

def get_teacher_name_by_id(book, teacher_id):
    sheet = book.worksheet("teachers_master")
    data = sheet.get_all_records()
    for row in data:
        if row.get("teacher_id") == teacher_id:
            return row.get("teacher")
    return None