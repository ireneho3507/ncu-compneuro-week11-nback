"""
Week 11 — N-back Working Memory Dashboard
NS5116 電腦硬體與程式語言（Spring 2026）
Author: Irene Ho
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ---------- Page config ----------
st.set_page_config(
    page_title="N-back Working Memory Dashboard",
    page_icon="🧠",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "nback_working_memory.csv"


# ---------- 1. Data loading with error handling (10 pts) ----------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"❌ 找不到資料檔：{DATA_PATH}")
    st.stop()
except Exception as e:
    st.error(f"❌ 讀取資料時發生錯誤：{e}")
    st.stop()


# ---------- Header ----------
st.title("🧠 N-back Working Memory Dashboard")
st.caption(
    "200 participants × 3 conditions (1/2/3-back) — interactive exploration of "
    "age, sex, and cognitive load effects on working memory performance."
)


# ---------- 2. Sidebar widgets (15 pts) ----------
st.sidebar.header("🔎 Filters")

age_min, age_max = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider(
    "Age range",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max),
    step=1,
)

sex_options = sorted(df["sex"].unique().tolist())
sex_selected = st.sidebar.multiselect(
    "Sex",
    options=sex_options,
    default=sex_options,
)

condition_options = ["1-back", "2-back", "3-back"]
condition_selected = st.sidebar.multiselect(
    "Condition (N-back load)",
    options=condition_options,
    default=condition_options,
)

group_options = ["young", "middle", "older"]
group_selected = st.sidebar.multiselect(
    "Age group",
    options=group_options,
    default=group_options,
)

metric_choice = st.sidebar.selectbox(
    "Performance metric for chart",
    options=["accuracy", "mean_rt_ms", "d_prime"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.caption("Made with Streamlit · Irene Ho · NS5116")


# ---------- Apply filters ----------
mask = (
    df["age"].between(age_range[0], age_range[1])
    & df["sex"].isin(sex_selected)
    & df["condition"].isin(condition_selected)
    & df["group"].isin(group_selected)
)
filtered = df.loc[mask].copy()


# ---------- Status messages (+5 bonus) ----------
if filtered.empty:
    st.warning("⚠️ 目前篩選條件下沒有資料。請放寬條件。")
    st.stop()
elif len(filtered) < 30:
    st.info(f"ℹ️ 篩選後資料較少（{len(filtered)} 列），統計結果可能不穩定。")
else:
    st.success(f"✅ 已套用篩選：{len(filtered)} 列資料 / {filtered['participant_id'].nunique()} 位受試者")


# ---------- Tabs (+5 bonus: multi-page interface) ----------
tab_overview, tab_chart, tab_data = st.tabs(["📊 Overview", "📈 Visualization", "📥 Data"])


# ---------- 3. Metrics (10 pts) ----------
with tab_overview:
    st.subheader("Summary statistics")
    n_participants = filtered["participant_id"].nunique()
    mean_acc = filtered["accuracy"].mean()
    mean_rt = filtered["mean_rt_ms"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Participants", f"{n_participants}")
    c2.metric("Mean accuracy", f"{mean_acc:.2f}")
    c3.metric("Mean RT (ms)", f"{int(round(mean_rt))}")

    st.markdown("#### Performance by condition")
    by_cond = (
        filtered.groupby("condition", observed=True)[["accuracy", "mean_rt_ms", "d_prime"]]
        .mean()
        .round(3)
        .reindex(condition_options)
        .dropna(how="all")
    )
    st.dataframe(by_cond, use_container_width=True)

    st.markdown("#### Performance by age group")
    by_group = (
        filtered.groupby("group", observed=True)[["accuracy", "mean_rt_ms", "d_prime"]]
        .mean()
        .round(3)
        .reindex(group_options)
        .dropna(how="all")
    )
    st.dataframe(by_group, use_container_width=True)


# ---------- 4. Visualization (15 pts) ----------
with tab_chart:
    st.subheader(f"Age × {metric_choice} across conditions")

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"1-back": "#4C78A8", "2-back": "#F58518", "3-back": "#E45756"}

    for cond in condition_selected:
        sub = filtered[filtered["condition"] == cond]
        if sub.empty:
            continue
        ax.scatter(
            sub["age"],
            sub[metric_choice],
            alpha=0.55,
            s=35,
            color=colors.get(cond, "gray"),
            label=cond,
            edgecolor="white",
            linewidth=0.5,
        )
        if len(sub) >= 2:
            coef = np.polyfit(sub["age"], sub[metric_choice], 1)
            xs = np.linspace(sub["age"].min(), sub["age"].max(), 50)
            ax.plot(xs, np.polyval(coef, xs), color=colors.get(cond, "gray"), linewidth=2)

    y_labels = {
        "accuracy": "Accuracy (proportion correct)",
        "mean_rt_ms": "Mean reaction time (ms)",
        "d_prime": "d′ (sensitivity)",
    }
    ax.set_xlabel("Age (years)", fontsize=11)
    ax.set_ylabel(y_labels[metric_choice], fontsize=11)
    ax.set_title(f"{y_labels[metric_choice]} vs. age, by N-back condition", fontsize=12)
    ax.legend(title="Condition", loc="best", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)

    st.caption(
        "Points = individual participants. Lines = linear fit per condition. "
        "Expected: accuracy/d′ decline with age, especially under higher load; RT increases with age and load."
    )


# ---------- 5. Data export (10 pts) ----------
with tab_data:
    st.subheader("Filtered dataset")
    st.dataframe(filtered, use_container_width=True, height=400)

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download filtered CSV",
        data=csv_bytes,
        file_name="nback_filtered.csv",
        mime="text/csv",
    )

    with st.expander("ℹ️ Variable dictionary"):
        st.markdown(
            """
            - **participant_id** — anonymized ID
            - **age** — 18–75 years
            - **sex** — F / M
            - **education** — years of schooling
            - **group** — young / middle / older
            - **condition** — 1-back / 2-back / 3-back
            - **n_trials** — trials per block
            - **accuracy** — proportion correct (0–1)
            - **mean_rt_ms** — mean reaction time, ms
            - **d_prime** — signal-detection sensitivity (d′)
            """
        )
