import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import streamlit as st

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    credentials.refresh(Request())
    client = gspread.authorize(credentials)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA").worksheet(sheet_name)

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    jst = datetime.utcnow() + timedelta(hours=9)
    date_str = (date_override or jst.date()).isoformat()
    timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")
    values = [date_str, timestamp, class_name, student_id, student_name, status, entered_by]
    sheet.append_row(values)

def load_master_dataframe(sheet):
    df = pd.DataFrame(sheet.get_all_records())
    df.columns = df.columns.map(lambda x: str(x).strip().lower())
    return df
