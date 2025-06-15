
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone

scopes = ["https://www.googleapis.com/auth/spreadsheets"]

def connect_to_sheet(sheet_name):
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA")

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def load_attendance_log(book):
    worksheet = book.worksheet("attendance_log")
    return pd.DataFrame(worksheet.get_all_records())

def write_attendance(sheet, date_str, timestamp, class_name, student_id, student_name, status, entered_by):
    sheet.append_row([date_str, timestamp, class_name, student_id, student_name, status, entered_by])
