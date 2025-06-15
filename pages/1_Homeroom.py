import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))

import pandas as pd
from datetime import datetime
from google_sheets_utils import (
    connect_to_sheet, get_worksheet_df,
    write_attendance_data, write_status_log,
    get_existing_attendance,
)
import pytz

st.set_page_config(page_title="Homeroom 出欠入力", layout="centered")
st.title("🏫 Homeroom 出欠入力")

# セッションチェック
if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌mainページから教師と日付を選択してください。")
    st.stop()

teacher_id = st.session_state["teacher_id"]
teacher_name = st.session_state["teacher_name"]
selected_date = st.session_state["selected_date"]
period = st.radio("HR区分を選択してください", ["MHR","EHR"])

# 初期設定
today_str = selected_date.strftime("%Y-%m-%d")
book = connect_to_sheet("attendance-shared")
students_df = get_worksheet_df(book, "students_master")
teachers_df = get_worksheet_df(book, "teachers_master")

default_class = teachers_df.loc[teachers_df["teacher_id"] == teacher_id, "homeroom_class"].squeeze() or ""
homeroom_class = st.selectbox(
    "🏫 クラスを選択してください",
    sorted(students_df["class"].dropna().unique()),
    index=list(sorted(students_df["class"].dropna().unique())).index(default_class) if default_class else 0
)

# 出欠ログ取得
existing_df = get_existing_attendance(book, "attendance_log")
mhr_today_df = existing_df[
    (existing_df["class"] == homeroom_class) &
    (existing_df["period"] == "MHR") &
    (existing_df["date"] == today_str)
]
existing_today = existing_df[
    (existing_df["class"] == homeroom_class) &
    (existing_df["period"] == period) &
    (existing_df["date"] == today_str)
]

# 前時限取得（6→…→1限、なければ空 DataFrame、MHRは別途参照）
prior_period_df = pd.DataFrame()
if period == "EHR":
    for i in range(6, 0, -1):
        tmp = existing_df[
            (existing_df["class"] == homeroom_class) &
            (existing_df["period"] == f"{i}限") &
            (existing_df["date"] == today_str)
        ]
        if not tmp.empty:
            prior_period_df = tmp
            break

# 入力UI
st.markdown("## ✏️ 出欠入力")
status_options = ["○","／","公","病","事","忌","停","遅","早","保"]
attendance_data = []
alerts = []

for _, stu in students_df[students_df["class"]==homeroom_class].iterrows():
    sid = stu["student_id"]
    sname = stu["student_name"]

    # デフォルト取得
    existing_row = existing_today[existing_today["student_id"] == sid]
    if not existing_row.empty:
        default_status = existing_row["status"].iloc[0]
    elif period == "EHR":
        prior_row = prior_period_df[prior_period_df["student_id"] == sid]
        if not prior_row.empty:
            default_status = prior_row["status"].iloc[0]
        else:
            default_status = mhr_today_df[mhr_today_df["student_id"] == sid]["status"].iloc[0] if sid in mhr_today_df["student_id"].values else "○"
    else:
        default_status = "○"

    # 差異チェック
    mhr_status = mhr_today_df[mhr_today_df["student_id"] == sid]["status"].iloc[0] if sid in mhr_today_df["student_id"].values else None
    prev_status = None
    if period=="EHR":
        if sid in prior_period_df["student_id"].values:
            prev_status = prior_period_df[prior_period_df["student_id"]==sid]["status"].iloc[0]
        else:
            prev_status = mhr_status

    if period=="EHR" and prev_status and mhr_status and prev_status != mhr_status:
        st.markdown(f"""
            <div style="
                background-color:#ffe6e6;
                padding:10px;
                border:2px solid red;
                border-radius:5px;
                margin-bottom:10px;">
                <span style="color:red;font-weight:bold;">
                    {sid}：{sname}<br>
                    前時限: {prev_status} ｜ MHR: {mhr_status}（差異あり）
                </span>
            </div>""", unsafe_allow_html=True)

    status = st.radio(f"{sid}：{sname}", status_options,
                      horizontal=True,
                      index=status_options.index(default_status))
    attendance_data.append({"student_id":sid,"student_name":sname,"status":status})
    if status!="○":
        alerts.append((sid,sname,status))

# 上書きチェック
if not existing_today.empty and not st.checkbox("⚠️ 既存データがあります。上書きしますか？"):
    st.stop()

# 登録ボタン
if st.button("📥 出欠を一括登録"):
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    enriched = [
        [today_str, now, homeroom_class, r["student_id"], r["student_name"], r["status"], teacher_name, period]
        for r in attendance_data
    ]
    write_attendance_data(book, "attendance_log", enriched)
    st.success("✅ 出欠情報を登録しました。")

# 確認必要者ログ機能
if alerts:
    st.markdown("### ⚠️ 確認が必要な生徒")
    if "resolved_students" not in st.session_state:
        st.session_state["resolved_students"] = {}
    jst = pytz.timezone("Asia/Tokyo"); now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    for sid,sname,stat in alerts:
        if st.session_state["resolved_students"].get(sid): continue
        col1,col2 = st.columns([3,2])
        with col1:
            comment = st.text_input(f"{sname}（{stat}）への対応コメント", key=f"{sid}_comment")
        with col2:
            if st.button(f"✅ 対応済み: {sname}", key=f"{sid}_resolved"):
                write_status_log(book, "student_statuslog", [[today_str,now,homeroom_class,sid,sname,stat,teacher_name,period,comment]])
                st.session_state["resolved_students"][sid] = True
                st.success(f"✅ {sname} の対応を記録しました")

    if all(st.session_state["resolved_students"].get(sid) for sid,_,_ in alerts):
        st.success("🎉 すべての確認が完了しました！")
