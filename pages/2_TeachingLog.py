import streamlit as st
from google_sheets_utils import connect_to_sheet, write_attendance
from datetime import datetime
import pandas as pd

st.title("📒 Teaching Log - 授業出欠と定期テスト入力")

sheet = connect_to_sheet(st.session_state.sheet_name)
today = datetime.now().strftime("%Y-%m-%d")

st.header("📗 授業ごとの出欠入力")
class_name = st.text_input("クラス", "1A")
student_id = st.text_input("生徒ID")
student_name = st.text_input("名前")
period = st.selectbox("時限", ["1限", "2限", "3限", "4限", "5限", "6限"])
subject = st.text_input("科目名", "国語")

data = sheet.get_all_records()
df_today = pd.DataFrame(data)
df_today = df_today[df_today['date'] == today]
student_records = df_today[df_today['student_id'] == student_id]

previous_status = "○"
if period == "1限":
    morning_record = student_records[student_records['entered_by'] == "homeroom-morning"]
    if not morning_record.empty:
        previous_status = morning_record.iloc[-1]['status']
else:
    periods = ["1限", "2限", "3限", "4限", "5限", "6限"]
    i = periods.index(period)
    prev_period = periods[i-1]
    prev_record = student_records[student_records['entered_by'] == f"teaching-log:{prev_period}"]
    if not prev_record.empty:
        previous_status = prev_record.iloc[-1]['status']

status = st.selectbox("出欠（編集可能）", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"],
    index=["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"].index(previous_status))

if st.button("出欠を登録"):
    write_attendance(sheet, class_name, student_id, student_name, status, f"teaching-log:{period}")
    st.success(f"{period} の出欠を登録しました。")

st.divider()
st.header("📝 定期テストの点数入力")
term = st.selectbox("学期・回数", ["第1回", "第2回", "第3回", "第4回", "第5回"])
test_subject = st.text_input("科目", "数学")
score = st.number_input("点数", min_value=0, max_value=100, step=1)

if st.button("テスト結果を登録"):
    sheet.append_row([today, class_name, student_id, student_name, f"{test_subject}:{term}:{score}", "test-log"])
    st.success("テスト結果を記録しました。")
