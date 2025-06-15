import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import connect_to_sheet, write_attendance_log

st.set_page_config(page_title="Homeroom 出欠入力", layout="wide")
st.title("🏫 Homeroom 出欠入力")

sheet_name = "attendance_log"
sheet = connect_to_sheet(sheet_name)

# 今日の日付（JST）
today = datetime.utcnow() + timedelta(hours=9)
today_str = today.strftime("%Y-%m-%d")

# 教師マスタ取得
teacher_df = connect_to_sheet("teachers_master")
teacher_list = teacher_df["teacher"].dropna().unique().tolist()
selected_teacher = st.selectbox("👩‍🏫 担任の先生を選択", teacher_list)

# 担任クラス候補（編集可能）
homeroom_default = teacher_df.loc[teacher_df["teacher"] == selected_teacher, "homeroom_class"].values
default_class = homeroom_default[0] if len(homeroom_default) > 0 else ""
homeroom_class = st.text_input("🧑‍🎓 クラス（担任していない場合は手動入力）", value=default_class)

# 日付選択
selected_date = st.date_input("📅 日付を選択", value=today.date())
selected_date_str = selected_date.strftime("%Y-%m-%d")

# 朝・夕選択
mode_label = st.radio("時間帯を選択", ["homeroom-morning", "homeroom-evening"], horizontal=True)

# 生徒マスタ取得
students_df = connect_to_sheet("students_master")
students = students_df[students_df["class"] == homeroom_class]

# 既存出欠ログ取得
log_df = connect_to_sheet("attendance_log")
log_df.columns = log_df.columns.map(str).str.strip()

existing = log_df[
    (log_df["date"] == selected_date_str) &
    (log_df["class"] == homeroom_class) &
    (log_df["entered_by"] == mode_label)
]

statuses = {}
default_status_map = {}

if not existing.empty:
    for _, row in existing.iterrows():
        default_status_map[row["student_id"]] = row["status"]
    st.warning("⚠️ 既に登録された出欠データがあります。変更後に上書き保存されます。")

# 出欠選択
st.subheader("生徒別 出欠入力")
for _, student in students.iterrows():
    sid = student["student_id"]
    name = student["student_name"]
    default = default_status_map.get(sid, "○")
    status = st.selectbox(f"{sid} - {name}", ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保", "×"], key=sid, index=["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保", "×"].index(default))
    statuses[sid] = (name, status)

# アラート：○以外
alert = {sid: (name, s) for sid, (name, s) in statuses.items() if s != "○"}
if alert:
    st.warning("⚠️ ○以外の生徒がいます。 間違いないですか？")
    for sid, (name, s) in alert.items():
        st.write(f"- {sid} - {name}：{s}")

# 書き込み
if st.button("📬 出欠を一括登録", type="primary"):
    write_attendance_log(sheet, selected_date_str, homeroom_class, statuses, selected_teacher, mode_label)
    st.success("✅ 登録が完了しました")