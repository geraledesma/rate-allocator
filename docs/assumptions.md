# Model Assumptions

## V1 Allocator

### Rate Comparability
All rates are for the same time horizon (e.g., annual). No adjustments for different compounding frequencies.

### Full Allocation
The total amount is entirely deployed. No cash reserves modeled.

### No Negative Positions
All allocations are non-negative. No short selling or borrowing.

### Tier Structure
- Tiers are cumulative: the limit is the maximum **total** amount up to and including that tier
- Rates apply to the marginal amount in each tier
- Lower tiers must be filled completely before accessing higher tiers

### Static Optimization
Single-period allocation. No multi-period rebalancing or dynamic optimization.

### No Transaction Costs
No fees, taxes, or frictions.

### Daily Liquidity Assumption
All products have daily liquidity (for future backtesting).

## Future Extensions

Out of scope for V1:
- SOFIPO deposit insurance limits
- Multi-currency support
- Institution-specific withdrawal rules
- Tax optimization
- Real-time rate feeds
