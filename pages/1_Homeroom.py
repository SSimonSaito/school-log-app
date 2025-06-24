import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import pytz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import (
    connect_to_sheet,
    get_worksheet_df,
    write_attendance_data,
    write_status_log,
    get_existing_attendance,
)

st.set_page_config(page_title="Homeroom 出欠入力", layout="centered")
st.title("🏢 Homeroom 出欠入力")

try:
    # セッションチェック
    if "teacher_id" not in st.session_state or "teacher_name" not in st.session_state or "selected_date" not in st.session_state:
        st.error("❌mainページから教師と日付を選択してください。")
        st.stop()

    teacher_id = st.session_state["teacher_id"]
    teacher_name = st.session_state["teacher_name"]
    selected_date = st.session_state["selected_date"]

    st.markdown(f"👩‍🏫 教師: {teacher_name}")
    st.markdown(f"🗕️ 日付: {selected_date.strftime('%Y-%m-%d')}")

    period = "MHR"
    st.markdown("📌 本アプリでは朝のホームルーム（MHR）の出欠のみを記録します。")

    # スプレッドシート接続＆マスター取得
    book = connect_to_sheet("attendance-shared")
    students_df = get_worksheet_df(book, "students_master")
    teachers_df = get_worksheet_df(book, "teachers_master")
    existing_df = get_existing_attendance(book, "attendance_log")

    # クラス選択
    default_class = teachers_df[teachers_df["teacher_id"] == teacher_id]["homeroom_class"].values
    default_class = default_class[0] if len(default_class) > 0 else ""
    class_list = sorted(students_df["class"].dropna().unique())
    homeroom_class = st.selectbox(
        "🏢 クラスを選択してください",
        class_list,
        index=class_list.index(default_class) if default_class in class_list else 0
    )

    students_in_class = students_df[students_df["class"] == homeroom_class].copy()
    today_str = selected_date.strftime("%Y-%m-%d")

    # 該当日の既存出欠取得
    existing_today = existing_df[
        (existing_df["class"] == homeroom_class) &
        (existing_df["period"] == period) &
        (existing_df["date"] == today_str)
    ]

    # 出欠入力欄
    st.markdown("## ✏️ 出欠入力")
    status_options = ["○", "／", "公", "病", "事", "忌", "停", "遅", "早", "保"]
    attendance_data = []
    alerts = []

    for _, row in students_in_class.iterrows():
        student_id = row["student_id"]
        student_name = row["student_name"]
        existing_row = existing_today[existing_today["student_id"] == student_id]
        default_status = existing_row["status"].values[0] if not existing_row.empty else "○"

        status = st.radio(
            f"{student_name}({student_id})",
            status_options,
            horizontal=True,
            index=status_options.index(default_status)
        )

        attendance_data.append({
            "student_id": student_id,
            "student_name": student_name,
            "status": status
        })

        if status != "○":
            alerts.append((student_id, student_name, status))

    # 上書き確認
    overwrite_ok = True
    if not existing_today.empty:
        overwrite_ok = st.checkbox("⚠️既存データがあります。上書きして保存しますか？")
        if not overwrite_ok:
            st.stop()

    # 出欠登録
    if st.button("📅 出欠を一括登録"):
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
        enriched = [
            [today_str, now, homeroom_class, row["student_id"], row["student_name"], row["status"], teacher_name, period]
            for row in attendance_data
        ]

        # 既存データを除外
        new_df = existing_df[
            ~(
                (existing_df["class"] == homeroom_class) &
                (existing_df["period"] == period) &
                (existing_df["date"] == today_str)
            )
        ]

        try:
            final_df = pd.concat([new_df, pd.DataFrame(enriched, columns=existing_df.columns)], ignore_index=True)
            sheet = book.worksheet("attendance_log")
            sheet.clear()
            sheet.update([final_df.columns.values.tolist()] + final_df.values.tolist())
            st.success("✅ 出欠情報を上書き保存しました。")
        except Exception as e:
            st.error(f"❌ 保存中にエラーが発生しました: {e}")

    # 確認が必要な生徒のログ記録
    if alerts:
        st.markdown("### ⚠️ 確認が必要な生徒")
        if "resolved_students" not in st.session_state:
            st.session_state["resolved_students"] = {}
        now = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
        for sid, sname, stat in alerts:
            if st.session_state["resolved_students"].get(sid):
                continue
            col1, col2 = st.columns([3, 2])
            with col1:
                comment = st.text_input(f"{sname}({stat})への対応コメント", key=f"{sid}_comment")
            with col2:
                if st.button(f"✅ 対応済み: {sname}", key=f"{sid}_resolved"):
                    statuslog = [[
                        today_str, now, homeroom_class,
                        sid, sname, stat,
                        teacher_name, period, comment
                    ]]
                    try:
                        write_status_log(book, "student_statuslog", statuslog)
                        st.session_state["resolved_students"][sid] = True
                        st.success(f"✅ {sname} の対応を記録しました")
                    except Exception as e:
                        st.error(f"❌ 記録失敗: {e}")
        if all(st.session_state["resolved_students"].get(sid) for sid, _, _ in alerts):
            st.success("🎉 すべての確認が完了しました！")

except Exception as e:
    st.error(f"❌ エラーが発生しました: {e}")
