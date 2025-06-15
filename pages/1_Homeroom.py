import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets_utils import connect_to_sheet, write_attendance, overwrite_attendance, load_master_dataframe

sheet_name = "attendance_log"
book = connect_to_sheet(sheet_name)
sheet = book.worksheet(sheet_name)

today = datetime.today()

st.title("🏫 Homeroom 出欠入力（朝・夕対応）")
date = st.date_input("📅 日付を選択", today)

teachers_df = load_master_dataframe(book, "teachers_master")
teachers_df["label"] = teachers_df.index.map(lambda i: f"T{str(i+1).zfill(3)}：{teachers_df.loc[i, 'teacher']}")
teacher_label = st.selectbox("👨‍🏫 教師を選択", teachers_df["label"])

teacher_index = int(teacher_label[1:4]) - 1
default_class = teachers_df.loc[teacher_index, "homeroom_class"]
homeroom_class = st.selectbox("🏫 クラスを選択", sorted(teachers_df["homeroom_class"].dropna().unique()), index=list(sorted(teachers_df["homeroom_class"].dropna().unique())).index(default_class))

mode_label = st.radio("🕒 ホームルーム区分", ["homeroom-morning", "homeroom-evening"])

students_df = load_master_dataframe(book, "students_master")
students = students_df[students_df["class"] == homeroom_class].sort_values("student_id")

log_df = pd.DataFrame(sheet.get_all_records())
log_df.columns = log_df.columns.astype(str).str.strip().str.lower()

records = None
if not log_df.empty:
    mask = (
        (log_df["date"].astype(str).str.strip() == date.strftime("%Y-%m-%d")) &
        (log_df["class"] == homeroom_class) &
        (log_df["entered_by"] == mode_label)
    )
    records = log_df[mask].set_index("student_id") if mask.any() else None

status_options = ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "悩"]

attendance_data = {}
for _, row in students.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    default = records.loc[sid]["status"] if records is not None and sid in records.index else "○"
    attendance_data[sid] = {
        "name": name,
        "status": st.selectbox(f"{sid} - {name}", status_options, index=status_options.index(default))
    }

non_ok = {sid: d for sid, d in attendance_data.items() if d["status"] != "○"}
if non_ok:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for sid, d in non_ok.items():
        st.write(f"・{sid} - {d['name']}：{d['status']}")

if st.button("📩 出欠を一括登録"):
    if records is not None and not records.empty:
        if st.confirm("すでにデータが存在します。上書きしますか？"):
            overwrite_attendance(sheet, date, homeroom_class, mode_label)
        else:
            st.stop()
    for sid, d in attendance_data.items():
        write_attendance(sheet, homeroom_class, sid, d["name"], d["status"], mode_label, date_override=date)
    st.success("✅ 出欠データを登録しました。")
