import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from google_sheets_utils import connect_to_sheet, write_attendance_data, write_status_log, get_existing_attendance

st.set_page_config(page_title="Homeroom 出欠入力", page_icon="🏫")

# セッションステートから教師情報と日付を取得
if "selected_teacher" not in st.session_state or "selected_date" not in st.session_state:
    st.warning("main画面から教師と日付を選択してください。")
    st.stop()

teacher = st.session_state["selected_teacher"]
teacher_id = st.session_state["selected_teacher_id"]
date = st.session_state["selected_date"]

st.title("🏫 Homeroom 出欠入力")
st.markdown(f"👩‍🏫 教師: {teacher}")
st.markdown(f"📅 日付: {date}")

# HRの時間帯を選択
period = st.radio("HRの時間帯を選択してください", ("朝", "夕"))
period_code = "MHR" if period == "朝" else "EHR"

# Google Sheets 接続
book = connect_to_sheet()
students_df = pd.DataFrame(book.worksheet("students_master").get_all_records())
teachers_df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())
attendance_ws = book.worksheet("attendance_log")
statuslog_ws = book.worksheet("student_statuslog")

# 教師が担当するクラス（担任）を取得、ただし変更可能とする
default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values[0]
selected_class = st.selectbox("クラスを選択してください", students_df["class"].unique(), index=list(students_df["class"].unique()).index(default_class))

# 対象クラスの生徒を抽出
students = students_df[students_df["class"] == selected_class].copy()

# 既存データ読み込み
attendance_df = pd.DataFrame(attendance_ws.get_all_records())
existing_entries = attendance_df[
    (attendance_df["date"] == date) &
    (attendance_df["class"] == selected_class) &
    (attendance_df["period"] == period_code)
]

# 出欠入力フォーム
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
status_inputs = {}

st.subheader("出欠入力")

for _, row in students.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]
    existing_status = existing_entries[existing_entries["student_id"] == student_id]["status"].values
    default_status = existing_status[0] if len(existing_status) > 0 else "○"
    status = st.radio(f"{student_name}", status_options, index=status_options.index(default_status), horizontal=True, key=student_id)
    status_inputs[student_id] = {"name": student_name, "status": status}

# 入力済み確認
if not existing_entries.empty:
    if not st.checkbox("⚠️ すでに入力済みのデータがあります。上書きしますか？"):
        st.stop()

# 登録確定前チェック
invalid_students = {sid: val for sid, val in status_inputs.items() if val["status"] != "○"}

if invalid_students:
    st.warning("⚠️ 下記の生徒が『○』以外で入力されています。状況確認が必要です。")
    for sid, val in invalid_students.items():
        st.markdown(f"- {val['name']}：{val['status']}")

# 出欠登録ボタン
if st.button("📋 出欠を一括登録"):
    timestamp = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    new_data = []

    for sid, val in status_inputs.items():
        new_data.append({
            "date": date,
            "timestamp": timestamp,
            "class": selected_class,
            "student_id": sid,
            "student_name": val["name"],
            "status": val["status"],
            "entered_by": teacher,
            "period": period_code,
            "comment": ""
        })

    write_attendance_data(attendance_ws, new_data)

    st.success("✅ 出欠情報を登録しました。")

    # 状況確認セクション
    st.subheader("状況確認が必要な生徒")
    status_review = []

    for entry in new_data:
        if entry["status"] != "○":
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 3])
                with col1:
                    st.markdown(f"👤 {entry['student_name']}（{entry['status']}）")
                with col2:
                    entry["confirmed"] = st.checkbox("確認済み", key=f"chk_{entry['student_id']}")
                with col3:
                    entry["comment"] = st.text_input("コメント", key=f"cmt_{entry['student_id']}")
                status_review.append(entry)

    # 確認済み以外のみ student_statuslog に保存
    if st.button("📝 状況確認ログを保存"):
        status_to_log = []
        for entry in status_review:
            if not entry.get("confirmed"):
                status_to_log.append({
                    "timestamp": timestamp,
                    "class": entry["class"],
                    "student_id": entry["student_id"],
                    "student_name": entry["student_name"],
                    "status": entry["status"],
                    "entered_by": teacher,
                    "period": entry["period"],
                    "comment": entry["comment"]
                })

        if status_to_log:
            write_status_log(statuslog_ws, status_to_log)
            st.success("✅ 状況確認ログを保存しました。")
        else:
            st.info("全ての生徒が確認済みです。")
