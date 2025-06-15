import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets_utils import connect_to_sheet, write_attendance, load_master_dataframe

st.title("🏫 Homeroom 出欠入力")

sheet_name = "attendance_log"
sheet = connect_to_sheet(sheet_name)
df_existing = load_master_dataframe(sheet)

today = datetime.now().date()
teachers_df = load_master_dataframe(connect_to_sheet("teachers_master"))
students_df = load_master_dataframe(connect_to_sheet("students_master"))

# 担任教師選択
teacher_options = teachers_df.index.to_series().astype(str) + ": " + teachers_df["teacher"]
selected_teacher = st.selectbox("👨‍🏫 担任教師を選択", teacher_options)
teacher_id = selected_teacher.split(":")[0]

# クラス選択（デフォルトは担任クラス）
default_class = teachers_df.loc[int(teacher_id), "homeroom_class"]
selected_class = st.selectbox("🏫 クラスを選択", sorted(students_df["class"].unique()), index=list(sorted(students_df["class"].unique())).index(default_class))

# 朝・夕の選択
mode_label = st.radio("朝のホームルーム or 夕方のホームルーム", ["homeroom-morning", "homeroom-evening"])

# 該当クラスの生徒一覧
filtered_students = students_df[students_df["class"] == selected_class].sort_values("student_id")

# 既存のデータ取得
df_existing.columns = df_existing.columns.map(str)
if "date" in df_existing.columns:
    existing_today = df_existing[
        (df_existing["date"] == str(today)) &
        (df_existing["class"] == selected_class) &
        (df_existing["entered_by"] == mode_label)
    ]
else:
    existing_today = pd.DataFrame()

statuses = {}
for _, row in filtered_students.iterrows():
    sid = row["student_id"]
    name = row["student_name"]
    default_status = "○"
    if not existing_today.empty:
        existing_row = existing_today[existing_today["student_id"] == sid]
        if not existing_row.empty:
            default_status = existing_row.iloc[0]["status"]
    statuses[sid] = st.selectbox(f"{sid} - {name}", ["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"], index=["○", "×", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"].index(default_status))

# ○以外の確認
abnormal = [(sid, row["student_name"], statuses[sid]) for _, row in filtered_students.iterrows() if statuses[sid] != "○"]

if abnormal:
    st.warning("⚠️ ○以外の生徒がいます。間違いないですか？")
    for sid, name, status in abnormal:
        st.markdown(f"・{sid} - {name}：{status}")

# 上書きチェック
if not existing_today.empty:
    if st.button("⚠️ 上書きして登録"):
        indices_to_drop = df_existing[
            (df_existing["date"] == str(today)) &
            (df_existing["class"] == selected_class) &
            (df_existing["entered_by"] == mode_label)
        ].index
        df_existing.drop(indices_to_drop, inplace=True)
        sheet.clear()
        sheet.append_row(["date", "timestamp", "class", "student_id", "student_name", "status", "entered_by"])
        for _, row in df_existing.iterrows():
            sheet.append_row(row.tolist())
        for _, row in filtered_students.iterrows():
            write_attendance(sheet, selected_class, row["student_id"], row["student_name"], statuses[row["student_id"]], mode_label, date_override=today)
        st.success("上書きしました ✅")
else:
    if st.button("📩 出欠を一括登録"):
        for _, row in filtered_students.iterrows():
            write_attendance(sheet, selected_class, row["student_id"], row["student_name"], statuses[row["student_id"]], mode_label, date_override=today)
        st.success("登録しました ✅")
