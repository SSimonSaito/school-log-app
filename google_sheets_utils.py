import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

def connect_to_sheet():
    scopes = st.secrets["gcp"]["scopes"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["gcp"]["spreadsheet_id"])

def get_existing_attendance(sheet):
    df = pd.DataFrame(sheet.get_all_records())
    if "date" not in df.columns:
        df["date"] = ""
    if "period" not in df.columns:
        df["period"] = ""
    return df

def write_attendance_data(sheet, data_list):
    sheet.clear()
    headers = ["timestamp", "date", "class", "student_id", "student_name", "status", "entered_by", "period"]
    sheet.append_row(headers)
    for data in data_list:
        row = [data.get(h, "") for h in headers]
        sheet.append_row(row)

def write_status_log(book, class_name, student_name, status, teacher, comment):
    sheet = book.worksheet("student_statuslog")
    timestamp = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, class_name, student_name, status, teacher, comment]
    sheet.append_row(row)
