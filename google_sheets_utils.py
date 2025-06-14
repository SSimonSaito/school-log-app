import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def connect_to_sheet(json_key_path, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def write_attendance(sheet, class_name, student_id, student_name, status, entered_by):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([date_str, class_name, student_id, student_name, status, entered_by])
