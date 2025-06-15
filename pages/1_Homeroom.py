import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import connect_to_gsheet
import pytz

st.title("Homeroom 出欠入力")

if "teacher_name" not in st.session_state:
    st.warning("main画面から教師情報を入力してください。")
    st.stop()

teacher_name = st.session_state.teacher_name
class_name = st.session_state.class_name
selected_date = st.session_state.selected_date

st.markdown(f"### 👤 教師: {teacher_name}")
st.markdown(f"### 🏫 クラス: {class_name}")
st.markdown(f"### 📅 日付: {selected_date}")

sheet = connect_to_gsheet("students_master")
df_students = pd.DataFrame(sheet.get_all_records())
students = df_students[df_students["class"] == class_name]

status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
entries = []

for _, row in students.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    status = st.radio(f"{student_name}", status_options, horizontal=True, key=student_id)
    entries.append({
        "date": selected_date,
        "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
        "class": class_name,
        "student_id": student_id,
        "student_name": student_name,
        "status": status,
        "entered_by": teacher_name,
    })

if st.button("保存"):
    sheet_log = connect_to_gsheet("attendance_log")
    existing = pd.DataFrame(sheet_log.get_all_records())
    new_data = pd.DataFrame(entries)
    filtered = existing[
        (existing["date"] == selected_date) & 
        (existing["class"] == class_name)
    ]
    if not filtered.empty:
        st.warning("⚠️ すでに入力済みのデータがあります。上書き保存します。")
        sheet_log.clear()
        sheet_log.append_rows([list(new_data.columns)] + new_data.values.tolist())
    else:
        sheet_log.append_rows(new_data.values.tolist())
    st.success("✅ 保存しました")
