import streamlit as st

if "sheet_name" not in st.session_state:
    st.session_state["sheet_name"] = "attendance-shared"

from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe
from datetime import datetime
import pandas as pd

st.title("🏫 Homeroom 出欠入力（柔軟な担任対応）")

book = connect_to_sheet(st.session_state.sheet_name)
sheet = book.worksheet("attendance-shared")
today = st.date_input("出欠日付", value=datetime.today(), format="YYYY-MM-DD")

# マスタの読み込み
teachers_df = load_master_dataframe(book, "teachers_master")
students_df = load_master_dataframe(book, "students_master")

# 教師選択（教師コード順）
teachers_df = teachers_df.sort_values("teacher_code")
teacher_display = teachers_df["teacher_code"] + "：" + teachers_df["teacher"]
selected_display = st.selectbox("担任教師を選択", teacher_display.tolist())
teacher_code = selected_display.split("：")[0]
teacher_row = teachers_df[teachers_df["teacher_code"] == teacher_code]
teacher_name = teacher_row["teacher"].values[0]

# 担任クラス候補（空欄も許容）
suggested_class = teacher_row["homeroom_class"].values[0] if not teacher_row.empty else ""
available_classes = sorted(students_df["class"].dropna().unique())
homeroom_class = st.selectbox("対象クラスを選択（編集可能）", available_classes, index=available_classes.index(suggested_class) if suggested_class in available_classes else 0)

# 生徒一覧の表示
students_in_class = students_df[students_df["class"] == homeroom_class].sort_values("student_id")
statuses = ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

st.header(f"{homeroom_class} の生徒出欠入力（朝）")
attendance_inputs = {}

for _, row in students_in_class.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    default = "○"
    status = st.selectbox(f"{sid} - {name}", statuses, index=statuses.index(default), key=sid)
    attendance_inputs[sid] = (name, status)

if st.button("📥 出欠を一括登録"):
    for sid, (name, status) in attendance_inputs.items():
        write_attendance(sheet, homeroom_class, sid, name, status, "homeroom-morning", date_override=today)
    st.success(f"{homeroom_class} の朝の出欠を登録しました。")
