import streamlit as st
from google_sheets_utils import connect_to_sheet, write_attendance
from datetime import datetime
import pandas as pd

st.title("🏫 Homeroom 出欠入力と状況確認")

sheet = connect_to_sheet(st.session_state.json_key_path, st.session_state.sheet_name)
today = datetime.now().strftime("%Y-%m-%d")

st.header("🔵 朝の出欠入力")
class_name = st.text_input("クラス", "1A")
student_id = st.text_input("生徒ID")
student_name = st.text_input("名前")
status_morning = st.selectbox("出欠（朝）", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"])

if st.button("朝の出欠を登録"):
    write_attendance(sheet, class_name, student_id, student_name, status_morning, "homeroom-morning")
    st.success("朝の出欠を登録しました")

st.divider()
st.header("📘 今日の授業出欠状況")
data = sheet.get_all_records()
df_today = pd.DataFrame(data)
df_today = df_today[df_today['date'] == today]
st.dataframe(df_today[df_today['entered_by'].str.startswith('teaching-log')])

st.divider()
st.header("🟢 夕方の出欠入力")
final_period_df = df_today[df_today['entered_by'].str.startswith("teaching-log")]
latest_status = "○"
if not final_period_df.empty:
    latest_status = final_period_df.iloc[-1]['status']

status_evening = st.selectbox("出欠（夕方）", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"],
    index=["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"].index(latest_status))

if st.button("夕方の出欠を登録"):
    write_attendance(sheet, class_name, student_id, student_name, status_evening, "homeroom-evening")
    st.success("夕方の出欠を登録しました")

st.divider()
st.header("📊 定期テスト結果一覧（年5回）")
test_df = pd.DataFrame([row for row in data if row['entered_by'] == 'test-log'])
if not test_df.empty:
    st.dataframe(test_df)
else:
    st.info("定期テストの記録はまだありません。")
