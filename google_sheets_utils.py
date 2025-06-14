import gspread
import streamlit as st
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def connect_to_sheet(sheet_name):
    creds_dict = dict(st.secrets["gcp"])
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)

def load_master_dataframe(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by, date_override=None):
    date_str = date_override.strftime('%Y-%m-%d') if date_override else datetime.now().strftime('%Y-%m-%d')
    sheet.append_row([date_str, class_name, student_id, student_name, status, entered_by])
