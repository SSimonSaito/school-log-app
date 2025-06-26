import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google_sheets_utils import connect_to_sheet, get_worksheet_df

st.set_page_config(page_title="📊 テスト分析", layout="wide")
st.title("📊 テスト結果の分析")

try:
    # スプレッドシート接続
    book = connect_to_sheet("attendance-shared")
    test_log_df = get_worksheet_df(book, "test_log")

    if test_log_df.empty:
        st.warning("テストデータが存在しません。")
        st.stop()

    # 科目一覧の取得
    subjects_df = get_worksheet_df(book, "subjects_master")
    subject_dict = dict(zip(subjects_df["subject_code"], subjects_df["subject"]))
    subject_options = list(subject_dict.values())

    # ユーザー入力
    selected_subject = st.selectbox("科目を選択", subject_options)
    selected_term = st.selectbox("学期・試験を選択", ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"])
    all_classes = sorted(test_log_df["class"].dropna().unique())
    selected_classes = st.multiselect("クラスを選択", all_classes, default=all_classes)

    # フィルタリング
    subject_code = [code for code, name in subject_dict.items() if name == selected_subject][0]
    filtered_df = test_log_df[
        (test_log_df["subject_code"] == subject_code) &
        (test_log_df["term"] == selected_term) &
        (test_log_df["class"].isin(selected_classes))
    ].copy()

    if filtered_df.empty:
        st.warning("該当するテスト結果が見つかりません。")
        st.stop()

    # 数値変換
    filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")
    filtered_df.dropna(subset=["score"], inplace=True)

    # 統計情報
    max_score = filtered_df["score"].max()
    min_score = filtered_df["score"].min()
    mean_score = filtered_df["score"].mean()
    median_score = filtered_df["score"].median()
    std_dev = filtered_df["score"].std()

    st.subheader("📈 スコア分布（散布図）")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.stripplot(data=filtered_df, x="student_name", y="score", hue="class", dodge=True, ax=ax)
    ax.set_xlabel("生徒名")
    ax.set_ylabel("スコア")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    st.pyplot(fig)

    st.subheader("📊 統計情報")
    stats_df = pd.DataFrame({
        "項目": ["最高点", "最低点", "平均点", "中央値", "標準偏差"],
        "値": [max_score, min_score, round(mean_score, 2), median_score, round(std_dev, 2)]
    })
    st.dataframe(stats_df, use_container_width=True)

except Exception as e:
    st.error(f"❌ エラーが発生しました: {e}")
