import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from scipy.stats import gaussian_kde
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# フォント設定
font_path = "./ipaexg.ttf"  # アプリのルートディレクトリに配置
if not os.path.exists(font_path):
    st.error("❌ 日本語フォントファイル（ipaexg.ttf）が見つかりません。 アプリと同じフォルダにあるかご確認ください。")
else:
    jp_font = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = jp_font.get_name()

# ページ設定
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# Google Sheets 読み込み
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# 科目名をsubject_code順に取得
subjects_df = subjects_df.sort_values("subject_code")
subject_dict = dict(zip(subjects_df["subject"], subjects_df["subject_code"]))
subject_names = list(subject_dict.keys())  # ソート済の表示順

term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_list = [
    "1A", "1B", "1C", "1D",
    "2A", "2B", "2C", "2D",
    "3A", "3B", "3C", "3D"
]

# UI
selected_subject_name = st.selectbox("📘 科目を選択", subject_names)
selected_subject_code = subject_dict[selected_subject_name]
selected_term = st.selectbox("🗓️ テスト期間を選択", term_list)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_list, default=class_list[:1])

# フィルタ
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject_code) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

filtered_df["score"] = pd.to_numeric(filtered_df["score"], errors="coerce")

if filtered_df.empty:
    st.warning("該当するデータが見つかりませんでした。")
else:
    # 統計情報
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

    # グラフ描画（棒＋KDE）
    st.subheader("📈 スコア分布（棒＋KDE）")

    scores = filtered_df["score"].dropna()
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # ヒストグラム（人数）
    counts, bins, patches = ax1.hist(
        scores, bins=10, range=(0, 100), color="skyblue", edgecolor="black", alpha=0.6
    )
    ax1.set_xlabel("スコア", fontproperties=jp_font)
    ax1.set_ylabel("人数", fontproperties=jp_font)
    ax1.set_ylim(0, 30)
    ax1.set_xlim(0, 100)

    # 棒に人数を表示
    for count, patch in zip(counts, patches):
        if count > 0:
            ax1.text(
                patch.get_x() + patch.get_width() / 2,
                count + 0.5,
                f"{int(count)}",
                ha="center",
                fontsize=9
            )

    # KDE（密度）
    if len(scores) > 1:
        kde = gaussian_kde(scores)
        x = np.linspace(0, 100, 500)
        kde_values = kde(x)
        # KDEを人数スケールに変換
        scale = 15 / max(kde_values)  # 最大密度 ≒ 15 人レベル
        ax2 = ax1.twinx()
        ax2.plot(x, kde_values * scale, color="blue", linewidth=2)
        ax2.set_ylabel("密度", fontproperties=jp_font)
        ax2.set_ylim(0, 20)

    ax1.set_title(f"{selected_term} の {selected_subject_name} 分布", fontproperties=jp_font, fontsize=16)
    ax1.grid(True)

    st.pyplot(fig)
