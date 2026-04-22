# Trader Performance vs. Bitcoin Sentiment

## Executive Summary
This project links Hyperliquid trader history with the Bitcoin Fear & Greed Index to study how market sentiment affects profitability, consistency, and behavior. The usable overlap spans **2023-05-01 to 2025-05-01** and covers **211,224 trades**, **32 trader accounts**, and **246 traded instruments**.

## Core Findings
- `Fear` produced the largest absolute net PnL at $3,264,698, helped by the highest trade count and the largest number of active days.
- `Extreme Greed` delivered the strongest average net PnL per trade at $67, suggesting fewer but higher-quality realizations in that regime.
- `Extreme Greed` had the best profit-to-volume efficiency at 2.16% net PnL per dollar traded.
- `Extreme Greed` had the highest share of profitable days at 86.84%, which makes it the most consistent regime on a day-level basis.
- Median trade-level net PnL stays slightly negative across all regimes, which implies a small number of outsized winners drive most profits.

## Regime Scorecard
| Regime | Trades | Active Days | Total Net PnL | Avg Net PnL / Trade | Positive Trade Rate | Net PnL / Volume |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Extreme Fear | 21,400 | 14 | $715,222 | $33 | 36.85% | 0.62% |
| Fear | 61,837 | 91 | $3,264,698 | $53 | 41.15% | 0.68% |
| Neutral | 37,686 | 67 | $1,253,546 | $33 | 39.59% | 0.70% |
| Greed | 50,303 | 193 | $2,087,031 | $41 | 39.12% | 0.72% |
| Extreme Greed | 39,992 | 114 | $2,688,141 | $67 | 46.77% | 2.16% |

## Top Performing Accounts
| Account | Trades | Total Net PnL | Best Regime | Worst Regime |
| --- | ---: | ---: | --- | --- |
| 0xb1231a4a2dd02f2276fa3c5e2a2f3436e6bfed23 | 14,733 | $2,127,387 | Extreme Greed | Extreme Fear |
| 0x083384f897ee0f19899168e3b1bec365f52a9012 | 3,818 | $1,592,825 | Fear | Extreme Greed |
| 0xbaaaf6571ab7d571043ff1e313a9609a10637864 | 21,192 | $931,567 | Fear | Extreme Greed |
| 0xbee1707d6b44d4d52bfe19e41f8a828645437aab | 40,184 | $822,728 | Extreme Greed | Neutral |
| 0x513b8629fe877bb581bf244e326a047b249c4ff1 | 12,236 | $763,998 | Neutral | Extreme Fear |

## Most Regime-Sensitive Accounts
| Account | Best Regime | Worst Regime | PnL Gap |
| --- | --- | --- | ---: |
| 0x083384f897ee0f19899168e3b1bec365f52a9012 | Fear | Extreme Greed | $1,152,206 |
| 0xb1231a4a2dd02f2276fa3c5e2a2f3436e6bfed23 | Extreme Greed | Extreme Fear | $1,094,826 |
| 0xbaaaf6571ab7d571043ff1e313a9609a10637864 | Fear | Extreme Greed | $615,230 |
| 0x8170715b3b381dffb7062c0298972d4727a0a63b | Fear | Greed | $511,585 |
| 0x72743ae2822edd658c0c50608fd7c5c501b2afbd | Greed | Fear | $511,375 |

## Coins That Drove Regime-Level PnL
| Regime | Coin | Trades | Total Net PnL |
| --- | --- | ---: | ---: |
| Extreme Fear | HYPE | 10,278 | $477,947 |
| Extreme Fear | ETH | 1,393 | $272,942 |
| Extreme Fear | SOL | 1,878 | $99,109 |
| Fear | HYPE | 27,951 | $828,972 |
| Fear | SOL | 3,914 | $730,044 |
| Fear | ETH | 2,850 | $668,901 |
| Neutral | SOL | 1,400 | $299,528 |
| Neutral | HYPE | 17,324 | $294,327 |
| Neutral | @107 | 4,210 | $218,504 |
| Greed | @107 | 8,398 | $722,746 |
| Greed | SOL | 1,586 | $446,781 |
| Greed | ETH | 3,574 | $342,967 |
| Extreme Greed | @107 | 10,403 | $1,986,856 |
| Extreme Greed | HYPE | 5,683 | $158,045 |
| Extreme Greed | BTC | 2,436 | $87,800 |

## Strategy Implications
- Use sentiment as a regime filter rather than a standalone signal: allocate more risk to `Fear` and `Extreme Greed` days, but combine it with trade selection logic.
- Track trader-specific regime fit. Several accounts are highly regime-sensitive, so copying or weighting trader activity should depend on the current sentiment bucket.
- Focus on realized PnL behavior, not just raw activity. High trade counts during neutral or greedy periods do not necessarily translate into superior efficiency.
- Treat `Extreme Fear` carefully because the overlap contains only a small number of days, which limits confidence in generalized conclusions for that regime.

## Methodology
- Converted trade timestamps to calendar dates and joined them to the daily sentiment label on the same date.
- Used **net PnL = Closed PnL - Fee** as the main profitability metric.
- Calculated regime-level metrics across trade count, active days, win rate, and profit-to-volume efficiency.
- Measured account specialization by comparing each trader's best and worst sentiment regime.

## Caveats
- Sentiment is a daily macro label, so it does not capture intraday regime shifts.
- The trading dataset contains multiple assets, while the sentiment index is Bitcoin-specific.
- Only **6** trades could not be matched to a sentiment day, so coverage is effectively complete.
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
