
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from google_sheets_utils import connect_to_sheet

st.set_page_config(page_title="Homeroom 出欠入力", page_icon="🏫")

sheet_url = "https://docs.google.com/spreadsheets/d/1xPEGfNw0e9GemdJu2QIw0Bt2wVp6gbWRm56FuBWnzrA/edit#gid=0"
students_sheet_name = "students_master"
log_sheet_name = "attendance_log"

# JST対応
jst = timezone(timedelta(hours=9))
now = datetime.now(jst)

teacher_name = st.session_state.get("teacher_name", "")
selected_date = st.session_state.get("selected_date", now.date())

st.title("🏫 Homeroom 出欠入力")
st.write(f"🧑‍🏫 教師: {teacher_name}")
st.write(f"📅 日付: {selected_date}")

# 生徒取得
sheet_students = connect_to_sheet(sheet_url, students_sheet_name)
students_df = pd.DataFrame(sheet_students.get_all_records())
students_df.columns = students_df.columns.str.strip()

class_list = students_df["class"].dropna().unique().tolist()
target_class = st.selectbox("クラスを選択してください", class_list)

filtered_students = students_df[students_df["class"] == target_class]
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

statuses = {}
for _, row in filtered_students.iterrows():
    sid = row["student_id"]
    sname = row["student_name"]
    default = "○"
    statuses[sid] = st.selectbox(f"{sid} - {sname}", status_options, index=status_options.index(default))

# 既存ログ取得と上書き確認
sheet_log = connect_to_sheet(sheet_url, log_sheet_name)
log_df = pd.DataFrame(sheet_log.get_all_records())
log_df.columns = log_df.columns.str.strip()

existing = log_df[
    (log_df["date"] == str(selected_date)) &
    (log_df["class"] == target_class) &
    (log_df["entered_by"] == "homeroom-morning")
]

if not existing.empty:
    if not st.checkbox("⚠️ 既存の出欠記録があります。上書きする場合はチェックしてください"):
        st.stop()

# 一括登録
if st.button("📬 出欠を一括登録"):
    sheet_log.clear()  # 仮に上書き許可された場合はリセット
    for _, row in filtered_students.iterrows():
        sid = row["student_id"]
        sname = row["student_name"]
        status = statuses[sid]
        sheet_log.append_row([
            str(selected_date),
            now.strftime("%Y-%m-%d %H:%M:%S"),
            target_class,
            sid,
            sname,
            status,
            "homeroom-morning"
        ])
    st.success("✅ 出欠登録が完了しました")
