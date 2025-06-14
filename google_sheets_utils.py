import gspread
import json
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def connect_to_sheet(sheet_name):
    creds_dict = st.secrets["gcp"]
    creds_json = json.loads(json.dumps(creds_dict))
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([date_str, class_name, student_id, student_name, status, entered_by])
