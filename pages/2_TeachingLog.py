import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
import pytz
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    get_existing_attendance,
    write_attendance_data,
)

st.set_page_config(page_title="TeachingLog（教務手帳）", layout="centered")
st.title("📘 TeachingLog（教務手帳）")

# セッションチェック
if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]

# 英語→日本語に変換して weekday を正しく取得
weekday_map = {
    "Mon": "月", "Tue": "火", "Wed": "水",
    "Thu": "木", "Fri": "金", "Sat": "土", "Sun": "日"
}
weekday = weekday_map[selected_date.strftime("%a")]

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date.strftime('%Y-%m-%d（%a）')}")

book = connect_to_sheet("attendance-shared")
timetable_df = get_worksheet_df(book, "timetable_master")

# 当該教師の担当授業（当日のみ）
today_classes = timetable_df[
    (timetable_df["teacher"] == teacher_name) &
    (timetable_df["weekday"] == weekday)
].copy()

if today_classes.empty:
    st.info("本日の授業担当はありません。")
    st.stop()

# 時限順にソートし、時限と科目を表示
today_classes["period_num"] = today_classes["period"].str.extract(r'(\d)').astype(int)
today_classes = today_classes.sort_values("period_num")
period_labels = [
    f'{row["period"]}：{row["subject"]}' for _, row in today_classes.iterrows()
]
period_map = {
    f'{row["period"]}：{row["subject"]}': (row["class"], row["period"])
    for _, row in today_classes.iterrows()
}
selected_period_label = st.radio("授業時限を選択してください", period_labels)
selected_class, selected_period = period_map[selected_period_label]

# 生徒リスト取得
students_df = get_worksheet_df(book, "students_master")
students_in_class = students_df[students_df["class"] == selected_class].copy()

# 出欠ログ取得
attendance_df = get_existing_attendance(book)
today_str = selected_date.strftime("%Y-%m-%d")
existing_today = attendance_df[
    (attendance_df["class"] == selected_class)
    & (attendance_df["period"] == selected_period)
    & (attendance_df["date"] == today_str)
]

# デフォルト出欠状況を設定（MHR または前時限）
reference_period = "MHR"
prev = today_classes["period_num"].tolist()
cur_idx = today_classes[today_classes["period"] == selected_period]["period_num"].values[0]
if cur_idx != min(prev):
    reference_period = today_classes[today_classes["period_num"] == cur_idx - 1]["period"].values[0]

reference_df = attendance_df[
    (attendance_df["class"] == selected_class)
    & (attendance_df["period"] == reference_period)
    & (attendance_df["date"] == today_str)
]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

st.markdown(f"🏫 **{selected_class} の出欠入力（{selected_period}）**")

if not reference_df.empty:
    st.caption(f"※ デフォルト出欠状況は {reference_period} を参照")

attendance_data = []
for _, row in students_in_class.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    ref_row = reference_df[reference_df["student_id"] == student_id]
    default_status = ref_row["status"].values[0] if not ref_row.empty else "○"

    existing_row = existing_today[existing_today["student_id"] == student_id]
    if not existing_row.empty:
        st.warning("⚠️ すでに入力済みです。上書きしますか？")
        default_status = existing_row["status"].values[0]

    status = st.radio(f"{student_name}（{student_id}）", status_options, horizontal=True, index=status_options.index(default_status))
    attendance_data.append({
        "student_id": student_id,
        "student_name": student_name,
        "status": status
    })

if st.button("📝 出欠を登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    enriched_data = []

    for row in attendance_data:
        enriched_data.append([
            today_str,
            now,
            selected_class,
            row["student_id"],
            row["student_name"],
            row["status"],
            teacher_name,
            selected_period
        ])

    # 重複削除
    if not existing_today.empty:
        attendance_df = attendance_df[
            ~(
                (attendance_df["class"] == selected_class) &
                (attendance_df["period"] == selected_period) &
                (attendance_df["date"] == today_str)
            )
        ]
        sheet = book.worksheet("attendance_log")
        sheet.clear()
        sheet.append_row(attendance_df.columns.tolist())
        sheet.append_rows(attendance_df.values.tolist())

    write_attendance_data(book, "attendance_log", enriched_data)
    st.success("✅ 出欠情報を登録しました。")
