import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe, get_latest_attendance, overwrite_attendance
from datetime import datetime
import pandas as pd

st.title("🏫 Homeroom 出欠入力（朝・夕対応）")

book = connect_to_sheet(st.session_state.sheet_name if "sheet_name" in st.session_state else "attendance-shared")
sheet = book.worksheet("attendance_log")
today = st.date_input("出欠日付", value=datetime.today(), format="YYYY-MM-DD")

teachers_df = load_master_dataframe(book, "teachers_master")
students_df = load_master_dataframe(book, "students_master")

teachers_df = teachers_df.sort_values("teacher_code")
teacher_display = teachers_df["teacher_code"] + "：" + teachers_df["teacher"]
selected_display = st.selectbox("担任教師を選択", teacher_display.tolist())
teacher_code = selected_display.split("：")[0]
teacher_row = teachers_df[teachers_df["teacher_code"] == teacher_code]
teacher_name = teacher_row["teacher"].values[0]

suggested_class = teacher_row["homeroom_class"].values[0] if not teacher_row.empty else ""
available_classes = sorted(students_df["class"].dropna().unique())
homeroom_class = st.selectbox("対象クラスを選択（編集可能）", available_classes, index=available_classes.index(suggested_class) if suggested_class in available_classes else 0)

mode = st.radio("ホームルームの種別を選択", ["朝", "夕方"])
mode_label = "homeroom-morning" if mode == "朝" else "homeroom-evening"

students_in_class = students_df[students_df["class"] == homeroom_class].sort_values("student_id")
statuses = ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

st.header(f"{homeroom_class} の生徒出欠入力（{mode}）")
attendance_inputs = {}

latest_df = get_latest_attendance(sheet, homeroom_class, today.strftime("%Y-%m-%d")) if mode == "夕方" else {}

non_default_students = []

for _, row in students_in_class.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    default_status = latest_df.get(sid, "○")
    status = st.selectbox(f"{sid} - {name}", statuses, index=statuses.index(default_status), key=sid)
    attendance_inputs[sid] = (name, status)
    if status != "○":
        non_default_students.append((sid, name, status))

if non_default_students:
    st.subheader("⚠️ ⚪︎以外の生徒がいます。間違いないですか？")
    for sid, name, status in non_default_students:
        st.write(f"・{sid} - {name}：{status}")

if st.button("📥 出欠を一括登録"):
    for sid, (name, status) in attendance_inputs.items():
        write_attendance(sheet, homeroom_class, sid, name, status, mode_label, date_override=today)
    st.success(f"{homeroom_class} の{mode}の出欠を登録しました。")

    st.subheader("📝 状況確認が必要な生徒")
    for sid, name, status in non_default_students:
        if not st.checkbox(f"{sid} - {name}：{status}（確認完了）", key=f"check_{sid}"):
            st.write(f"🕵️‍♂️ {sid} - {name}：{status}")
