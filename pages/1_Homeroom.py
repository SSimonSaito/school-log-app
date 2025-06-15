import streamlit as st
from google_sheets_utils import connect_to_sheet, get_existing_attendance
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Homeroom 出欠入力", layout="wide")

sheet_url = st.secrets["sheet_url"]
attendance_sheet = connect_to_sheet(sheet_url, "attendance_log")
students_sheet = connect_to_sheet(sheet_url, "students_master")

teacher_name = st.session_state.get("teacher_name", "")
teacher_id = st.session_state.get("teacher_id", "")

jst_today = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d")
date = st.date_input("🗓️ 日付を選択", value=datetime.strptime(jst_today, "%Y-%m-%d"))

df_students = pd.DataFrame(students_sheet.get_all_records())
df_students.columns = df_students.columns.str.strip()
df_class = df_students[df_students["homeroom_teacher_id"] == teacher_id]

if df_class.empty:
    st.warning("担任クラスが見つかりませんでした。")
    st.stop()

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
existing_df = get_existing_attendance(attendance_sheet)
existing = existing_df[
    (existing_df["date"] == date.strftime("%Y-%m-%d")) &
    (existing_df["entered_by"] == teacher_name)
]

overwrite = True
if not existing.empty:
    overwrite = st.radio("⚠️ 既に出欠データがあります。上書きしますか？", ["はい", "いいえ"]) == "はい"

if overwrite:
    records = []
    for _, row in df_class.iterrows():
        st.markdown(f"**{row['student_name']}**")
        status = st.radio(
            f"出欠 ({row['student_id']})",
            status_options,
            key=row['student_id'],
            horizontal=True
        )
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
            "class": row["class"],
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "status": status,
            "entered_by": teacher_name
        })

    if st.button("💾 登録"):
        existing_df = existing_df[~(
            (existing_df["date"] == date.strftime("%Y-%m-%d")) &
            (existing_df["entered_by"] == teacher_name)
        )]
        df_new = pd.DataFrame(records)
        df_final = pd.concat([existing_df, df_new], ignore_index=True)
        attendance_sheet.clear()
        attendance_sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
        st.success("✅ 出欠データを登録しました。")
