import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
import pytz
from datetime import datetime

def connect_to_sheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA")
    return sheet.worksheet(sheet_name)

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, records):
    jst = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    for record in records:
        record[1] = jst  # timestamp
    sheet.clear()
    sheet.append_row(["date", "timestamp", "class", "student_id", "student_name", "status", "entered_by"])
    sheet.append_rows(records)
