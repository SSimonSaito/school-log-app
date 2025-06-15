import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from google_sheets_utils import (
    connect_to_sheet,
    get_existing_attendance,
    write_attendance_data,
    write_status_log
)

st.set_page_config(page_title="Homeroom 出欠入力", layout="wide")

# セッションステートから値を取得
if "selected_teacher" not in st.session_state or "selected_date" not in st.session_state:
    st.error("❌ mainページから教師と日付を選択してください。")
    st.stop()

teacher_name = st.session_state["selected_teacher"]
selected_date = st.session_state["selected_date"]

st.title("🏫 Homeroom 出欠入力")
st.markdown(f"👩‍🏫 教師: {teacher_name}")
st.markdown(f"📅 日付: {selected_date}")

# スプレッドシートに接続
book = connect_to_sheet()

# teacher_master取得し、該当教師の担任クラスを取得
teacher_df = pd.DataFrame(book.worksheet("teachers_master").get_all_records())
teacher_row = teacher_df[teacher_df["teacher"] == teacher_name]
homeroom_class = teacher_row["homeroom_class"].values[0] if not teacher_row.empty else ""

# クラス編集可能
class_name = st.text_input("🏘️ クラスを確認・編集してください", value=homeroom_class)

# 朝・夕のHRを選択
period = st.radio("⏰ 実施時間を選択してください", ["MHR", "EHR"])

# 出欠ログと学生マスタを取得
attendance_sheet = book.worksheet("attendance_log")
df_existing = get_existing_attendance(attendance_sheet)
students_df = pd.DataFrame(book.worksheet("students_master").get_all_records())
students_in_class = students_df[students_df["class"] == class_name]

# デフォルト設定
statuses = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
default_status = {}
for _, row in students_in_class.iterrows():
    match = df_existing[
        (df_existing["date"] == selected_date)
        & (df_existing["class"] == class_name)
        & (df_existing["period"] == period)
        & (df_existing["student_id"] == row["student_id"])
    ]
    default_status[row["student_id"]] = match["status"].values[0] if not match.empty else "○"

# 出欠入力UI
st.subheader("📋 出欠入力")
input_data = []
for _, row in students_in_class.iterrows():
    status = st.radio(
        f"{row['student_name']}（{row['student_id']}）",
        statuses,
        index=statuses.index(default_status[row["student_id"]]),
        horizontal=True,
        key=row["student_id"]
    )
    input_data.append({
        "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S"),
        "date": selected_date,
        "class": class_name,
        "student_id": row["student_id"],
        "student_name": row["student_name"],
        "status": status,
        "entered_by": teacher_name,
        "period": period
    })

# 登録前チェック
alert_students = [d for d in input_data if d["status"] != "○"]

if alert_students:
    st.warning("⚠️ 以下の生徒が「○」以外で入力されています。")
    for s in alert_students:
        st.write(f"{s['student_name']}: {s['status']}")

if st.button("📥 出欠を一括登録"):
    if not df_existing[
        (df_existing["date"] == selected_date)
        & (df_existing["class"] == class_name)
        & (df_existing["period"] == period)
    ].empty:
        if not st.confirm("⚠️ 既に入力済みのデータがあります。上書きしますか？"):
            st.stop()
    write_attendance_data(attendance_sheet, input_data)
    st.success("✅ 出欠を登録しました。")

    if alert_students:
        st.subheader("🧑‍🏫 状況確認が必要な生徒")
        for s in alert_students:
            col1, col2 = st.columns([2, 3])
            with col1:
                checked = st.checkbox(f"{s['student_name']} の確認完了", key="chk_" + s["student_id"])
            with col2:
                comment = st.text_input("コメントを記入", key="cmt_" + s["student_id"])
            if checked:
                write_status_log(
                    book,
                    class_name=s["class"],
                    student_name=s["student_name"],
                    status=s["status"],
                    teacher=teacher_name,
                    comment=comment
                )
                st.success(f"✅ {s['student_name']} の状況を記録しました。")
