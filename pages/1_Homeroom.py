import streamlit as st
import pandas as pd
from google_sheets_utils import connect_to_sheet, load_master_dataframe, write_attendance
from datetime import datetime, date

sheet_name = "attendance-shared"
log_sheet_name = "attendance_log"

book = connect_to_sheet(sheet_name)
sheet = book.worksheet(log_sheet_name)
teachers_df = load_master_dataframe(book, "teachers_master")
students_df = load_master_dataframe(book, "students_master")

st.title("🏫 Homeroom 出欠入力（朝・夕対応）")

today = st.date_input("📅 日付を選択", value=date.today())
teacher_label = st.selectbox("👨‍🏫 担任教師を選択（教師ID付き）", 
    [f"{i:03d}：{name}" for i, name in enumerate(teachers_df["teacher"], 1)])
teacher_name = teacher_label.split("：")[1]
homeroom_class_default = teachers_df[teachers_df["teacher"] == teacher_name]["homeroom_class"].values[0]
homeroom_class = st.selectbox("🏫 担任クラスを選択（変更可能）", sorted(students_df["class"].unique()), index=list(sorted(students_df["class"].unique())).index(homeroom_class_default))
mode_label = st.radio("ホームルームの時間帯を選択", ["homeroom-morning", "homeroom-evening"], horizontal=True)

filtered_students = students_df[students_df["class"] == homeroom_class].sort_values("student_id")
statuses = {}

# 既存データ読み込みとデフォルト表示
df_existing = pd.DataFrame(sheet.get_all_records())
if not df_existing.empty and "date" in df_existing.columns and "class" in df_existing.columns and "entered_by" in df_existing.columns:
    df_existing.columns = df_existing.columns.astype(str).str.strip()
    existing_filtered = df_existing[
        (df_existing["date"].astype(str).str.strip() == today.strftime("%Y-%m-%d")) &
        (df_existing["class"].astype(str).str.strip() == homeroom_class) &
        (df_existing["entered_by"].astype(str).str.strip() == mode_label)
    ]
    existing_map = dict(zip(existing_filtered["student_id"], existing_filtered["status"]))
else:
    existing_map = {}

# 出欠入力
for _, row in filtered_students.iterrows():
    sid, name = row["student_id"], row["student_name"]
    default = existing_map.get(sid, "○")
    statuses[sid] = st.selectbox(f"{sid} - {name}", ["○", "×", "／", "公", "病", "事", "忌", "遅", "早", "忌"], index=["○", "×", "／", "公", "病", "事", "忌", "遅", "早", "忌"].index(default))

# ⚪︎以外の一覧
abnormal = [(sid, filtered_students.loc[filtered_students["student_id"] == sid, "student_name"].values[0], status) 
            for sid, status in statuses.items() if status != "○"]

if abnormal:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for sid, name, status in abnormal:
        st.markdown(f"・{sid} - {name}：{status}")
    confirm = st.button("📩 出欠を一括登録")
    if confirm:
        # 上書きチェック
        records = df_existing[
            (df_existing["date"].astype(str).str.strip() == today.strftime("%Y-%m-%d")) &
            (df_existing["class"].astype(str).str.strip() == homeroom_class) &
            (df_existing["entered_by"].astype(str).str.strip() == mode_label)
        ]
        if not records.empty:
            if not st.confirm("⚠️ すでにデータが存在します。上書きしますか？"):
                st.stop()
            # 古いデータ削除（今回は省略）

        for _, row in filtered_students.iterrows():
            sid, name = row["student_id"], row["student_name"]
            status = statuses[sid]
            write_attendance(sheet, homeroom_class, sid, name, status, mode_label, date_override=today)
        st.success("✅ 出欠情報を登録しました。")
