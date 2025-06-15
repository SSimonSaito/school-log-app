import streamlit as st
from google_sheets_utils import connect_to_sheet
import pandas as pd
from datetime import datetime
import pytz

st.title("🏫 ホームルーム 出欠入力")

sheet_url = st.secrets["spreadsheet_id"]
sheet = connect_to_sheet(sheet_url, "attendance_log")

# 入力欄
teacher_name = st.text_input("👤 担任の先生の名前（または代理入力者）")
homeroom_class = st.text_input("🏷️ クラス（例: 1A）")

# 日本時間の今日
today = datetime.now(pytz.timezone("Asia/Tokyo")).date()
date = st.date_input("📅 日付", today)

# 生徒情報
students = [f"S{str(i).zfill(3)}" for i in range(1, 11)]
data = []
statuses = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

for student_id in students:
    cols = st.columns([1, 3, 3])
    with cols[0]:
        st.markdown(student_id)
    with cols[1]:
        student_name = st.text_input(f"{student_id}_name", label_visibility="collapsed", placeholder="氏名")
    with cols[2]:
        status = st.radio(f"{student_id}_status", statuses, horizontal=True, label_visibility="collapsed", index=0)
    data.append({
        "date": date.strftime("%Y-%m-%d"),
        "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
        "class": homeroom_class,
        "student_id": student_id,
        "student_name": student_name,
        "status": status,
        "entered_by": teacher_name
    })

# 送信
if st.button("✅ 出欠を記録する"):
    sheet.append_rows([list(d.values()) for d in data])
    st.success("出欠を記録しました")