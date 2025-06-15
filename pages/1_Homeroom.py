
import streamlit as st
from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe, load_attendance_log
from datetime import datetime, timedelta, timezone
import pandas as pd

st.title("🏫 Homeroom 出欠入力")

sheet_name = "attendance_log"
book = connect_to_sheet(sheet_name)
sheet = book.worksheet(sheet_name)

teachers_df = load_master_dataframe(book, "teachers_master")
students_df = load_master_dataframe(book, "students_master")

today = st.date_input("📅 日付を選択", datetime.now().date())
mode = st.radio("ホームルーム種別を選択", ["朝", "夕方"])
mode_label = "homeroom-morning" if mode == "朝" else "homeroom-evening"

teachers_df["label"] = teachers_df.index.map(lambda i: f"T{str(i+1).zfill(3)}: {teachers_df.loc[i, 'teacher']}")
teacher_selected = st.selectbox("👨‍🏫 担任教師を選択", teachers_df["label"].tolist())
selected_teacher = teachers_df.loc[teachers_df["label"] == teacher_selected].iloc[0]
default_class = selected_teacher["homeroom_class"]

homeroom_class = st.selectbox("🏫 クラスを選択", students_df["class"].unique(), index=list(students_df["class"].unique()).index(default_class))
class_students = students_df[students_df["class"] == homeroom_class].sort_values("student_id")

# 過去データの確認と初期化
df_existing = load_attendance_log(book)
existing_today = df_existing[
    (df_existing["date"] == str(today)) &
    (df_existing["class"] == homeroom_class) &
    (df_existing["entered_by"] == mode_label)
]
existing_map = {(r["student_id"]): r["status"] for _, r in existing_today.iterrows()}

statuses = ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "忖"]
student_status = {}

for _, row in class_students.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    default = existing_map.get(sid, "○")
    student_status[sid] = st.selectbox(f"{sid} - {name}", statuses, index=statuses.index(default))

non_present = {sid: status for sid, status in student_status.items() if status != "○"}
if non_present:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for sid in non_present:
        student_name = class_students[class_students["student_id"] == sid]["student_name"].values[0]
        st.write(f"・{sid} - {student_name}：{non_present[sid]}")

if st.button("📩 出欠を一括登録"):
    # 既存削除
    rows_to_delete = df_existing[
        (df_existing["date"] == str(today)) &
        (df_existing["class"] == homeroom_class) &
        (df_existing["entered_by"] == mode_label)
    ].index.tolist()
    sheet_values = sheet.get_all_values()
    for i in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(i+2)  # header offset

    jst = datetime.now(timezone(timedelta(hours=9)))
    timestamp = jst.strftime("%Y-%m-%d %H:%M:%S")

    for _, row in class_students.iterrows():
        sid = row["student_id"]
        name = row["student_name"]
        status = student_status[sid]
        write_attendance(sheet, str(today), timestamp, homeroom_class, sid, name, status, mode_label)
    st.success("✅ 出欠情報が登録されました。")
