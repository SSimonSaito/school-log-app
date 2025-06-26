import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os

# モジュールのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules')))
from google_sheets_utils import connect_to_sheet, get_worksheet_df

st.set_page_config(page_title="テスト結果分析", layout="wide")
st.title("📊 テスト結果分析")

try:
    # Google Sheets 接続
    book = connect_to_sheet("attendance-shared")
    test_log_df = get_worksheet_df(book, "test_log")
    subjects_df = get_worksheet_df(book, "subjects_master")

    # 必要な列のみ使用
    required_cols = ["subject_code", "term", "class", "student_name", "score"]
    test_log_df = test_log_df[required_cols]
    test_log_df["score"] = pd.to_numeric(test_log_df["score"], errors="coerce")
    test_log_df = test_log_df.dropna(subset=["score"])

    # プルダウン選択肢の準備
    subject_options = subjects_df["subject"].tolist()
    selected_subject = st.selectbox("📚 科目を選択", subject_options)

    term_options = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
    selected_term = st.selectbox("🕒 学期を選択", term_options)

    class_options = sorted(test_log_df["class"].dropna().unique())
    selected_classes = st.multiselect("🏫 クラスを選択", class_options, default=class_options)

    # subject_codeの取得
    selected_subject_code = subjects_df[subjects_df["subject"] == selected_subject]["subject_code"].values[0]

    # データフィルター
    filtered_df = test_log_df[
        (test_log_df["subject_code"] == selected_subject_code) &
        (test_log_df["term"] == selected_term) &
        (test_log_df["class"].isin(selected_classes))
    ]

    if filtered_df.empty:
        st.warning("⚠️ 該当するテストデータがありません。")
        st.stop()

    # 分析値の計算
    max_score = filtered_df["score"].max()
    min_score = filtered_df["score"].min()
    mean_score = filtered_df["score"].mean()
    median_score = filtered_df["score"].median()
    std_score = filtered_df["score"].std()

    st.markdown("### 📈 テスト統計")
    col1, col2, col3 = st.columns(3)
    col1.metric("最高点", f"{max_score:.1f}")
    col1.metric("最低点", f"{min_score:.1f}")
    col2.metric("平均点", f"{mean_score:.1f}")
    col2.metric("中央値", f"{median_score:.1f}")
    col3.metric("標準偏差", f"{std_score:.2f}")

    # 散布図表示
    st.markdown("### 🎯 テスト結果の散布図")
    fig, ax = plt.subplots()
    ax.scatter(range(len(filtered_df)), filtered_df["score"])
    ax.set_xlabel("生徒インデックス")
    ax.set_ylabel("スコア")
    ax.set_title(f"{selected_subject} - {selected_term}")
    st.pyplot(fig)

except Exception as e:
    st.error(f"❌ エラーが発生しました: {e}")
