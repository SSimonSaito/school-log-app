import streamlit as st

if "sheet_name" not in st.session_state:
    st.session_state["sheet_name"] = "attendance-shared"

from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe
from datetime import datetime
import pandas as pd

st.title("🏫 Homeroom 出欠入力（マスタ連携）")

book = connect_to_sheet(st.session_state.sheet_name)
sheet = book.worksheet("attendance-shared")
today = datetime.now().strftime("%Y-%m-%d")

# Load student master
students_df = load_master_dataframe(book, "students_master")

# Class and Student selection
class_options = sorted(students_df["class"].unique())
selected_class = st.selectbox("クラス", class_options)

student_options = students_df[students_df["class"] == selected_class]["student_name"]
selected_student = st.selectbox("生徒名", sorted(student_options))

student_row = students_df[(students_df["class"] == selected_class) & (students_df["student_name"] == selected_student)]
student_id = student_row["student_id"].values[0] if not student_row.empty else ""

status_morning = st.selectbox("出欠（朝）", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"])

if st.button("朝の出欠を登録"):
    write_attendance(sheet, selected_class, student_id, selected_student, status_morning, "homeroom-morning")
    st.success("朝の出欠を登録しました")

st.divider()
st.header("📘 今日の授業出欠一覧")
data = sheet.get_all_records()
df_today = pd.DataFrame(data)
df_today = df_today[df_today.get('date') == today]
st.dataframe(df_today[df_today.get('entered_by', '').str.startswith('teaching-log')])

st.divider()
st.header("🟢 夕方の出欠入力")
final_period_df = df_today[df_today.get('entered_by', '').str.startswith("teaching-log")]
latest_status = "○"
if not final_period_df.empty:
    latest_status = final_period_df.iloc[-1]['status']

status_evening = st.selectbox("出欠（夕方）", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"],
    index=["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"].index(latest_status))

if st.button("夕方の出欠を登録"):
    write_attendance(sheet, selected_class, student_id, selected_student, status_evening, "homeroom-evening")
    st.success("夕方の出欠を登録しました")

st.divider()
st.header("📊 定期テスト結果一覧（年5回）")
test_df = pd.DataFrame([row for row in data if row['entered_by'] == 'test-log'])
if not test_df.empty:
    st.dataframe(test_df)
else:
    st.info("定期テストの記録はまだありません。")
