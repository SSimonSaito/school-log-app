import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe

st.set_page_config(page_title="Homeroom 出欠入力（朝・夕対応）")

sheet_name = st.session_state.sheet_name if "sheet_name" in st.session_state else "attendance_log"
book = connect_to_sheet(sheet_name)

teachers_df = load_master_dataframe(book, "teachers_master")
students_df = load_master_dataframe(book, "students_master")
attendance_sheet = book.worksheet("attendance_log")

# 日付・教師・担任クラス選択
today = datetime.now() + timedelta(hours=9)
date_selected = st.date_input("📅 日付を選択", today.date())

teachers_df = teachers_df.dropna(subset=["teacher"])
teachers_df = teachers_df.reset_index(drop=True)

teacher_options = [
    f"T{str(i+1).zfill(3)}：{row['teacher']}" for i, row in teachers_df.iterrows()
]
selected_teacher = st.selectbox("👨‍🏫 担任教師を選択", teacher_options)
teacher_index = teacher_options.index(selected_teacher)
default_class = teachers_df.loc[teacher_index, "homeroom_class"]

homeroom_class = st.selectbox("🏫 担任クラスを選択", sorted(students_df["class"].unique()), index=list(sorted(students_df["class"].unique())).index(default_class))

# 朝夕モード
mode_label = st.radio("時間帯を選択", ["homeroom-morning", "homeroom-evening"], horizontal=True)

# 生徒リストと初期状態
students = students_df[students_df["class"] == homeroom_class].sort_values("student_id")
status_map = {"⚪︎": "○", "✕": "×", "／": "／", "病": "病", "事": "事", "公": "公", "忌": "忌"}

existing_data = attendance_sheet.get_all_records()
df_existing = pd.DataFrame(existing_data)

if not df_existing.empty:
    df_existing.columns = df_existing.columns.astype(str).str.strip()
    records = df_existing[
        (df_existing["date"] == str(date_selected)) &
        (df_existing["class"] == homeroom_class) &
        (df_existing["entered_by"] == mode_label)
    ]
else:
    records = pd.DataFrame()

# デフォルト表示
statuses = {}
for _, row in students.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    previous = records[records["student_id"] == sid]["status"]
    default_status = previous.values[0] if not previous.empty else "○"
    statuses[sid] = st.selectbox(f"{sid} - {name}", options=list(status_map.values()), index=list(status_map.values()).index(default_status))

# ○以外の表示と確認
non_default = {k: v for k, v in statuses.items() if v != "○"}
if non_default:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for sid in non_default:
        name = students[students["student_id"] == sid]["student_name"].values[0]
        st.write(f"・{sid} - {name}：{statuses[sid]}")

# 上書きチェックと登録
if st.button("📮 出欠を一括登録"):
    if not records.empty:
        if not st.session_state.get("confirmed_overwrite", False):
            st.session_state.confirmed_overwrite = st.radio("すでに出欠データがあります。上書きしますか？", ["はい", "いいえ"]) == "はい"
        if not st.session_state.confirmed_overwrite:
            st.warning("登録がキャンセルされました。")
            st.stop()
        else:
            df_existing = df_existing[~(
                (df_existing["date"] == str(date_selected)) &
                (df_existing["class"] == homeroom_class) &
                (df_existing["entered_by"] == mode_label)
            )]
            attendance_sheet.clear()
            attendance_sheet.append_row(df_existing.columns.tolist())
            for row in df_existing.values.tolist():
                attendance_sheet.append_row(row)

    for sid, status in statuses.items():
        name = students[students["student_id"] == sid]["student_name"].values[0]
        write_attendance(attendance_sheet, homeroom_class, sid, name, status, mode_label, date_override=date_selected)
    st.success("✅ 登録が完了しました。")