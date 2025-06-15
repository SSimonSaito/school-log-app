
import streamlit as st
import datetime
from google_sheets_utils import connect_to_sheet

st.set_page_config(page_title="出欠入力", layout="centered")

st.title("📘 教師ID入力")

# スプレッドシート接続
sheet = connect_to_sheet("teachers_master")
df = sheet.get_all_records()

# 教師ID一覧とマッピング作成
teacher_id_map = {str(row["teacher_id"]): row["teacher"] for row in df if row["teacher_id"]}
teacher_ids = list(teacher_id_map.keys())

# 教師ID入力
input_id = st.text_input("👤 教師IDを入力してください")

# 教師名の表示
if input_id in teacher_id_map:
    st.success(f"教師名：{teacher_id_map[input_id]}")
    teacher_name = teacher_id_map[input_id]
else:
    teacher_name = None

# 日付選択（デフォルト：今日）
today = datetime.date.today()
selected_date = st.date_input("📅 日付を選択してください", value=today)

# ボタンでページ遷移（セッションに値を保存）
if teacher_name and st.button("出欠入力へ"):
    st.session_state["teacher_id"] = input_id
    st.session_state["teacher_name"] = teacher_name
    st.session_state["selected_date"] = selected_date
    st.switch_page("pages/1_Homeroom.py")
