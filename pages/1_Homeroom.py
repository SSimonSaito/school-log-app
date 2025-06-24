import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import pytz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    get_existing_attendance,
    write_attendance_data,
    write_status_log,
)

st.set_page_config(page_title="Homeroom 出欠入力", layout="centered")
st.title("🏢 Homeroom 出欠入力")

# セッションチェック
if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date.strftime('%Y-%m-%d（%a）')}")

period = "MHR"
st.markdown("📌 本アプリでは朝のホームルーム（MHR）の出欠＋メモのみを記録します。")

book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
teachers_df = get_worksheet_df(book, "teachers_master")
attendance_df = get_existing_attendance(book)

# 担任クラス取得
default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values
if len(default_class) == 0:
    st.error("⚠️ 担任クラスが見つかりません。teachers_masterを確認してください。")
    st.stop()
homeroom_class = default_class[0]

# 生徒取得
students_in_class = students_df[students_df["class"] == homeroom_class].copy()
if students_in_class.empty:
    st.warning("⚠️ クラスに所属する生徒が見つかりません。")
    st.stop()

# 出欠取得
today_str = selected_date.strftime("%Y-%m-%d")
existing_today = attendance_df[
    (attendance_df["class"] == homeroom_class) &
    (attendance_df["period"] == period) &
    (attendance_df["date"] == today_str)
]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
st.markdown(f"### 🏫 {homeroom_class} の出欠＋メモ入力（{period}）")

attendance_data = []
for _, row in students_in_class.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    
    existing_row = existing_today[existing_today["student_id"] == student_id]
    default_status = existing_row["status"].values[0] if not existing_row.empty else "○"
    default_memo = existing_row["memo"].values[0] if not existing_row.empty and "memo" in existing_row.columns else ""

    if not existing_row.empty:
        st.warning(f"⚠️ {student_name} はすでに入力済みです（上書きされます）")

    col1, col2 = st.columns([2, 3])
    with col1:
        status = st.radio(f"{student_name}（{student_id}）", status_options, horizontal=True, index=status_options.index(default_status), key=f"status_{student_id}")
    with col2:
        memo = st.text_input("メモ（任意）", value=default_memo, key=f"memo_{student_id}")

    attendance_data.append({
        "student_id": student_id,
        "student_name": student_name,
        "status": status,
        "memo": memo
    })

if st.button("📝 出欠＋メモを登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    enriched_data = []
    for row in attendance_data:
        enriched_data.append([
            today_str,
            now,
            homeroom_class,
            row["student_id"],
            row["student_name"],
            row["status"],
            teacher_name,
            period,
            row["memo"]
        ])

    try:
        attendance_df = attendance_df[
            ~(
                (attendance_df["class"] == homeroom_class) &
                (attendance_df["period"] == period) &
                (attendance_df["date"] == today_str)
            )
        ]

        sheet = book.worksheet("attendance_log")
        sheet.clear()
        sheet.append_row(attendance_df.columns.tolist())
        sheet.append_rows(attendance_df.values.tolist())

        write_attendance_data(book, "attendance_log", enriched_data)
        st.success("✅ 出欠＋メモを登録しました。")

    except Exception as e:
        st.error(f"❌ 出欠データ保存中にエラーが発生しました: {e}")
