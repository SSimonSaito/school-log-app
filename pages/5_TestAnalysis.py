import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from google_sheets_utils import connect_to_sheet, get_worksheet_df

# フォント設定
font_path = "ipaexg.ttf"  # 同じディレクトリに配置
try:
    jp_font = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = jp_font.get_name()
except Exception:
    st.error("❌ 日本語フォントファイル（ipaexg.ttf）が見つかりません。アプリと同じフォルダにあるかご確認ください。")

# UI設定
st.set_page_config(page_title="🧮 テスト分析", layout="wide")
st.title("🧮 テスト結果分析")

# スプレッドシート読み込み
book = connect_to_sheet("attendance-shared")
test_log_df = get_worksheet_df(book, "test_log")
subjects_df = get_worksheet_df(book, "subjects_master")

# データ整備
subjects_df = subjects_df.dropna(subset=["subject_code", "subject"])
subject_dict = dict(zip(subjects_df["subject"], subjects_df["subject_code"]))
subject_list = list(subject_dict.keys())

term_list = ["1学期中間", "1学期期末", "2学期中間", "2学期期末", "3学期期末"]
class_list = [f"{g}{c}" for g in range(1, 4) for c in "ABCD"]

# フィルタUI
selected_subject = st.selectbox("📘 科目を選択", subject_list)
selected_term = st.selectbox("🗓️ テスト期間を選択", term_list)
selected_classes = st.multiselect("🏫 クラスを選択（複数可）", class_list, default=class_list[:1])

# subject_code に変換してフィルタ
selected_subject_code = subject_dict[selected_subject]
filtered_df = test_log_df[
    (test_log_df["subject_code"] == selected_subject_code) &
    (test_log_df["term"] == selected_term) &
    (test_log_df["class"].isin(selected_classes))
].copy()

# スコア列を数値に
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

    # 分布グラフ
    st.subheader("📈 スコア分布（棒＋KDE）")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(filtered_df["score"], bins=10, kde=False, ax=ax, color="skyblue", edgecolor="black")

    # 上に人数ラベル
    for p in ax.patches:
        height = int(p.get_height())
        if height > 0:
            ax.text(p.get_x() + p.get_width() / 2., height + 0.5, f'{height}', ha='center', va='bottom', fontsize=9)

    # KDE（人数にスケーリング）
    kde_ax = ax.twinx()
    sns.kdeplot(
        filtered_df["score"],
        ax=kde_ax,
        color="blue",
        lw=2
    )
    kde_ax.set_ylim(0, 15)
    kde_ax.set_ylabel("密度", fontproperties=jp_font)

    # ラベル
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 20)
    ax.set_xlabel("スコア", fontproperties=jp_font)
    ax.set_ylabel("人数", fontproperties=jp_font)
    ax.set_title(f"{selected_term} の {selected_subject} 分布", fontproperties=jp_font, fontsize=16)

    st.pyplot(fig)
