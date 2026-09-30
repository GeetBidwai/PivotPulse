# PivotPulse

NSE stock scanner and market-monitoring system focused on identifying
Volatility Contraction Pattern (VCP) setups and potential breakouts.

> **Status:** Early development — foundation stage

## Overview

PivotPulse is a Python-based market analysis project designed to scan
NSE-listed equities for structured technical setups, with an initial
focus on the Volatility Contraction Pattern (VCP).

The project is being built incrementally with an emphasis on:

- Transparent, rule-based detection
- Configurable strategy parameters
- Historical backtesting and validation
- Reliable market-data handling
- Separation between data providers and strategy logic
- Future real-time monitoring and notifications

The initial goal is to build a reliable **scanner and alerting system**.
Automated trading is not part of the initial implementation.

---

## Current Development Status

### Completed

- Project structure
- YAML-based configuration
- OHLCV data loading and validation
- Technical indicator calculations
- Market-data provider abstraction
- Local CSV market-data provider
- Initial automated tests
- Git/GitHub repository setup

### In Progress

- VCP detection engine
- Swing high/low detection
- Base detection
- Contraction analysis
- VCP scoring
- Pivot identification
- Breakout detection

### Planned

- Upstox historical market-data integration
- NSE stock universe scanning
- Historical backtesting
- Performance metrics
- VCP signal validation
- Real-time market monitoring
- Alert de-duplication
- Telegram/WhatsApp notifications
- Client-specific configuration
- Paper-trading support

---

## Initial VCP Framework

PivotPulse will initially use a rule-based VCP framework.

The initial configuration includes:

- Daily timeframe
- Minimum stock price: ₹50
- Minimum average daily turnover: ₹5 crore
- Price above 50-DMA and 200-DMA
- 50-DMA above 200-DMA
- Proximity to 52-week high
- Base duration: 15–120 trading days
- Typically 2–4 contractions
- Preferably decreasing contraction depth
- Decreasing volatility through the base
- Preferably decreasing volume through the base
- Final contraction preferably within 10%
- Breakout confirmation using price and volume
- VCP candidate score threshold: 70
- Strong setup threshold: 80

These parameters are configurable and will be refined through
testing and historical validation.

---

## Architecture

The project is designed so that market-data providers remain separate
from the strategy engine.

```text
Market Data
    │
    ├── CSV Provider
    │
    ├── Upstox Provider
    │
    └── Future Providers
            │
            ▼
      Standard OHLCV Data
            │
            ▼
        Indicators
            │
            ▼
      Trend Qualification
            │
            ▼
        Base Detection
            │
            ▼
     Contraction Analysis
            │
            ▼
        VCP Scoring
            │
            ▼
      Pivot Detection
            │
            ▼
     Breakout Detection
            │
            ▼
          Alerts
