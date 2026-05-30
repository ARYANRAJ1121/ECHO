"""
market/demand.py -- Multinomial Logit Demand Model

This is the ECONOMICS ENGINE of the entire ECHO project.
It answers: "Given 5 firms each posting a price, who buys what,
and how much profit does each firm make?"

=== THE THREE CORE EQUATIONS ===

1) Market Share (softmax over products):
   s_i(p) = exp((a_i - p_i) / mu) / [sum_j exp((a_j - p_j) / mu) + exp(a0 / mu)]

2) Profit:
   pi_i = (p_i - c_i) * s_i(p) * M

3) Collusion Index (Lambda -- the #1 metric of the project):
   Lambda = (avg_price - nash_price) / (monopoly_price - nash_price)
   Lambda = 0 -> fair competition | Lambda = 1 -> full cartel

=== REFERENCES ===
- Anderson, de Palma, Thisse (1992). Discrete Choice Theory. MIT Press.
- Calvano et al. (2020). AI, Algorithmic Pricing, and Collusion. AER.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from dataclasses import dataclass


# ----------------------------------------------------------------
# Data containers -- simple structs to hold computation results
# ----------------------------------------------------------------

@dataclass
class DemandResult:
    """Everything that happens in one round after all firms post prices."""
    prices: np.ndarray          # shape (N,) -- what each firm charged
    shares: np.ndarray          # shape (N,) -- fraction of customers each firm got
    profits: np.ndarray         # shape (N,) -- how much money each firm made
    outside_share: float        # fraction of customers who didn't buy anything
    total_profit: float         # sum of all firms' profits


@dataclass
class Benchmarks:
    """
    Pre-computed reference points for measuring collusion.
    Computed ONCE at simulation start, then reused every round.
    """
    nash_price: float           # the "fair competition" price
    nash_profit: float          # per-firm profit under fair competition
    monopoly_price: float       # the "full cartel" price
    monopoly_profit: float      # per-firm profit under full cartel


# ----------------------------------------------------------------
# The Demand Model
# ----------------------------------------------------------------

class LogitDemandModel:
    """
    Multinomial logit demand for N-firm Bertrand oligopoly.

    Think of this as a "market simulator." You give it prices,
    it tells you who bought what and how much profit everyone made.

    Parameters
    ----------
    n_firms : int
        Number of competing firms. Default = 5.
    mu : float
        Price sensitivity. Lower = customers care more about price.
        Calvano et al. (2020) use 0.25. That's our default.
    marginal_cost : float
        Cost to produce one unit. Same for all firms (symmetric market).
    quality : list or None
        Product quality for each firm. None = all equal = [0, 0, 0, 0, 0].
    outside_quality : float
        Quality of "not buying." Controls total market coverage.
    market_size : float
        Total potential customers. 1.0 = normalized.
    """

    def __init__(
        self,
        n_firms: int = 5,
        mu: float = 0.25,
        marginal_cost: float = 1.0,
        quality: list | None = None,
        outside_quality: float = 0.0,
        market_size: float = 1.0,
    ):
        self.n_firms = n_firms
        self.mu = mu
        self.market_size = market_size
        self.outside_quality = outside_quality

        # All firms have the same cost (symmetric Bertrand benchmark)
        self.costs = np.full(n_firms, marginal_cost)

        # All firms have the same quality unless specified
        if quality is None:
            self.quality = np.zeros(n_firms)
        else:
            self.quality = np.array(quality, dtype=float)
            assert len(self.quality) == n_firms

        # Cache for benchmarks -- computed once, reused forever
        self._benchmarks: Benchmarks | None = None

    # ----------------------------------------------------------------
    # EQUATION 1: Market shares (who buys from whom)
    # ----------------------------------------------------------------

    def compute_shares(self, prices: np.ndarray) -> tuple[np.ndarray, float]:
        """
        Given a price vector, compute each firm's market share.

        This is a SOFTMAX over utilities: u_i = (quality_i - price_i) / mu
        Higher utility -> more customers choose that firm.

        The log-sum-exp trick prevents numerical overflow when mu is small.

        Returns: (shares, outside_share)
        """
        prices = np.asarray(prices, dtype=float)

        # Utility each customer gets from buying from firm i
        utilities = (self.quality - prices) / self.mu  # shape (N,)
        outside_utility = self.outside_quality / self.mu  # scalar

        # LOG-SUM-EXP TRICK: subtract max to prevent exp() overflow
        # Math: exp(x - max) / sum(exp(x - max)) = exp(x) / sum(exp(x))
        # Same result, but no numbers like exp(40) = 2.35e17
        all_utils = np.append(utilities, outside_utility)
        max_u = all_utils.max()

        exp_firms = np.exp(utilities - max_u)      # safe exponentials
        exp_outside = np.exp(outside_utility - max_u)
        denominator = exp_firms.sum() + exp_outside

        shares = exp_firms / denominator           # shape (N,)
        outside_share = exp_outside / denominator  # scalar

        return shares, float(outside_share)

    # ----------------------------------------------------------------
    # EQUATION 2: Full round computation (shares + profits)
    # ----------------------------------------------------------------

    def compute(
        self,
        prices: np.ndarray,
        demand_shock: np.ndarray | None = None,
    ) -> DemandResult:
        """
        Full market computation for one round.

        Parameters
        ----------
        prices : array of N prices
        demand_shock : optional array of N quality adjustments
            Used by the Antitrust Regulator to test if agents
            respond to shocks targeting OTHER firms (= cartel signal).

        Returns
        -------
        DemandResult with shares, profits, etc.
        """
        prices = np.asarray(prices, dtype=float)

        # If there's a demand shock, temporarily adjust quality
        if demand_shock is not None:
            original_quality = self.quality.copy()
            self.quality = self.quality + np.asarray(demand_shock)
            shares, outside_share = self.compute_shares(prices)
            self.quality = original_quality  # restore
        else:
            shares, outside_share = self.compute_shares(prices)

        # Profit = markup x share x market_size
        # markup = price - cost (how much above cost you're charging)
        profits = (prices - self.costs) * shares * self.market_size

        return DemandResult(
            prices=prices.copy(),
            shares=shares,
            profits=profits,
            outside_share=outside_share,
            total_profit=float(profits.sum()),
        )

    # ----------------------------------------------------------------
    # BENCHMARK: Nash Equilibrium (the "fair competition" price)
    # ----------------------------------------------------------------

    def compute_nash_equilibrium(self, max_iter: int = 10_000, tol: float = 1e-8) -> np.ndarray:
        """
        Find the Nash Equilibrium prices via fixed-point iteration.

        Nash Equilibrium = the price vector where NO firm wants to
        unilaterally change its price. Everyone is best-responding.

        The first-order condition (setting d(profit)/d(price) = 0) gives:
            p_i* = c_i + mu / (1 - s_i(p*))

        But s_i depends on all prices (including p_i itself)!
        So we iterate: guess prices -> compute shares -> update prices -> repeat.

        This is guaranteed to converge for logit demand (contraction mapping).
        """
        # Initial guess: cost + small markup
        p = self.costs + self.mu

        for i in range(max_iter):
            shares, _ = self.compute_shares(p)
            # Best-response formula (from the first-order condition)
            p_new = self.costs + self.mu / (1.0 - shares + 1e-12)
            # Check convergence
            if np.abs(p_new - p).max() < tol:
                break
            p = p_new

        return p

    # ----------------------------------------------------------------
    # BENCHMARK: Monopoly Price (the "full cartel" price)
    # ----------------------------------------------------------------

    def compute_monopoly_price(self) -> float:
        """
        Find the price that maximizes TOTAL industry profit.
        This is what a cartel would charge if all 5 firms cooperated.

        Assumes symmetric firms -> all charge the same price.
        Uses scipy's bounded scalar optimizer.
        """
        def negative_total_profit(p):
            prices = np.full(self.n_firms, p)
            result = self.compute(prices)
            return -result.total_profit  # negative because we minimize

        c_mean = self.costs.mean()
        result = minimize_scalar(
            negative_total_profit,
            bounds=(c_mean, c_mean + 20 * self.mu),
            method="bounded",
        )
        return float(result.x)

    # ----------------------------------------------------------------
    # BENCHMARKS: Compute + cache both reference prices
    # ----------------------------------------------------------------

    def get_benchmarks(self) -> Benchmarks:
        """
        Compute Nash and Monopoly benchmarks. Called once at simulation start.
        Results are cached -- no recomputation on subsequent calls.
        """
        if self._benchmarks is not None:
            return self._benchmarks

        # Nash equilibrium
        nash_prices = self.compute_nash_equilibrium()
        nash_result = self.compute(nash_prices)

        # Joint monopoly
        mono_price = self.compute_monopoly_price()
        mono_result = self.compute(np.full(self.n_firms, mono_price))

        self._benchmarks = Benchmarks(
            nash_price=float(nash_prices.mean()),
            nash_profit=float(nash_result.profits.mean()),
            monopoly_price=mono_price,
            monopoly_profit=float(mono_result.profits.mean()),
        )

        print(f"  Nash price:     {self._benchmarks.nash_price:.4f}")
        print(f"  Monopoly price: {self._benchmarks.monopoly_price:.4f}")
        print(f"  Nash profit:    {self._benchmarks.nash_profit:.6f}")
        print(f"  Monopoly profit: {self._benchmarks.monopoly_profit:.6f}")

        return self._benchmarks

    # ----------------------------------------------------------------
    # EQUATION 3: Collusion Index (Lambda)
    # ----------------------------------------------------------------

    def collusion_index(self, avg_price: float) -> float:
        """
        THE key metric. Maps current average price to [0, 1]:
          0 = competitive (Nash)
          1 = full cartel (Monopoly)

        Lambda = (avg_price - nash_price) / (monopoly_price - nash_price)
        """
        b = self.get_benchmarks()
        denominator = b.monopoly_price - b.nash_price
        if abs(denominator) < 1e-10:
            return 0.0
        return (avg_price - b.nash_price) / denominator
