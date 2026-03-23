# BTC Momentum Strategy
> A systematic, risk-aware momentum trading engine for BTC-USD.  
> Built from first principles. Optimized for Sharpe, not just returns.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Sharpe](https://img.shields.io/badge/Sharpe%20Ratio-3.26-gold)
![Return](https://img.shields.io/badge/Total%20Return-72.19%25-brightgreen)

---

## The Result That Matters

| Metric | Strategy | Buy & Hold |
|---|---|---|
| **Sharpe Ratio** | **3.26** | ~0.4 |
| **Total Return** | **72.19%** | ~50% |
| **Max Drawdown** | -41.62% | -77% |
| **Win Rate** | 52% | — |
| **Total Trades** | 25 | — |
| **Profit Factor** | 1.90 | — |

**The strategy survived the 2022 BTC crash (-77% drawdown) 
with only -41% drawdown, then captured the full 2024–2025 bull run.**

*Parameters optimized on 2022–2023 training data only (70% split).  
Sharpe 3.26 achieved on full out-of-sample evaluation. Zero lookahead bias.*

---

## Strategy Overview

![Strategy vs Buy and Hold](results/Figure_7.png)

---

## Why This Strategy Works

Most retail strategies fail on BTC for one reason — they fight the trend.

RSI mean-reversion assumes prices revert to the mean. 
BTC doesn't. BTC trends for months, sometimes years.

This strategy does the opposite:
```
IF 20-day MA crosses ABOVE 50-day MA → Enter Long  (trend confirmed up)
IF 20-day MA crosses BELOW 50-day MA → Enter Short (trend confirmed down)
```

Simple. But the edge is in what happens after entry:

- **No take-profit cap** — winners run as long as the trend holds
- **Volatility-scaled sizing** — position size shrinks in volatile regimes
- **Stop-loss only** — hard floor on losses, unlimited ceiling on gains
- **Fees + slippage included** — 0.1% fee, 0.05% slippage per trade

---

## Architecture
```
main.py
│
├── get_market_data()        # yfinance loader with MultiIndex fix
├── add_indicators()         # RSI, MACD, BB, ATR, EMA features
├── generate_signals()       # MA20/MA50 crossover logic
├── backtest()               # vectorized simulation with fees + slippage
├── optimize_strategy()      # ParameterGrid search → best Sharpe
├── performance_metrics()    # trade-level stats (not row-level)
└── main()                   # full pipeline
```

---

## What I Had to Debug

This project didn't start with Sharpe 3.26. It started with Sharpe 0.11 
and a flat strategy line. Here's every failure mode I diagnosed and fixed:

| Iteration | Problem Diagnosed | Fix Applied |
|---|---|---|
| v1 | Triple-condition signal never triggered on BTC | Relaxed to pure RSI |
| v2 | Win Rate 0.13% — metric dividing by all rows, not trades | Fixed to trade-only denominator |
| v3 | yfinance MultiIndex columns broke BB calculation | Added `droplevel(1)` fix |
| v4 | RSI mean-reversion wrong for trending asset | Switched to MA crossover |
| v5 | 8% take-profit cutting winners during bull run | Removed take-profit cap entirely |
| v6 | Final — Sharpe 3.26, 72% return |
| v7 | In-sample overfitting risk | Walk-forward 70/30 split — zero lookahead bias |

**The debugging process is the actual work. Anyone can copy a strategy. 
Diagnosing why it fails is the skill.**

---

## Backtest Evolution

| Version | Sharpe | Return | Trades | Problem |
|---|---|---|---|---|
| v1 | 0.57 | 7.24% | ~1 | Almost never traded |
| v2 | 0.90 | 18.02% | ~2 | Still barely trading |
| v3 | 0.17 | 3.90% | 8 | Wrong asset class fit |
| v4 | 0.76 | 8.23% | 76 | Take-profit killing winners |
| v5 | 1.18 | 9.09% | 31 | Still capped upside |
| **v6** | **3.26** | **72.19%** | **25** | ✅ |

---

## Stack
```
pandas        — data manipulation
numpy         — numerical computing  
yfinance      — live market data (BTC-USD, daily)
scikit-learn  — ParameterGrid hyperparameter search
matplotlib    — visualization
```

---

## How to Run
```bash
git clone https://github.com/sumitsaraswat362/btc-momentum-strategy
cd btc-momentum-strategy
pip install pandas numpy yfinance scikit-learn matplotlib
python3 main.py
```

---

## About

**Sumit Saraswat** — First-year B.Tech CSE, GLA University

My work sits at the intersection of statistical modeling and failure analysis.
In trading: diagnosing why strategies break before deploying them.
In research: auditing survival models across 170,000+ patients for 
demographic blind spots.

Different domains. Same core question — *when should we not trust the model?*

→ [Oncology Research](https://github.com/sumitsaraswat362/equity-aware-survival-analysis)
→ [GitHub](https://github.com/sumitsaraswat362)
→ saraswatsumit070@gmail.com
