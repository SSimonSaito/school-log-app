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
today_str = selected_date.strftime("%Y-%m-%d")
period = "MHR"

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {today_str}")
st.markdown("📌 本アプリでは朝のホームルーム（MHR）の出欠のみを記録します。")

book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
teachers_df = get_worksheet_df(book, "teachers_master")
attendance_df = get_existing_attendance(book, "attendance_log")

# クラスの特定
default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values
if len(default_class) == 0:
    st.error("❌ 該当する担任クラスが見つかりません。")
    st.stop()
homeroom_class = default_class[0]
students_in_class = students_df[students_df["class"] == homeroom_class].copy()

# 出欠ログ取得
today_records = attendance_df[
    (attendance_df["class"] == homeroom_class) &
    (attendance_df["period"] == period) &
    (attendance_df["date"] == today_str)
]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

st.markdown(f"## 🏫 {homeroom_class} 出欠入力（MHR）")

attendance_data = []
for _, row in students_in_class.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    existing_row = today_records[today_records["student_id"] == student_id]
    default_status = existing_row["status"].values[0] if not existing_row.empty else "○"

    status = st.radio(f"{student_name}（{student_id}）", status_options, horizontal=True, index=status_options.index(default_status), key=f"status_{student_id}")

    attendance_data.append({
        "student_id": student_id,
        "student_name": student_name,
        "status": status
    })

if st.button("📅 出欠を登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    enriched_rows = [
        [today_str, now, homeroom_class, row["student_id"], row["student_name"], row["status"], teacher_name, period, ""]
        for row in attendance_data
    ]

    # 既存データを除外
    updated_df = attendance_df[
        ~(
            (attendance_df["class"] == homeroom_class) &
            (attendance_df["period"] == period) &
            (attendance_df["date"] == today_str)
        )
    ]

    try:
        sheet = book.worksheet("attendance_log")
        sheet.clear()
        sheet.append_row(updated_df.columns.tolist())
        sheet.append_rows(updated_df.fillna("").values.tolist())

        write_attendance_data(book, "attendance_log", enriched_rows)
        st.success("✅ 出欠を登録しました。")
    except Exception as e:
        st.error(f"❌ 出欠データ保存中にエラーが発生しました: {e}")
