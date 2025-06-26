import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from google_sheets_utils import connect_to_sheet, get_worksheet_df
from scipy.stats import gaussian_kde

# 📁 フォント読み込み
font_path = "./ipaexg.ttf"
try:
    jp_font = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = jp_font.get_name()
except Exception:
    st.error("❌ 日本語フォントファイル（ipaexg.ttf）が見つかりません。アプリと同じフォルダにあるかご確認ください。")

# Streamlitページ設定
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# 📊 データ取得
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subject_master_df = get_worksheet_df(book, "subjects_master")

# 📌 フィルター用リスト作成
term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_list = [f"{g}{c}" for g in range(1, 4) for c in "ABCD"]
subject_dict = dict(zip(subject_master_df["subject_code"], subject_master_df["subject"]))

# 🎛️ フィルタUI
selected_subject_code = st.selectbox("📘 科目を選択", list(subject_dict.keys()), format_func=lambda x: subject_dict[x])
selected_term = st.selectbox("🗓️ テスト期間を選択", term_list)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_list, default=class_list[:1])

# 🎯 データ抽出
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject_code) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

# 📈 表示処理
if filtered_df.empty:
    st.warning("該当するデータが見つかりませんでした。")
else:
    # 基本統計情報
    stats = {
        "📈 平均": round(filtered_df["score"].mean(), 2),
        "👿 最低点": int(filtered_df["score"].min()),
        "🏆 最高点": int(filtered_df["score"].max()),
        "⚖️ 中央値": round(filtered_df["score"].median(), 2),
        "📏 標準偏差": round(filtered_df["score"].std(), 2)
    }

    st.subheader("📊 統計情報")
    stat_cols = st.columns(len(stats))
    for col, (label, value) in zip(stat_cols, stats.items()):
        col.metric(label, value)

    # グラフ表示
    st.subheader("📈 スコア分布（棒＋KDE）")
    scores = filtered_df["score"].dropna()

    # KDE計算
    kde = gaussian_kde(scores)
    xs = np.linspace(0, 100, 200)
    kde_vals = kde(xs)
    max_density = max(kde_vals) * 1.2  # 右軸の最大値（余裕持たせる）

    # グラフ描画
    fig, ax = plt.subplots(figsize=(10, 6))

    # 棒グラフ
    bins = np.linspace(0, 100, 11)
    hist_data = sns.histplot(scores, bins=bins, kde=False, ax=ax, color="skyblue", edgecolor="black")

    # 人数ラベル表示
    for p in hist_data.patches:
        height = int(p.get_height())
        if height > 0:
            ax.text(p.get_x() + p.get_width() / 2., height + 0.3, f'{height}', ha='center', va='bottom', fontsize=9)

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.set_xlabel("スコア", fontproperties=jp_font)
    ax.set_ylabel("人数", fontproperties=jp_font)

    # KDEを右軸に重ねる
    kde_ax = ax.twinx()
    kde_ax.plot(xs, kde_vals, color="blue", lw=2)
    kde_ax.set_ylim(0, max_density)
    kde_ax.set_ylabel("密度", fontproperties=jp_font)

    # タイトル
    subject_name = subject_dict[selected_subject_code]
    ax.set_title(f"{selected_term} の {subject_name} 分布", fontproperties=jp_font, fontsize=16)

    st.pyplot(fig)
