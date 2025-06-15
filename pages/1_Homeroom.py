
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google_sheets_utils import (
    connect_to_sheet,
    write_attendance_data,
    write_status_log,
    get_existing_attendance,
)

# JSTタイムスタンプ関数
def get_jst_now():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

# セッションステートから教師情報と日付を取得
if "selected_teacher" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher_name = st.session_state.selected_teacher
selected_date = st.session_state.selected_date

st.title("🏫 Homeroom 出欠入力")
st.write(f"👩‍🏫 教師: {teacher_name}")
st.write(f"📅 日付: {selected_date}")

# HR区分選択
period = st.radio("HR区分を選択してください", ("MHR", "EHR"), horizontal=True)

# シート接続
attendance_sheet = connect_to_sheet("attendance_log")
statuslog_sheet = connect_to_sheet("student_statuslog")
students_df = connect_to_sheet("students_master")

# クラス選択（代理入力対応）
homeroom_class = st.selectbox("クラスを選択してください", students_df["class"].unique())

# 選択クラスの生徒一覧を取得
students = students_df[students_df["class"] == homeroom_class].sort_values("student_id")

# 既存出欠取得
df_existing = get_existing_attendance(attendance_sheet)
df_existing_today = df_existing[
    (df_existing["date"] == selected_date)
    & (df_existing["class"] == homeroom_class)
    & (df_existing["period"] == period)
]

# 出欠入力
st.subheader("出欠入力")
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
attendance_data = []

for _, row in students.iterrows():
    default_status = "○"
    matched = df_existing_today[df_existing_today["student_id"] == row["student_id"]]
    if not matched.empty:
        default_status = matched.iloc[0]["status"]
    status = st.radio(
        f"{row['student_id']} {row['student_name']}",
        status_options,
        index=status_options.index(default_status),
        key=row["student_id"],
        horizontal=True,
    )
    attendance_data.append(
        {
            "timestamp": get_jst_now(),
            "date": selected_date,
            "class": homeroom_class,
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "status": status,
            "entered_by": teacher_name,
            "period": period,
        }
    )

# 確認・保存処理
if any(d["status"] != "○" for d in attendance_data):
    st.warning("⚠️ 出席以外のステータスが含まれています。下記に一覧を表示します。")
    for d in attendance_data:
        if d["status"] != "○":
            comment = st.text_input(f"📝 {d['student_id']} {d['student_name']} のコメント", key=f"cmt_{d['student_id']}")
            d["comment"] = comment

if df_existing_today.empty:
    if st.button("✅ 出欠を登録"):
        write_attendance_data(attendance_sheet, attendance_data)
        st.success("✅ 出欠を登録しました")
        status_data = [d for d in attendance_data if d["status"] != "○"]
        if status_data:
            write_status_log(statuslog_sheet, status_data)
else:
    if st.checkbox("⚠️ すでに出欠データがあります。上書きしますか？"):
        if st.button("✅ 出欠を上書き登録"):
            write_attendance_data(attendance_sheet, attendance_data, overwrite=True, date=selected_date, class_=homeroom_class, period=period)
            st.success("✅ 出欠を上書き登録しました")
            status_data = [d for d in attendance_data if d["status"] != "○"]
            if status_data:
                write_status_log(statuslog_sheet, status_data)
