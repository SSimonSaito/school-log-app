import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_attendance_data,
    get_existing_attendance,
)
import pytz

st.set_page_config(page_title="📘 TeachingLog（教務手帳）", layout="centered")
st.title("📘 TeachingLog（教務手帳）")

# セッションチェック
if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌ mainページから教師と日付を選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]
weekday = selected_date.strftime("%a")

weekday_jp = {"Mon": "月", "Tue": "火", "Wed": "水", "Thu": "木", "Fri": "金", "Sat": "土", "Sun": "日"}
weekday_str = weekday_jp.get(weekday, weekday)

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date}（{weekday_str}）")

book = connect_to_sheet("attendance-shared")
tt_df = get_worksheet_df(book, "timetable_master")
students_df = get_worksheet_df(book, "students_master")
attendance_df = get_existing_attendance(book, "attendance_log")

tt_today = tt_df[(tt_df["teacher"] == teacher_name) & (tt_df["weekday"] == weekday_str)]

if tt_today.empty:
    st.info("本日の授業はありません。")
    st.stop()

selected_period = st.radio("授業時限を選択してください", tt_today["period"].tolist())
selected_class = tt_today[tt_today["period"] == selected_period]["class"].values[0]

st.markdown(f"### 🏫 {selected_class} の出欠入力（{selected_period}）")

students_in_class = students_df[students_df["class"] == selected_class].copy()

period_order = ["MHR", "1限", "2限", "3限", "4限", "5限", "6限", "EHR"]
def get_previous_period(period):
    idx = period_order.index(period)
    return period_order[idx - 1] if idx > 0 else "MHR"

default_period = get_previous_period(selected_period)

existing_df = attendance_df.copy()
existing_today = existing_df[
    (existing_df["class"] == selected_class)
    & (existing_df["date"] == selected_date.strftime("%Y-%m-%d"))
    & (existing_df["period"] == selected_period)
]

previous_data = attendance_df[
    (attendance_df["class"] == selected_class)
    & (attendance_df["date"] == selected_date.strftime("%Y-%m-%d"))
    & (attendance_df["period"] == default_period)
]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
attendance_data = []

if not existing_today.empty:
    if not st.checkbox("⚠️ この時限は既に入力されています。上書きしますか？"):
        st.stop()

for _, row in students_in_class.iterrows():
    sid = row["student_id"]
    sname = row["student_name"]
    default_status = previous_data[previous_data["student_id"] == sid]["status"].values
    default = default_status[0] if len(default_status) > 0 else "○"
    status = st.radio(f"{sname}（{sid}）", status_options, horizontal=True, index=status_options.index(default))
    attendance_data.append([
        selected_date.strftime("%Y-%m-%d"),
        datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        selected_class,
        sid,
        sname,
        status,
        teacher_name,
        selected_period
    ])

if st.button("📥 出欠を登録"):
    if not existing_today.empty:
        attendance_df = attendance_df[~(
            (attendance_df["class"] == selected_class) &
            (attendance_df["date"] == selected_date.strftime("%Y-%m-%d")) &
            (attendance_df["period"] == selected_period)
        )]
        worksheet = book.worksheet("attendance_log")
        worksheet.clear()
        worksheet.append_row(list(attendance_df.columns))
        worksheet.append_rows(attendance_df.values.tolist())

    write_attendance_data(book, "attendance_log", attendance_data)
    st.success("✅ 教務出欠情報を登録しました。")
