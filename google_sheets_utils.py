
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open(sheet_name)

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    date_str = date_override.strftime('%Y-%m-%d') if date_override else datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([date_str, timestamp, class_name, student_id, student_name, status, entered_by])

def get_latest_attendance(sheet, class_name, date_str):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df = df[(df["class"] == class_name) & (df["date"] == date_str)]
    latest_attendance = {}
    for _, row in df.iterrows():
        sid = row["student_id"]
        time = row["timestamp"]
        if sid not in latest_attendance or row["timestamp"] > latest_attendance[sid][1]:
            latest_attendance[sid] = (row["status"], row["timestamp"])
    return {sid: val[0] for sid, val in latest_attendance.items()}
