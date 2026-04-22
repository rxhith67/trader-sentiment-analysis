from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
REGIME_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
MIN_ACCOUNT_TRADES = 250
TOP_ACCOUNTS = 12


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    trades = pd.read_csv(BASE_DIR / "historical_data.csv")
    sentiment = pd.read_csv(BASE_DIR / "fear_greed_index.csv")

    trades["Timestamp IST"] = pd.to_datetime(
        trades["Timestamp IST"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    trades["date"] = trades["Timestamp IST"].dt.normalize()

    sentiment["date"] = pd.to_datetime(sentiment["date"], errors="coerce")
    sentiment["classification"] = pd.Categorical(
        sentiment["classification"], categories=REGIME_ORDER, ordered=True
    )

    numeric_columns = [
        "Execution Price",
        "Size Tokens",
        "Size USD",
        "Start Position",
        "Closed PnL",
        "Fee",
        "Timestamp",
    ]
    for column in numeric_columns:
        trades[column] = pd.to_numeric(trades[column], errors="coerce")

    return trades, sentiment


def prepare_dataset(trades: pd.DataFrame, sentiment: pd.DataFrame) -> pd.DataFrame:
    merged = trades.merge(
        sentiment[["date", "classification", "value"]],
        on="date",
        how="left",
    ).copy()

    merged = merged[merged["Timestamp IST"].notna()].copy()
    merged["net_pnl"] = merged["Closed PnL"] - merged["Fee"]
    merged["is_profitable"] = (merged["net_pnl"] > 0).astype(int)
    merged["has_realized_pnl"] = (merged["Closed PnL"] != 0).astype(int)
    merged["abs_net_pnl"] = merged["net_pnl"].abs()
    merged["size_usd_safe"] = merged["Size USD"].where(merged["Size USD"] != 0)
    merged["net_roi_proxy"] = merged["net_pnl"] / merged["size_usd_safe"]
    merged["classification"] = pd.Categorical(
        merged["classification"], categories=REGIME_ORDER, ordered=True
    )
    merged["regime"] = merged["classification"].astype("object").fillna("Unknown")

    return merged


def build_regime_summary(merged: pd.DataFrame) -> pd.DataFrame:
    valid = merged[merged["classification"].notna()].copy()
    total_volume = valid.groupby("classification", observed=False)["Size USD"].sum()

    summary = (
        valid.groupby("classification", observed=False)
        .agg(
            trades=("Account", "size"),
            active_days=("date", "nunique"),
            active_accounts=("Account", "nunique"),
            traded_coins=("Coin", "nunique"),
            total_volume_usd=("Size USD", "sum"),
            total_closed_pnl=("Closed PnL", "sum"),
            total_fees=("Fee", "sum"),
            total_net_pnl=("net_pnl", "sum"),
            avg_net_pnl_per_trade=("net_pnl", "mean"),
            median_net_pnl_per_trade=("net_pnl", "median"),
            positive_trade_rate=("is_profitable", "mean"),
            realized_trade_share=("has_realized_pnl", "mean"),
            mean_roi_proxy=("net_roi_proxy", "mean"),
            median_roi_proxy=("net_roi_proxy", "median"),
        )
        .reset_index()
    )

    summary["net_pnl_to_volume"] = summary["total_net_pnl"] / total_volume.values
    summary["net_pnl_per_million_volume"] = summary["net_pnl_to_volume"] * 1_000_000
    summary["positive_trade_rate"] = summary["positive_trade_rate"] * 100
    summary["realized_trade_share"] = summary["realized_trade_share"] * 100

    return summary


def build_daily_summary(merged: pd.DataFrame) -> pd.DataFrame:
    valid = merged[merged["classification"].notna()].copy()
    daily = (
        valid.groupby(["date", "classification"], observed=True)
        .agg(
            daily_net_pnl=("net_pnl", "sum"),
            daily_volume_usd=("Size USD", "sum"),
            daily_trades=("Account", "size"),
            daily_accounts=("Account", "nunique"),
        )
        .reset_index()
    )

    return daily


def build_account_summary(merged: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = merged[merged["classification"].notna()].copy()
    account_regime = (
        valid.groupby(["Account", "classification"], observed=True)
        .agg(
            trades=("Account", "size"),
            total_net_pnl=("net_pnl", "sum"),
            avg_net_pnl=("net_pnl", "mean"),
            avg_size_usd=("Size USD", "mean"),
            positive_trade_rate=("is_profitable", "mean"),
        )
        .reset_index()
    )
    account_regime["positive_trade_rate"] *= 100

    eligible_accounts = (
        account_regime.groupby("Account", observed=False)["trades"].sum().loc[lambda s: s >= MIN_ACCOUNT_TRADES]
    )
    filtered = account_regime[account_regime["Account"].isin(eligible_accounts.index)].copy()

    pivot = filtered.pivot(index="Account", columns="classification", values="total_net_pnl").fillna(0)
    best_regime = pivot.idxmax(axis=1)
    worst_regime = pivot.idxmin(axis=1)
    specialization = pivot.max(axis=1) - pivot.min(axis=1)

    account_summary = (
        filtered.groupby("Account", observed=True)
        .agg(
            total_trades=("trades", "sum"),
            total_net_pnl=("total_net_pnl", "sum"),
            avg_trade_net_pnl=("avg_net_pnl", "mean"),
        )
        .reset_index()
    )
    account_summary["best_regime"] = account_summary["Account"].map(best_regime)
    account_summary["worst_regime"] = account_summary["Account"].map(worst_regime)
    account_summary["specialization_gap"] = account_summary["Account"].map(specialization)

    return filtered, account_summary.sort_values("total_net_pnl", ascending=False)


def build_coin_summary(merged: pd.DataFrame) -> pd.DataFrame:
    valid = merged[merged["classification"].notna()].copy()
    coin_regime = (
        valid.groupby(["Coin", "classification"], observed=True)
        .agg(
            trades=("Coin", "size"),
            total_net_pnl=("net_pnl", "sum"),
            total_volume_usd=("Size USD", "sum"),
        )
        .reset_index()
    )
    return coin_regime


def save_tables(
    merged: pd.DataFrame,
    regime_summary: pd.DataFrame,
    daily_summary: pd.DataFrame,
    account_regime: pd.DataFrame,
    account_summary: pd.DataFrame,
    coin_summary: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    regime_summary.to_csv(OUTPUT_DIR / "regime_summary.csv", index=False)
    daily_summary.to_csv(OUTPUT_DIR / "daily_regime_summary.csv", index=False)
    account_regime.to_csv(OUTPUT_DIR / "account_regime_summary.csv", index=False)
    account_summary.to_csv(OUTPUT_DIR / "account_overview.csv", index=False)

    top_coin_rows = (
        coin_summary.sort_values(["classification", "total_net_pnl"], ascending=[True, False])
        .groupby("classification", observed=False)
        .head(8)
    )
    top_coin_rows.to_csv(OUTPUT_DIR / "top_coins_by_regime.csv", index=False)

    missing_sentiment = merged[merged["classification"].isna()].copy()
    if not missing_sentiment.empty:
        missing_sentiment.to_csv(OUTPUT_DIR / "unmatched_trades.csv", index=False)


def plot_regime_net_pnl(regime_summary: pd.DataFrame) -> None:
    chart = regime_summary.copy()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.barplot(
        data=chart,
        x="classification",
        y="total_net_pnl",
        hue="classification",
        order=REGIME_ORDER,
        palette="RdYlGn",
        legend=False,
        ax=axes[0],
    )
    axes[0].set_title("Total Net PnL by Sentiment Regime")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Net PnL")
    axes[0].tick_params(axis="x", rotation=20)

    sns.barplot(
        data=chart,
        x="classification",
        y="avg_net_pnl_per_trade",
        hue="classification",
        order=REGIME_ORDER,
        palette="RdYlGn",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("Average Net PnL per Trade")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Net PnL per trade")
    axes[1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "regime_pnl_overview.png", dpi=220)
    plt.close(fig)


def plot_daily_distribution(daily_summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.boxplot(
        data=daily_summary,
        x="classification",
        y="daily_net_pnl",
        hue="classification",
        order=REGIME_ORDER,
        palette="RdYlGn",
        ax=axes[0],
        showfliers=False,
        legend=False,
    )
    axes[0].set_title("Daily Net PnL Distribution")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Daily net PnL")
    axes[0].tick_params(axis="x", rotation=20)

    sns.barplot(
        data=daily_summary.groupby("classification", observed=True, as_index=False).agg(
            profitable_day_rate=("daily_net_pnl", lambda s: (s > 0).mean() * 100),
            avg_daily_trades=("daily_trades", "mean"),
        ),
        x="classification",
        y="profitable_day_rate",
        hue="classification",
        order=REGIME_ORDER,
        palette="RdYlGn",
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("Share of Profitable Days")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Profitable days (%)")
    axes[1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "daily_regime_behavior.png", dpi=220)
    plt.close(fig)


def plot_account_heatmap(account_regime: pd.DataFrame, account_summary: pd.DataFrame) -> None:
    top_accounts = account_summary.head(TOP_ACCOUNTS)["Account"]
    heatmap_data = (
        account_regime[account_regime["Account"].isin(top_accounts)]
        .pivot(index="Account", columns="classification", values="total_net_pnl")
        .reindex(columns=REGIME_ORDER)
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(
        heatmap_data,
        cmap="RdYlGn",
        center=0,
        linewidths=0.5,
        annot=True,
        fmt=".0f",
        cbar_kws={"label": "Net PnL"},
        ax=ax,
    )
    ax.set_title("Top Accounts: Net PnL by Sentiment Regime")
    ax.set_xlabel("")
    ax.set_ylabel("Account")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "account_regime_heatmap.png", dpi=220)
    plt.close(fig)


def plot_volume_vs_profit(regime_summary: pd.DataFrame) -> None:
    chart = regime_summary.copy()
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(
        data=chart,
        x="total_volume_usd",
        y="total_net_pnl",
        hue="classification",
        hue_order=REGIME_ORDER,
        palette="RdYlGn",
        s=180,
        ax=ax,
    )
    for row in chart.itertuples():
        ax.text(row.total_volume_usd, row.total_net_pnl, f" {row.classification}", fontsize=9)
    ax.set_title("Profitability vs. Traded Volume")
    ax.set_xlabel("Total volume (USD)")
    ax.set_ylabel("Total net PnL")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "volume_vs_profit.png", dpi=220)
    plt.close(fig)


def create_plots(
    regime_summary: pd.DataFrame,
    daily_summary: pd.DataFrame,
    account_regime: pd.DataFrame,
    account_summary: pd.DataFrame,
) -> None:
    plot_regime_net_pnl(regime_summary)
    plot_daily_distribution(daily_summary)
    plot_account_heatmap(account_regime, account_summary)
    plot_volume_vs_profit(regime_summary)


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_pct(value: float) -> str:
    return f"{value:.2f}%"


def build_report(
    merged: pd.DataFrame,
    regime_summary: pd.DataFrame,
    daily_summary: pd.DataFrame,
    account_summary: pd.DataFrame,
    coin_summary: pd.DataFrame,
) -> str:
    valid = regime_summary[regime_summary["classification"].notna()].copy()
    best_total = valid.loc[valid["total_net_pnl"].idxmax()]
    best_efficiency = valid.loc[valid["net_pnl_to_volume"].idxmax()]
    best_trade = valid.loc[valid["avg_net_pnl_per_trade"].idxmax()]
    best_day = (
        daily_summary.groupby("classification", observed=True, as_index=False)
        .agg(
            profitable_day_rate=("daily_net_pnl", lambda s: (s > 0).mean() * 100),
            avg_daily_net_pnl=("daily_net_pnl", "mean"),
        )
        .sort_values("profitable_day_rate", ascending=False)
        .iloc[0]
    )

    top_accounts = account_summary.head(5).copy()
    regime_specialists = account_summary.sort_values("specialization_gap", ascending=False).head(5)

    top_coin_rows = (
        coin_summary.sort_values(["classification", "total_net_pnl"], ascending=[True, False])
        .groupby("classification", observed=False)
        .head(3)
    )

    overlap_start = merged["date"].min().date()
    overlap_end = merged["date"].max().date()
    unmatched = int(merged["classification"].isna().sum())

    findings = [
        f"`{best_total['classification']}` produced the largest absolute net PnL at {format_currency(best_total['total_net_pnl'])}, helped by the highest trade count and the largest number of active days.",
        f"`{best_trade['classification']}` delivered the strongest average net PnL per trade at {format_currency(best_trade['avg_net_pnl_per_trade'])}, suggesting fewer but higher-quality realizations in that regime.",
        f"`{best_efficiency['classification']}` had the best profit-to-volume efficiency at {best_efficiency['net_pnl_to_volume'] * 100:.2f}% net PnL per dollar traded.",
        f"`{best_day['classification']}` had the highest share of profitable days at {best_day['profitable_day_rate']:.2f}%, which makes it the most consistent regime on a day-level basis.",
        "Median trade-level net PnL stays slightly negative across all regimes, which implies a small number of outsized winners drive most profits.",
    ]

    recommendations = [
        f"Use sentiment as a regime filter rather than a standalone signal: allocate more risk to `{best_total['classification']}` and `{best_efficiency['classification']}` days, but combine it with trade selection logic.",
        "Track trader-specific regime fit. Several accounts are highly regime-sensitive, so copying or weighting trader activity should depend on the current sentiment bucket.",
        "Focus on realized PnL behavior, not just raw activity. High trade counts during neutral or greedy periods do not necessarily translate into superior efficiency.",
        "Treat `Extreme Fear` carefully because the overlap contains only a small number of days, which limits confidence in generalized conclusions for that regime.",
    ]

    top_account_lines = "\n".join(
        f"| {row.Account} | {row.total_trades:,} | {format_currency(row.total_net_pnl)} | {row.best_regime} | {row.worst_regime} |"
        for row in top_accounts.itertuples()
    )

    specialist_lines = "\n".join(
        f"| {row.Account} | {row.best_regime} | {row.worst_regime} | {format_currency(row.specialization_gap)} |"
        for row in regime_specialists.itertuples()
    )

    coin_lines = "\n".join(
        f"| {row.classification} | {row.Coin} | {row.trades:,} | {format_currency(row.total_net_pnl)} |"
        for row in top_coin_rows.itertuples()
    )

    regime_table = valid[
        [
            "classification",
            "trades",
            "active_days",
            "total_net_pnl",
            "avg_net_pnl_per_trade",
            "positive_trade_rate",
            "net_pnl_to_volume",
        ]
    ].copy()

    regime_lines = "\n".join(
        f"| {row.classification} | {row.trades:,} | {row.active_days} | {format_currency(row.total_net_pnl)} | {format_currency(row.avg_net_pnl_per_trade)} | {row.positive_trade_rate:.2f}% | {row.net_pnl_to_volume * 100:.2f}% |"
        for row in regime_table.itertuples()
    )

    bullet_findings = "\n".join(f"- {item}" for item in findings)
    bullet_recommendations = "\n".join(f"- {item}" for item in recommendations)

    report = f"""# Trader Performance vs. Bitcoin Sentiment

## Executive Summary
This project links Hyperliquid trader history with the Bitcoin Fear & Greed Index to study how market sentiment affects profitability, consistency, and behavior. The usable overlap spans **{overlap_start} to {overlap_end}** and covers **{len(merged):,} trades**, **{merged['Account'].nunique()} trader accounts**, and **{merged['Coin'].nunique()} traded instruments**.

## Core Findings
{bullet_findings}

## Regime Scorecard
| Regime | Trades | Active Days | Total Net PnL | Avg Net PnL / Trade | Positive Trade Rate | Net PnL / Volume |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{regime_lines}

## Top Performing Accounts
| Account | Trades | Total Net PnL | Best Regime | Worst Regime |
| --- | ---: | ---: | --- | --- |
{top_account_lines}

## Most Regime-Sensitive Accounts
| Account | Best Regime | Worst Regime | PnL Gap |
| --- | --- | --- | ---: |
{specialist_lines}

## Coins That Drove Regime-Level PnL
| Regime | Coin | Trades | Total Net PnL |
| --- | --- | ---: | ---: |
{coin_lines}

## Strategy Implications
{bullet_recommendations}

## Methodology
- Converted trade timestamps to calendar dates and joined them to the daily sentiment label on the same date.
- Used **net PnL = Closed PnL - Fee** as the main profitability metric.
- Calculated regime-level metrics across trade count, active days, win rate, and profit-to-volume efficiency.
- Measured account specialization by comparing each trader's best and worst sentiment regime.

## Caveats
- Sentiment is a daily macro label, so it does not capture intraday regime shifts.
- The trading dataset contains multiple assets, while the sentiment index is Bitcoin-specific.
- Only **{unmatched}** trades could not be matched to a sentiment day, so coverage is effectively complete.
- `Extreme Fear` appears on relatively few overlap days, so those results should be treated as directional rather than conclusive.

## Output Files
- `outputs/regime_summary.csv`
- `outputs/daily_regime_summary.csv`
- `outputs/account_regime_summary.csv`
- `outputs/account_overview.csv`
- `outputs/top_coins_by_regime.csv`
- `outputs/regime_pnl_overview.png`
- `outputs/daily_regime_behavior.png`
- `outputs/account_regime_heatmap.png`
- `outputs/volume_vs_profit.png`
"""
    return report


def main() -> None:
    sns.set_theme(style="whitegrid")
    OUTPUT_DIR.mkdir(exist_ok=True)

    trades, sentiment = load_data()
    merged = prepare_dataset(trades, sentiment)

    regime_summary = build_regime_summary(merged)
    daily_summary = build_daily_summary(merged)
    account_regime, account_summary = build_account_summary(merged)
    coin_summary = build_coin_summary(merged)

    save_tables(
        merged=merged,
        regime_summary=regime_summary,
        daily_summary=daily_summary,
        account_regime=account_regime,
        account_summary=account_summary,
        coin_summary=coin_summary,
    )
    create_plots(regime_summary, daily_summary, account_regime, account_summary)

    report = build_report(
        merged=merged,
        regime_summary=regime_summary,
        daily_summary=daily_summary,
        account_summary=account_summary,
        coin_summary=coin_summary,
    )
    (OUTPUT_DIR / "analysis_report.md").write_text(report, encoding="utf-8")

    print("Analysis complete.")
    print(f"Report written to: {OUTPUT_DIR / 'analysis_report.md'}")


if __name__ == "__main__":
    main()
