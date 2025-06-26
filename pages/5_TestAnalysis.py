import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

from google_sheets_utils import connect_to_sheet, get_worksheet_df

st.set_page_config(page_title="テスト分析", layout="wide")
st.title("📊 テスト分析")

# Google Sheets からデータ取得
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# データが正しく読み込まれていなければエラー
if test_log_df.empty or subjects_df.empty:
    st.error("❌ データが読み込めませんでした。スプレッドシートをご確認ください。")
    st.stop()

# プルダウン・チェックボックスでフィルタ選択
subject_options = subjects_df["subject"].tolist()
term_options = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_options = ["1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "3D"]

selected_subject = st.selectbox("📘 科目を選択", subject_options)
selected_term = st.selectbox("🗓️ 学期・テストを選択", term_options)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_options, default=["1A"])

# subject_code に変換
subject_row = subjects_df[subjects_df["subject"] == selected_subject]
if subject_row.empty:
    st.error("❌ 該当する科目が見つかりません。")
    st.stop()

subject_code = subject_row["subject_code"].values[0]

# データ抽出
filtered_df = test_log_df[
    (test_log_df["subject_code"] == subject_code) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

if filtered_df.empty:
    st.warning("⚠️ 該当条件のデータが存在しません。")
    st.stop()

# スコア列を数値化
filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

# 統計情報
max_score = filtered_df["score"].max()
min_score = filtered_df["score"].min()
avg_score = filtered_df["score"].mean()
median_score = filtered_df["score"].median()
std_dev = filtered_df["score"].std()

st.subheader("🧮 統計情報")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("最高点", f"{max_score:.1f}")
col2.metric("最低点", f"{min_score:.1f}")
col3.metric("平均点", f"{avg_score:.1f}")
col4.metric("中央値", f"{median_score:.1f}")
col5.metric("標準偏差", f"{std_dev:.1f}")

# 📊 分布図（ヒストグラム）
st.subheader("📊 スコアの分布図")

# 日本語フォント設定（IPAexGothicなど）
try:
    plt.rcParams["font.family"] = "IPAexGothic"
except:
    pass  # 日本語フォントがインストールされていない場合はデフォルトのまま

fig, ax = plt.subplots()
ax.hist(filtered_df["score"].dropna(), bins=10, edgecolor="black", alpha=0.7)
ax.set_title(f"{selected_term} の {selected_subject} テスト分布")
ax.set_xlabel("スコア")
ax.set_ylabel("人数")
st.pyplot(fig)
