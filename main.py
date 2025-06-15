import streamlit as st
from google_sheets_utils import connect_to_sheet
import pandas as pd

st.title("📋 出欠記録アプリ")

# スプレッドシートへ接続
book = connect_to_sheet()

# 教師マスターの取得
df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())

st.write("👤 教師IDを入力してください")
teacher_id_input = st.text_input("教師ID")

teacher_name = None
homeroom_class = None

if teacher_id_input:
    matched = df[df["teacher_id"] == teacher_id_input]
    if not matched.empty:
        teacher_name = matched.iloc[0]["teacher"]
        homeroom_class = matched.iloc[0]["homeroom_class"]
        st.success(f"教師名: {teacher_name}（{homeroom_class}）")
    else:
        st.error("該当する教師IDが見つかりません。")

if teacher_name:
    if st.button("出欠入力へ"):
        st.switch_page("pages/1_Homeroom.py")
