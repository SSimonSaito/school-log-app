
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from google.auth.transport.requests import Request
from datetime import datetime, timezone, timedelta

def connect_to_sheet(sheet_name):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    credentials.refresh(Request())  # 明示的にリフレッシュ
    client = gspread.authorize(credentials)
    return client.open(sheet_name)

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    jst_now = datetime.now(timezone(timedelta(hours=9)))
    date_str = date_override.strftime("%Y-%m-%d") if date_override else jst_now.strftime("%Y-%m-%d")
    timestamp = jst_now.strftime("%Y-%m-%d %H:%M:%S")
    values = [date_str, timestamp, class_name, student_id, student_name, status, entered_by]
    sheet.append_row(values)
