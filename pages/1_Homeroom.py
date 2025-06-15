import streamlit as st
import pandas as pd
import datetime
import pytz
import os
import sys

# 親ディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google_sheets_utils import (
    connect_to_sheet,
    write_attendance_data,
    write_status_log,
    get_existing_attendance
)

# セッションステートの確認
if "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

# タイトルと前提表示
st.title("🏫 Homeroom 出欠入力")
teacher_name = st.session_state.teacher_name
selected_date = st.session_state.selected_date
st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date}")

# Google Sheets接続とシート取得
book = connect_to_sheet("attendance-shared")
students_df = pd.DataFrame(book.worksheet("students_master").get_all_records())
log_sheet = book.worksheet("attendance_log")
log_df = get_existing_attendance(log_sheet)
statuslog_sheet = book.worksheet("student_statuslog")

# 担任クラス取得（デフォルト）
teachers_df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())
homeroom_class = teachers_df.query("teacher == @teacher_name")["homeroom_class"].values[0]
selected_class = st.selectbox("📚 クラスを選択してください（代理入力可能）", sorted(students_df["class"].unique()), index=list(students_df["class"].unique()).index(homeroom_class))

# 朝・夕の選択
period = st.radio("🕰️ ホームルームの時間帯を選択してください", ["朝", "夕"], horizontal=True)
period_code = "MHR" if period == "朝" else "EHR"

# 指定クラスの生徒取得
target_students = students_df[students_df["class"] == selected_class]

# 過去ログの抽出
existing = log_df[
    (log_df["date"] == selected_date)
    & (log_df["class"] == selected_class)
    & (log_df["period"] == period_code)
]

# デフォルト値設定（既存があれば反映）
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
status_dict = {}
for _, row in target_students.iterrows():
    student_id = row["student_id"]
    name = row["student_name"]
    prior = existing[existing["student_id"] == student_id]
    default = prior["status"].values[0] if not prior.empty else "○"
    status = st.radio(f"{name}", options=status_options, index=status_options.index(default), horizontal=True, key=student_id)
    status_dict[student_id] = {
        "name": name,
        "status": status
    }

# 入力確認
abnormal_students = {k: v for k, v in status_dict.items() if v["status"] != "○"}
if abnormal_students:
    st.warning("⚠️ 以下の生徒は○以外の出欠状態です：")
    for sid, info in abnormal_students.items():
        st.write(f"- {info['name']}: {info['status']}")

# 上書き確認と登録
if st.button("📥 出欠を一括登録"):
    if not existing.empty:
        if not st.confirm("⚠️ すでに入力済みのデータがあります。上書きしますか？"):
            st.stop()

    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    records = []
    for sid, info in status_dict.items():
        records.append({
            "date": selected_date,
            "timestamp": now,
            "class": selected_class,
            "student_id": sid,
            "student_name": info["name"],
            "status": info["status"],
            "entered_by": teacher_name,
            "period": period_code
        })

    write_attendance_data(log_sheet, records)

    if abnormal_students:
        status_records = []
        for sid, info in abnormal_students.items():
            comment = st.text_input(f"📝 コメント（{info['name']}）", key=f"comment_{sid}")
            if st.checkbox(f"✅ {info['name']}の状況を確認済みにする", key=f"confirm_{sid}"):
                status_records.append({
                    "timestamp": now,
                    "class": selected_class,
                    "student_id": sid,
                    "student_name": info["name"],
                    "status": info["status"],
                    "entered_by": teacher_name,
                    "period": period_code,
                    "comment": comment
                })
        if status_records:
            write_status_log(statuslog_sheet, status_records)
            st.success("✅ 出欠・状況ログを保存しました。")
