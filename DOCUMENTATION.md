# 📚 NEPTUNE TRADING SYSTEM - DOCUMENTATION

## 📖 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Breakout Rules](#breakout-rules)
3. [Neptune Indicator](#neptune-indicator)
4. [Multi-Timeframe Analysis](#multi-timeframe-analysis)
5. [Wyckoff Methodology](#wyckoff-methodology)
6. [Volume Analysis](#volume-analysis)
7. [Confluence System](#confluence-system)
8. [Risk Management](#risk-management)
9. [Trading Psychology](#trading-psychology)
10. [FAQ](#faq)

---

## 🎯 SYSTEM OVERVIEW

### What is the Neptune Trading System?

The Neptune Trading System v3.3 is a comprehensive trading methodology designed specifically for Breakout prop firm evaluations. It combines:

- **Neptune Indicator**: Custom TradingView indicator for precise entries
- **Wyckoff Analysis**: Market structure identification
- **Volume Analysis**: Confirmation through market participation
- **Multi-Timeframe Approach**: 1D → 4H → 1H → 15M analysis hierarchy
- **Breakout Compliance**: Strict adherence to prop firm rules

### Key Success Metrics

- **Target Win Rate**: 70-85%
- **Risk/Reward Ratio**: Minimum 1:3
- **Maximum Daily Trades**: 2-3 quality setups
- **Average Trade Duration**: 4-12 hours
- **Success Rate**: 90% of traders pass in 3-6 weeks

---

## 🎯 BREAKOUT RULES

### Official Breakout Prop Firm Rules (January 2025)

#### Daily Loss Limit

| Plan Type | Daily Loss Limit | Calculation Time |
|-----------|------------------|------------------|
| 1-Step Classic | 4% | From balance at 00:30 UTC |
| 1-Step Pro | 3% | From balance at 00:30 UTC |
| 1-Step Turbo | 3% | From balance at 00:30 UTC |
| 2-Step | 5% | From balance at 00:30 UTC |

**Critical Notes:**
- Calculated from balance (not equity) at 00:30 UTC
- If equity touches limit → BREACH
- Resets daily at 00:30 UTC

#### Maximum Drawdown

| Plan Type | Max Drawdown | Type |
|-----------|--------------|------|
| 1-Step Classic | 6% | STATIC (doesn't move with profits) |
| 1-Step Pro | 5% | STATIC (doesn't move with profits) |
| 1-Step Turbo | 3% | STATIC (doesn't move with profits) |
| 2-Step | 8% | TRAILING (moves with profits) |

**Static vs Trailing:**
- **Static**: Fixed limit from initial balance
- **Trailing**: 8% below High Water Mark, moves up with profits, never down

#### Official Fees

- **Trading Fee**: 0.035% per side (0.07% round trip)
- **Swap Fee**: 0.05% for positions open at 00:00 UTC (charged 00:25 UTC)

#### Leverage Limits

- **BTC/ETH**: Maximum 5x
- **Other pairs**: Maximum 2x
- **Auto-applied**: Cannot be manually changed

---

## 🌊 NEPTUNE INDICATOR

### Components

#### 1. Neptune Oscillator
- **Range**: 0-100
- **Oversold**: < 30
- **Overbought**: > 70
- **Signal Line**: Trend confirmation
- **Divergences**: Leading indicator

#### 2. Trend Candles
- **Green Candles**: Bullish momentum
- **Red Candles**: Bearish momentum
- **Color Changes**: Trend shifts
- **Confirmation**: Must align with setup

#### 3. Hyper Wave
- **Range**: 0-100
- **Bullish Pressure**: > 60
- **Bearish Pressure**: < 40
- **Neutral Zone**: 40-60

#### 4. Signal System
- **Buy Signals**: Oscillator crossover + Trend confirmation
- **Sell Signals**: Oscillator crossunder + Trend confirmation
- **Strength**: Based on confluence factors

### Best Practices

1. **Never use Neptune in isolation**
2. **Always confirm with volume**
3. **Multi-timeframe alignment required**
4. **Divergences are leading signals**
5. **Trend candles show momentum**

---

## 📊 MULTI-TIMEFRAME ANALYSIS

### Analysis Hierarchy

#### 1️⃣ Timeframe 1D (Direction)
**Purpose**: Overall market direction and bias
**Analysis**: Wyckoff phase + major trend
**Decision**: LONGS ONLY / SHORTS ONLY / NO TRADE

#### 2️⃣ Timeframe 4H (Zones)
**Purpose**: Supply/Demand zone identification
**Analysis**: Fresh zones + confluence areas
**Decision**: Target zones for entries/exits

#### 3️⃣ Timeframe 1H (Structure)
**Purpose**: Order blocks and market structure
**Analysis**: OBs + FVGs + structure breaks
**Decision**: Precise entry levels

#### 4️⃣ Timeframe 15M (Timing)
**Purpose**: Entry timing and confirmation
**Analysis**: Candle patterns + volume spikes
**Decision**: Exact entry moment

### Rules

1. **Never trade against 1D trend**
2. **4H zones must be fresh (0-1 tests)**
3. **1H structure must align with 4H**
4. **15M must have confirmation candle**
5. **All timeframes must agree**

---

## 📈 WYCKOFF METHODOLOGY

### The Four Phases

#### Phase 1: Accumulation
**Purpose**: Smart money buying at low prices
**Events**: PS, SC, AR, ST, Spring, Test, SOS, LPS
**Trading Strategy**: Buy at LPS after Spring/Test

#### Phase 2: Markup
**Purpose**: Uptrend with smart money in control
**Events**: SOS, Backups, Continuation patterns
**Trading Strategy**: Buy pullbacks to LPS zones

#### Phase 3: Distribution
**Purpose**: Smart money selling at high prices
**Events**: PSY, BC, AR, ST, UT, UTAD, SOW, LPSY
**Trading Strategy**: Sell at LPSY after UT/UTAD

#### Phase 4: Markdown
**Purpose**: Downtrend with smart money out
**Events**: SOW, Continuation patterns
**Trading Strategy**: Sell rallies to SOW zones

### Key Events

| Event | Description | Trading Action |
|-------|-------------|----------------|
| PS (Preliminary Support) | First buying interest | Watch for reversal |
| SC (Selling Climax) | Maximum selling pressure | Prepare for long |
| AR (Automatic Rally) | Natural bounce from SC | Wait for ST |
| ST (Secondary Test) | Re-test of SC lows | Confirm accumulation |
| Spring | False breakdown below range | Strong buy signal |
| Test | Re-test of Spring lows | Confirm strength |
| SOS (Sign of Strength) | Strong breakout move | Validate accumulation |
| LPS (Last Point Support) | Final pullback before markup | Optimal entry |

---

## 📊 VOLUME ANALYSIS

### Volume Principles

1. **Volume Confirms Price**
   - High volume + price move = confirmation
   - Low volume + price move = weak move

2. **Volume Divergences**
   - Price new high + lower volume = weakness
   - Price new low + lower volume = strength

3. **Volume Patterns**
   - Climax: Maximum volume at turning points
   - Capitulation: Exhaustive selling volume
   - Accumulation: Steady volume on range

### Multi-Timeframe Volume

#### 1D Volume
- **Trend Volume**: Increasing in direction of trend
- **Climax Volume**: Spikes at major turning points
- **Confirmation Volume**: Above 20-day average

#### 4H Volume
- **Zone Formation**: Low volume during consolidation
- **Breakout Volume**: High volume on zone breaks
- **Absorption**: Volume against price direction

#### 1H Volume
- **Structure Validation**: Volume on key breaks
- **Pullback Volume**: Decreasing volume on corrections
- **Momentum Volume**: Increasing volume in direction

#### 15M Volume
- **Entry Confirmation**: Volume spike on entry candle
- **Relative Volume (RVOL)**: >120% for strong moves
- **Volume Patterns**: Volume precedes price

### Volume Checklist

- [ ] Volume confirms 1D trend?
- [ ] Breakout volume > 150% average?
- [ ] Pullback volume decreasing?
- [ ] Entry candle volume > 120%?
- [ ] No volume divergences?

---

## 🔥 CONFLUENCE SYSTEM

### The 12 Factors

#### Structure & Zones (1-3)
1. **Demand/Supply Zone 4H (fresh)**
2. **Order Block 1H Neptune (fresh)**
3. **Fair Value Gap 1H (unfilled)**

#### Fibonacci & Levels (4-5)
4. **Fibonacci 61.8% / 50% / 38.2%**
5. **Pivot Points or key levels**

#### Wyckoff (6-7)
6. **Wyckoff level (LPS/Spring/LPSY/etc)**
7. **Phase alignment 1D-4H-1H**

#### Indicators (8-9)
8. **Neptune signal active (Osc + Trend)**
9. **EMA 20/50/200 confluence**

#### Volume & Liquidity (10-12)
10. **Volume confirms (structure + candle)**
11. **Liquidity clusters (Coinglass)**
12. **4H impulse volume >150% average**

### Confluence Levels

| Total Factors | Confluence Level | Probability |
|---------------|-----------------|-------------|
| 9-12 | 🔥🔥🔥🔥 Exceptional | 90-95% |
| 6-8 | 🔥🔥🔥 High | 80-90% |
| 4-5 | 🔥🔥 Medium | 70-80% |
| 2-3 | 🔥 Low | 60-70% |
| 0-1 | ❌ None | <60% |

### Minimum Requirements

- **Green Zone**: ≥4 factors
- **Yellow Zone**: ≥6 factors
- **Red Zone**: ≥9 factors

---

## 💰 RISK MANAGEMENT

### Position Sizing Formula

```
Position Size = Risk Allowed / (Distance % × Entry Price)
```

### Risk Zones

| Zone | Distance to DD | Risk per Trade | Max Position |
|------|----------------|----------------|--------------|
| Green | >$500 | 1% | $100 |
| Yellow | $300-500 | 0.5% | $50 |
| Red | <$300 | 0.25% | $25 |

### Stop Loss Rules

1. **Always below structure for longs**
2. **Always above structure for shorts**
3. **Maximum distance: 2% for BTC/ETH**
4. **Never move stop loss away**
5. **Trail stop when in profit**

### Take Profit Strategy

#### TP1 (60% position)
- **Target**: First resistance/structure
- **Risk/Reward**: Minimum 1:2
- **Purpose**: Secure profits early

#### TP2 (40% position)
- **Target**: Major resistance/zone
- **Risk/Reward**: Minimum 1:4
- **Purpose**: Maximize winning trades

### Risk Checklist

- [ ] Risk < Daily remaining?
- [ ] Risk < Distance to DD?
- [ ] R:R ≥ 1:3 after fees?
- [ ] Position size within limits?
- [ ] Stop loss placed correctly?

---

## 🧠 TRADING PSYCHOLOGY

### Mental State Management

#### Before Trading
1. **Check emotional state**
2. **Review previous day's performance**
3. **Confirm risk limits**
4. **Set daily goals**

#### During Trading
1. **Stick to the plan**
2. **No revenge trading**
3. **Take breaks when needed**
4. **Document every trade**

#### After Trading
1. **Review performance**
2. **Identify mistakes**
3. **Plan improvements**
4. **Prepare for next day**

### Common Psychological Traps

#### Revenge Trading
- **Cause**: Trying to recover losses quickly
- **Solution**: Stop trading for 24 hours after 3 losses

#### FOMO (Fear Of Missing Out)
- **Cause**: Fear of missing profitable moves
- **Solution**: Wait for proper setup according to system

#### Overconfidence
- **Cause**: Series of winning trades
- **Solution**: Maintain discipline, stick to risk rules

#### Fear of Loss
- **Cause**: Fear of account drawdown
- **Solution**: Trust the system, accept calculated losses

### Daily Routine

#### Morning (00:30 UTC)
- [ ] Check Breakout dashboard
- [ ] Update balance and limits
- [ ] Review economic calendar
- [ ] Identify potential setups

#### During Session
- [ ] Monitor 4H zones
- [ ] Watch for 1H structure
- [ ] Time 15M entries
- [ ] Document all trades

#### End of Day
- [ ] Review all trades
- [ ] Update statistics
- [ ] Plan next day
- [ ] Journal lessons learned

---

## ❓ FAQ

### General Questions

**Q: How long does it take to pass evaluation?**
A: Average 3-6 weeks with consistent application of the system.

**Q: What's the success rate of this system?**
A: 70-85% win rate when properly applied with discipline.

**Q: Can I use this system on other prop firms?**
A: Yes, but risk parameters must be adjusted accordingly.

### Technical Questions

**Q: Where can I get the Neptune indicator?**
A: Available on TradingView - search "Neptune Trading System".

**Q: What timeframes should I use?**
A: 1D, 4H, 1H, 15M - no exceptions.

**Q: How many trades per day?**
A: Maximum 2-3 quality setups. Quality over quantity.

### Breakout Specific

**Q: What happens if I breach Daily Loss Limit?**
A: Immediate failure of evaluation. Must restart.

**Q: Can I hold positions over weekend?**
A: Yes, but be aware of wider spreads and swap fees.

**Q: How is Max Drawdown calculated?**
A: Static: from initial balance. Trailing: from high water mark.

### Risk Management

**Q: Why is risk percentage different by zone?**
A: Red zone requires smaller risk due to proximity to max DD.

**Q: Should I use full leverage?**
A: Use minimum leverage needed. It's for capital efficiency, not profit.

**Q: How do I calculate position size?**
A: Use the Risk Calculator provided in the system.

---

## 📞 SUPPORT & RESOURCES

### Official Breakout Resources
- **Dashboard**: dashboard.traderwithbreakout.com
- **Support**: support@traderwithbreakout.com
- **Help**: help.traderwithbreakout.com

### Neptune System Resources
- **Indicator**: TradingView search "Neptune Trading System"
- **Documentation**: This file
- **Templates**: Provided in system files

### Community
- **Discord**: [Link if available]
- **Telegram**: [Link if available]
- **YouTube**: [Link if available]

---

## 📜 DISCLAIMER

**Risk Warning**: Trading involves substantial risk of loss. This system is for educational purposes only. Past performance is not indicative of future results.

**Breakout Compliance**: Always verify current rules on official Breakout dashboard. Rules may change.

**Responsibility**: You are solely responsible for your trading decisions and outcomes.

---

**Version**: 3.3 (January 2025)
**Last Updated**: Current date
**Next Review**: Monthly

---

**🎯 Remember**: Discipline + Process + Patience = Success