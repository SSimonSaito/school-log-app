import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_attendance_data,
    write_status_log,
    get_existing_attendance,
)
import pytz

st.set_page_config(page_title="Homeroom 出欠入力", layout="centered")
st.title("🏫 Homeroom 出欠入力")

# セッションチェック
if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

# セッション情報取得
teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date}")

# HR区分選択
period = st.radio("HR区分を選択してください", ["MHR", "EHR"])

# スプレッドシート接続
book = connect_to_sheet("attendance-shared")

# 各マスター取得
students_df = get_worksheet_df(book, "students_master")
teachers_df = get_worksheet_df(book, "teachers_master")

# 担任クラスを取得し、クラス選択
default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values
default_class = default_class[0] if len(default_class) > 0 else ""
class_list = sorted(students_df["class"].dropna().unique())
homeroom_class = st.selectbox("🏫 クラスを選択してください", class_list, index=class_list.index(default_class) if default_class in class_list else 0)

# クラス内生徒取得
students_in_class = students_df[students_df["class"] == homeroom_class].copy()

# 出欠ログ取得
existing_df = get_existing_attendance(book, "attendance_log")
today_str = selected_date.strftime("%Y-%m-%d")

# MHRデータ抽出（EHRデフォルト用）
mhr_today_df = existing_df[
    (existing_df["class"] == homeroom_class)
    & (existing_df["period"] == "MHR")
    & (existing_df["date"] == today_str)
]

# 現在の period の既存データ
existing_today = existing_df[
    (existing_df["class"] == homeroom_class)
    & (existing_df["period"] == period)
    & (existing_df["date"] == today_str)
]

# 出欠入力
st.markdown("## ✏️ 出欠入力")
status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
attendance_data = []
alerts = []

for _, row in students_in_class.iterrows():
    student_id = row["student_id"]
    student_name = row["student_name"]

    # デフォルト値の優先順位：現在period→MHR→○
    existing_row = existing_today[existing_today["student_id"] == student_id]
    if not existing_row.empty:
        default_status = existing_row["status"].values[0]
    elif period == "EHR":
        mhr_row = mhr_today_df[mhr_today_df["student_id"] == student_id]
        default_status = mhr_row["status"].values[0] if not mhr_row.empty else "○"
    else:
        default_status = "○"

    status = st.radio(f"{student_name}（{student_id}）", status_options, horizontal=True, index=status_options.index(default_status))
    attendance_data.append({
        "student_id": student_id,
        "student_name": student_name,
        "status": status
    })
    if status != "○":
        alerts.append((student_id, student_name, status))

# 上書き確認（データが存在する場合のみ）
if not existing_today.empty:
    if not st.checkbox("⚠️ 既存データがあります。上書きしますか？"):
        st.stop()

# 出欠登録処理
if st.button("📥 出欠を一括登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    today_str = selected_date.strftime("%Y-%m-%d")
    enriched_data = []

    for row in attendance_data:
        enriched_data.append([
            today_str,            # A列: date
            now,                  # B列: timestamp
            homeroom_class,
            row["student_id"],
            row["student_name"],
            row["status"],
            teacher_name,
            period
        ])

    write_attendance_data(book, "attendance_log", enriched_data)
    st.success("✅ 出欠情報を登録しました。")

# 状況確認・対応ログ
if alerts:
    st.markdown("### ⚠️ 確認が必要な生徒")

    # 対応済みセッションステート初期化
    if "resolved_students" not in st.session_state:
        st.session_state["resolved_students"] = {}

    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    for sid, sname, stat in alerts:
        if st.session_state["resolved_students"].get(sid):
            continue  # 非表示

        col1, col2 = st.columns([3, 2])
        with col1:
            comment = st.text_input(f"{sname}（{stat}）への対応コメント", key=f"{sid}_comment")
        with col2:
            if st.button(f"✅ 対応済み: {sname}", key=f"{sid}_resolved"):
                statuslog = [[
                    today_str,
                    now,
                    homeroom_class,
                    sid,
                    sname,
                    stat,
                    teacher_name,
                    period,
                    comment
                ]]
                try:
                    write_status_log(book, "student_statuslog", statuslog)
                    st.session_state["resolved_students"][sid] = True
                    st.success(f"✅ {sname} の対応を記録しました")
                except Exception as e:
                    st.error(f"❌ スプレッドシートへの記録に失敗しました: {e}")

    # 全員対応済みのメッセージ
    unresolved = [sid for sid, _, _ in alerts if not st.session_state["resolved_students"].get(sid)]
    if not unresolved:
        st.success("🎉 すべての確認が完了しました！")
