Analyse Polymarket prediction markets for a given topic or question.

Use `pms` (polymarket-search CLI) to find relevant events, inspect market prices, and summarise what the crowd currently thinks.

## Steps

1. **Search for relevant events** using `pms event search "<topic>"`. Try a few keyword variations if the first search returns nothing useful. Use `--min-volume 0` if you want to include low-liquidity markets.

2. **Get event details** for promising results using `pms event info <event_id>`. This shows all markets within the event and their current Yes/No (or outcome) prices.

3. **Get individual market details** with `pms market info <market_id>` if you need volume, liquidity, or token IDs for a specific market.

4. **Summarise your findings**: interpret the prices as implied probabilities (e.g. Yes: 65% means the crowd gives a 65% chance of the event happening), note the volume as a signal of how much conviction is behind the price, and flag any markets with interesting or surprising prices.

## Tips

- Event prices are cached locally — use `pms event search "<topic>" --fresh` to force a live fetch if you need up-to-the-minute data.
- Markets with very low volume (< $1k) have wide spreads and unreliable prices — treat them with scepticism.
- For short-term crypto markets (e.g. "Bitcoin Up or Down"), prices update frequently — always use `--fresh` or `pms market info` for live data.
- Volume is lifetime total in USD. A market with $1M+ volume has significant real-money conviction behind it.

## Example invocations

```
/polymarket-analysis US presidential election 2028
/polymarket-analysis will the Fed cut rates this year
/polymarket-analysis bitcoin price end of year
```

## $ARGUMENTS

$ARGUMENTS
