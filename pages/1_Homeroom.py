import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime
from modules.google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_attendance_data,
    write_status_log,
    get_existing_attendance,
)
import pytz

st.set_page_config(page_title="Homeroom 出欠入力", layout="centered")
st.title("🏫 Homeroom 出欠入力")

if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date}")

period = st.radio("HR区分を選択してください", ["MHR", "EHR"])

book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
class_list = sorted(students_df["class"].dropna().unique())

teachers_df = get_worksheet_df(book, "teachers_master")
default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values
default_class = default_class[0] if len(default_class) > 0 else ""

homeroom_class = st.selectbox("🏫 クラスを選択してください", class_list, index=class_list.index(default_class) if default_class in class_list else 0)
students_in_class = students_df[students_df["class"] == homeroom_class].copy()

existing_df = get_existing_attendance(book, "attendance_log")
today_str = str(selected_date)
existing_today = existing_df[
    (existing_df["class"] == homeroom_class)
    & (existing_df["period"] == period)
    & (existing_df["timestamp"].str.startswith(today_str))
]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
st.markdown("## ✏️ 出欠入力")
attendance_data = []
alerts = []

for _, row in students_in_class.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    existing_row = existing_today[existing_today["student_id"] == student_id]
    default_status = existing_row["status"].values[0] if not existing_row.empty else "○"
    status = st.radio(f"{student_name}（{student_id}）", status_options, horizontal=True, index=status_options.index(default_status))
    attendance_data.append({
        "student_id": student_id,
        "student_name": student_name,
        "status": status
    })
    if status != "○":
        alerts.append((student_id, student_name, status))

if not existing_today.empty:
    if not st.checkbox("⚠️ 既存データがあります。上書きしますか？"):
        st.stop()

if st.button("📥 出欠を一括登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today_str = selected_date.strftime("%Y-%m-%d")
    enriched_data = []

    for row in attendance_data:
        enriched_data.append([
            today_str,            # date列
            now,                  # timestamp列
            homeroom_class,
            row["student_id"],
            row["student_name"],
            row["status"],
            teacher_name,
            period
        ])

    write_attendance_data(book, "attendance_log", enriched_data)
    st.success("✅ 出欠情報を登録しました。")

# 状況確認：生徒ごとに対応チェック後にログ書き込み＋非表示処理
if alerts:
    st.markdown("### ⚠️ 確認が必要な生徒")
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today_str = selected_date.strftime("%Y-%m-%d")

    for sid, sname, stat in alerts:
        col1, col2 = st.columns([3, 2])
        with col1:
            comment = st.text_input(f"{sname}（{stat}）への対応コメント", key=f"{sid}_comment")
        with col2:
            if st.button("✔️ 対応済み", key=f"{sid}_resolved"):
                log_row = [[
                    today_str,
                    now,
                    homeroom_class,
                    sid,
                    sname,
                    stat,
                    teacher_name,
                    period,
                    comment
                ]]
                write_status_log(book, "student_statuslog", log_row)
                st.success(f"✅ {sname} の対応を記録しました")
                st.experimental_rerun()
