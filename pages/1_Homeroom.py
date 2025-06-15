
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import (
    connect_to_gsheet,
    get_existing_attendance,
    write_attendance_data,
    write_status_log,
)

# JST timezone handling
def get_jst_now():
    return datetime.utcnow() + timedelta(hours=9)

# 教師・日付の引き継ぎ
if "selected_teacher" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher = st.session_state["selected_teacher"]
selected_date = st.session_state["selected_date"]
sheet_attendance = connect_to_gsheet("attendance_log")
sheet_students = connect_to_gsheet("students_master")
sheet_status_log = connect_to_gsheet("student_statuslog")

st.title("🏫 Homeroom 出欠入力")
st.write(f"👩‍🏫 教師: {teacher}")
st.write(f"📅 日付: {selected_date}")

# 朝・夕のホームルーム選択
period = st.radio("🕒 ホームルーム区分を選択してください", ("MHR（朝）", "EHR（夕）"))
period_code = "MHR" if "朝" in period else "EHR"

# クラス情報取得（教師が担任するクラスを初期値に）
df_teachers = connect_to_gsheet("teachers_master").get_all_records()
df_teachers = pd.DataFrame(df_teachers)
homeroom_class = df_teachers[df_teachers["teacher"] == teacher]["homeroom_class"].values[0]
selected_class = st.selectbox("📘 クラスを選択", df_teachers["homeroom_class"].dropna().unique(), index=list(df_teachers["homeroom_class"]).index(homeroom_class))

# 生徒一覧取得
students_df = pd.DataFrame(sheet_students.get_all_records())
students_df = students_df[students_df["class"] == selected_class].copy()

# 既存出欠情報取得（date/class/periodで絞る）
existing_df = get_existing_attendance(sheet_attendance)
existing_today = existing_df[
    (existing_df["date"] == selected_date)
    & (existing_df["class"] == selected_class)
    & (existing_df["period"] == period_code)
]

# 出欠選択肢
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]

st.subheader("出欠入力")

statuses = {}
for _, row in students_df.iterrows():
    student_id = row["student_id"]
    name = row["student_name"]
    default_status = "○"
    match = existing_today[existing_today["student_id"] == student_id]
    if not match.empty:
        default_status = match["status"].values[0]
    statuses[student_id] = st.radio(f"{name}", status_options, index=status_options.index(default_status), horizontal=True)

# 登録処理
if st.button("📥 出欠を一括登録"):
    if not existing_today.empty:
        if not st.checkbox("⚠️ 既存データがあります。上書きしますか？"):
            st.warning("⛔ 上書きに同意してください。")
            st.stop()

    jst_now = get_jst_now()
    data_to_write = []
    for _, row in students_df.iterrows():
        student_id = row["student_id"]
        name = row["student_name"]
        status = statuses[student_id]
        data_to_write.append({
            "timestamp": jst_now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": selected_date,
            "class": selected_class,
            "student_id": student_id,
            "student_name": name,
            "status": status,
            "entered_by": teacher,
            "period": period_code,
        })
    write_attendance_data(sheet_attendance, data_to_write)
    st.success("✅ 出欠登録が完了しました。")

    # 確認対象者リスト表示
    flagged = [row for row in data_to_write if row["status"] != "○"]
    if flagged:
        st.warning("⚠️ 以下の生徒は確認が必要です。")
        for row in flagged:
            col1, col2, col3 = st.columns([2, 3, 5])
            with col1:
                st.write(f"{row['student_name']}（{row['status']}）")
            with col2:
                confirm = st.checkbox("✔️ 確認済", key=f"confirm_{row['student_id']}")
            with col3:
                comment = st.text_input("📝 コメント", key=f"comment_{row['student_id']}")

            if confirm:
                write_status_log(sheet_status_log, {
                    "timestamp": jst_now.strftime("%Y-%m-%d %H:%M:%S"),
                    "class": row["class"],
                    "student_id": row["student_id"],
                    "student_name": row["student_name"],
                    "status": row["status"],
                    "entered_by": teacher,
                    "period": period_code,
                    "comment": st.session_state.get(f"comment_{row['student_id']}", ""),
                })
                st.success(f"{row['student_name']} の確認ログを登録しました。")
