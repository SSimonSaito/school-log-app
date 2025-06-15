import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timedelta

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    sheet_url = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA"
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.worksheet(sheet_name)

def write_attendance_log(sheet, date_str, class_name, statuses, entered_by, mode_label):
    sheet.clear()  # 上書き
    rows = [["date", "timestamp", "class", "student_id", "student_name", "status", "entered_by"]]
    jst = datetime.utcnow() + timedelta(hours=9)
    timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")

    for sid, (name, status) in statuses.items():
        row = [date_str, timestamp, class_name, sid, name, status, mode_label]
        rows.append(row)

    sheet.append_rows(rows)