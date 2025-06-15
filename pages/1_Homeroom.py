import streamlit as st
import pandas as pd
import datetime
from google_sheets_utils import connect_to_sheet, load_master_dataframe, write_attendance

st.title("🏫 Homeroom 出欠入力")

mode = st.radio("朝・夕を選択", ["朝", "夕"], horizontal=True)
mode_label = "homeroom-morning" if mode == "朝" else "homeroom-evening"

sheet_name = "attendance_log"
sheet = connect_to_sheet(sheet_name)

today = datetime.date.today()
df_existing = pd.DataFrame(sheet.get_all_records())
if not df_existing.empty:
    df_existing.columns = df_existing.columns.str.strip()
    exists_today = df_existing[
        (df_existing["date"].astype(str).str.strip() == str(today)) &
        (df_existing["entered_by"] == mode_label)
    ]
else:
    exists_today = pd.DataFrame()

book = connect_to_sheet("teachers_master").spreadsheet
df_teachers = load_master_dataframe(book, "teachers_master")
df_students = load_master_dataframe(book, "students_master")

teachers = df_teachers[df_teachers["homeroom_class"].notna()]
teacher_option = st.selectbox("担当クラスを選択", teachers["homeroom_class"].unique())

students = df_students[df_students["class"] == teacher_option].sort_values("student_id")
status_options = ["○", "×", "公", "病", "事", "忌", "停", "遅", "早", "保"]
statuses = {}

for _, row in students.iterrows():
    sid, name = row["student_id"], row["student_name"]
    key = f"{sid}-{name}"
    default = "○"
    if not exists_today.empty:
        match = exists_today[exists_today["student_id"] == sid]
        if not match.empty:
            default = match["status"].values[0]
    statuses[key] = st.radio(f"{key}", status_options, horizontal=True, index=status_options.index(default))

others = {k: v for k, v in statuses.items() if v != "○"}
if others:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for k, v in others.items():
        st.markdown(f"- {k}：{v}")

if st.button("📬 出欠を一括登録"):
    records = []
    for key, status in statuses.items():
        sid, name = key.split("-", 1)
        records.append([str(today), "", teacher_option, sid, name, status, mode_label])
    if not exists_today.empty:
        if st.confirm("⚠️ 既存データがあります。上書きしますか？"):
            write_attendance(sheet, records)
            st.success("上書き保存しました。")
    else:
        write_attendance(sheet, records)
        st.success("出欠を登録しました。")
