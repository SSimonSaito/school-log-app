import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "attendance_log"

def connect_to_sheet(sheet_name=SHEET_NAME):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("attendance-shared")

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    jst = datetime.utcnow() + timedelta(hours=9)
    date_str = (date_override or jst).strftime("%Y-%m-%d")
    timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")
    row = [date_str, timestamp, class_name, student_id, student_name, status, entered_by]
    sheet.append_row(row)

def overwrite_attendance(sheet, date, class_name, entered_by):
    df = pd.DataFrame(sheet.get_all_records())
    if df.empty:
        return
    df.columns = df.columns.astype(str).str.strip().str.lower()
    mask = (
        (df["date"].astype(str).str.strip() == date.strftime("%Y-%m-%d")) &
        (df["class"].astype(str).str.strip() == class_name) &
        (df["entered_by"].astype(str).str.strip() == entered_by)
    )
    if mask.any():
        rows_to_delete = df[mask].index.tolist()
        for i in reversed(rows_to_delete):
            sheet.delete_rows(i + 2)
