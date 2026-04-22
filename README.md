# Trader Sentiment Analysis

Does the market's mood actually affect how traders perform? That's the core question this project tries to answer.

By combining real trade history from **Hyperliquid** with the **Bitcoin Fear & Greed Index**, this analysis maps out how different sentiment regimes — Extreme Fear, Fear, Neutral, Greed, Extreme Greed — influence trader profitability, consistency, and behavior across 211,224 trades over a two-year window (May 2023 to May 2025).

---

## What's Inside

```
├── trader_sentiment_analysis.ipynb   # Main analysis notebook
├── sentiment_analysis.py             # Python script version of the full pipeline
├── fear_greed_index.csv              # Daily Bitcoin Fear & Greed classifications
├── outputs/                          # Charts, CSVs, and the full analysis report
│   ├── analysis_report.md
│   ├── regime_pnl_overview.png
│   ├── daily_regime_behavior.png
│   ├── account_regime_heatmap.png
│   ├── volume_vs_profit.png
│   └── *.csv
└── notebook_outputs/                 # Supplementary CSVs from the notebook
```

> **Note:** `historical_data.csv` (46MB) is excluded from this repo. You can download it from the link in `description.txt`.

---

## Key Findings

- **Fear regimes drove the most raw profit** — trades executed during Fear days accumulated $3.26M in net PnL, the highest of any regime.
- **Extreme Greed was the most efficient** — it delivered the best average PnL per trade ($67), the best profit-to-volume ratio (2.16%), and the highest share of profitable days (86.84%).
- **Most trades lose money individually** — median net PnL is slightly negative across all regimes. A handful of outsized winners are carrying most of the gains.
- **Traders behave very differently depending on the regime** — some accounts thrive in Fear and collapse in Greed; others are the opposite. Sentiment regime fit is real and measurable.

### Regime Snapshot

| Regime | Trades | Total Net PnL | Avg PnL / Trade | Win Rate | PnL / Volume |
|---|---:|---:|---:|---:|---:|
| Extreme Fear | 21,400 | $715,222 | $33 | 36.85% | 0.62% |
| Fear | 61,837 | $3,264,698 | $53 | 41.15% | 0.68% |
| Neutral | 37,686 | $1,253,546 | $33 | 39.59% | 0.70% |
| Greed | 50,303 | $2,087,031 | $41 | 39.12% | 0.72% |
| Extreme Greed | 39,992 | $2,688,141 | $67 | 46.77% | 2.16% |

---

## Datasets

| Dataset | Source |
|---|---|
| Historical Trader Data (Hyperliquid) | Download link in `description.txt` |
| Bitcoin Fear & Greed Index | Included as `fear_greed_index.csv` |

The two datasets are joined on calendar date. Net PnL is computed as `Closed PnL - Fee`.

---

## Running the Analysis

**Requirements:** Python 3.9+, pandas, matplotlib, seaborn

```bash
pip install pandas matplotlib seaborn
```

Place `historical_data.csv` in the project root, then run:

```bash
python sentiment_analysis.py
```

Outputs will be written to the `outputs/` folder. Alternatively, open `trader_sentiment_analysis.ipynb` in Jupyter for an interactive walkthrough.

---

## What the Charts Show

- **`regime_pnl_overview.png`** — Total and average net PnL across all five sentiment regimes
- **`daily_regime_behavior.png`** — Day-level PnL distribution and profitable-day rates per regime
- **`account_regime_heatmap.png`** — Top 12 trader accounts broken down by their PnL in each regime
- **`volume_vs_profit.png`** — Whether trading more volume actually leads to more profit (spoiler: not always)

---

## Practical Takeaways

- Treat sentiment as a **regime filter**, not a buy/sell signal. Sizing up during Fear and Extreme Greed days, combined with good trade selection, seems to be where the edge is.
- **Know your regime fit.** If you're copying trades or following signal providers, their performance profile can shift dramatically depending on the sentiment environment.
- **Extreme Fear is underrepresented** in this dataset — only 14 days of overlap — so those results should be treated as directional rather than conclusive.
