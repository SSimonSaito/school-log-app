import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from google_sheets_utils import (
    connect_to_sheet,
    get_existing_attendance,
    write_attendance_data,
    write_status_log,
    get_students_by_class
)

st.set_page_config(page_title="Homeroom 出欠入力", page_icon="🏫")
st.title("🏫 Homeroom 出欠入力")

# セッションから教師情報と日付を取得
if "selected_teacher" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌ mainページから教師と日付を選択してください。")
    st.stop()

teacher_name = st.session_state["selected_teacher"]
target_date = st.session_state["selected_date"].strftime("%Y-%m-%d")

st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {target_date}")

# HR時間帯選択
period = st.radio("時間帯を選択してください", ["MHR", "EHR"], horizontal=True)

# attendance_logシートに接続
book = connect_to_sheet("attendance_log")
existing_df = get_existing_attendance(book)

# teachers_masterの担任情報取得
tm_sheet = connect_to_sheet("teachers_master")
tm_df = pd.DataFrame(tm_sheet.get_all_records())
teacher_row = tm_df[tm_df["teacher"] == teacher_name]
default_class = teacher_row["homeroom_class"].values[0] if not teacher_row.empty else ""

# クラス選択（編集可）
class_list = sorted(tm_df["homeroom_class"].dropna().unique())
selected_class = st.selectbox("クラスを選択してください", options=class_list, index=class_list.index(default_class))

# 生徒データ取得
students = get_students_by_class(selected_class)
if students.empty:
    st.warning("このクラスには生徒が登録されていません。")
    st.stop()

# 既存データの有無確認
existing_rows = existing_df[
    (existing_df["date"] == target_date) &
    (existing_df["class"] == selected_class) &
    (existing_df["period"] == period)
]

# 出欠区分と初期値設定
def_status_map = {}
for _, row in students.iterrows():
    sid = row["student_id"]
    match = existing_rows[existing_rows["student_id"] == sid]
    def_status_map[sid] = match["status"].values[0] if not match.empty else "○"

# 入力フォーム
data = []
st.subheader("出欠入力")
alert_flag = False
for _, row in students.iterrows():
    sid = row["student_id"]
    sname = row["student_name"]
    status = st.radio(f"{sname} ({sid})", ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"],
                      horizontal=True, key=sid, index=["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"].index(def_status_map[sid]))
    data.append({
        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "date": target_date,
        "class": selected_class,
        "student_id": sid,
        "student_name": sname,
        "status": status,
        "entered_by": teacher_name,
        "period": period
    })
    if status != "○":
        alert_flag = True

# 登録処理
if st.button("🗂 出欠を一括登録"):
    if not existing_rows.empty:
        if not st.confirm("⚠️ 既に入力済みのデータがあります。上書きしますか？"):
            st.stop()

    write_attendance_data(book, data)
    st.success("✅ 出欠データを登録しました。")

    if alert_flag:
        st.subheader("⚠️ 状況確認が必要な生徒")
        status_sheet = connect_to_sheet("student_statuslog")
        for row in data:
            if row["status"] != "○":
                comment = st.text_input(f"{row['student_name']} ({row['status']}) のコメント", key=f"cmt_{row['student_id']}")
                checked = st.checkbox("確認済み", key=f"chk_{row['student_id']}")
                if checked:
                    log_row = {
                        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                        "class": row["class"],
                        "student_id": row["student_id"],
                        "student_name": row["student_name"],
                        "status": row["status"],
                        "entered_by": row["entered_by"],
                        "period": row["period"],
                        "comment": comment
                    }
                    write_status_log(status_sheet, log_row)
                    st.success(f"{row['student_name']} の確認ログを保存しました。")
