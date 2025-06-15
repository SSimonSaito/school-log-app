import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe
from datetime import datetime
import pandas as pd

if "sheet_name" not in st.session_state:
    st.session_state["sheet_name"] = "attendance-shared"

st.title("📒 Teaching Log - 授業出欠と定期テスト入力")

book = connect_to_sheet(st.session_state.sheet_name)
sheet = book.worksheet("attendance_log")
today = st.date_input("日付を選択", value=datetime.today(), format="YYYY-MM-DD")

students_df = load_master_dataframe(book, "students_master")
timetable_df = load_master_dataframe(book, "timetable_master")

class_options = sorted(students_df["class"].unique())
selected_class = st.selectbox("クラス", class_options)

student_options = students_df[students_df["class"] == selected_class]["student_name"]
selected_student = st.selectbox("生徒名", sorted(student_options))

student_row = students_df[(students_df["class"] == selected_class) & (students_df["student_name"] == selected_student)]
student_id = student_row["student_id"].values[0] if not student_row.empty else ""

weekday = today.strftime("%A")
period = st.selectbox("時限", ["1限", "2限", "3限", "4限", "5限", "6限"])

subject_row = timetable_df[
    (timetable_df["class"] == selected_class) &
    (timetable_df["period"] == period) &
    (timetable_df["weekday"].str.lower() == weekday.lower())
]

subject = subject_row["subject"].values[0] if not subject_row.empty else ""
teacher = subject_row["teacher"].values[0] if "teacher" in subject_row.columns and not subject_row.empty else ""

st.markdown(f"📘 **科目：** {subject}　👩‍🏫 **教師：** {teacher}")

status = st.selectbox("出欠", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"])

if st.button("出欠を記録"):
    write_attendance(sheet, selected_class, student_id, selected_student, status, f"teaching-log:{period}", date_override=today)
    st.success(f"{selected_student} の {period} の出欠を登録しました。")
