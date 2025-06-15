import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

def connect_to_sheet(sheet_url):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_url(sheet_url)

def write_attendance(sheet, class_, student_id, student_name, status, mode_label, date_override=None):
    jst = datetime.utcnow() + timedelta(hours=9)
    date_str = date_override or jst.strftime("%Y-%m-%d")
    timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")
    row = [date_str, timestamp, class_, student_id, student_name, status, mode_label]
    records = sheet.get_all_records()
    found = None
    for i, r in enumerate(records):
        if r["date"] == date_str and r["class"] == class_ and r["student_id"] == student_id and r["entered_by"] == mode_label:
            found = i + 2
            break
    if found:
        sheet.delete_row(found)
    sheet.append_row(row)

def get_existing_attendance(book):
    sheet = book.worksheet("attendance_log")
    df = pd.DataFrame(sheet.get_all_records())
    return df