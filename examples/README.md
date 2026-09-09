# Examples

All commands below run from the repository root.

| Example | Purpose | Network required |
|---|---|---:|
| `pricing_and_greeks.py` | Price a European option and report Greeks | No |
| `earnings_variance.py` | Demonstrate two-expiry variance decomposition | No |
| `plot_earnings_comparison.py` | Rebuild the saved AAPL comparison chart | No |
| `historical_earnings_variance.py` | Reconstruct one event from historical providers | Yes |
| `volatility_surface.py` | Build and plot a current volatility surface | Yes |

`live_data/` contains lower-level provider smoke checks. They require local API
credentials and may consume provider quota. `results/` contains a small,
sanitised case-study record so the headline result can be inspected without
credentials.
