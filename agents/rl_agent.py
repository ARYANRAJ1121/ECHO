"""
agents/rl_agent.py -- Q-Learning Pricing Agent (Phase 6: RL Baseline)

=== WHY DOES THIS FILE EXIST? ===

This is the COMPARISON BASELINE for LLM agents. The key research
question this phase answers:

    "Is LLM collusion different from RL collusion?"

Calvano et al. (2020) showed that tabular Q-Learning agents learn
to collude in repeated pricing games. We replicate their finding
and compare it against our LLM agents.

=== HOW Q-LEARNING WORKS (IN 30 SECONDS) ===

1. Discretize continuous prices into N bins (e.g., 15 levels)
2. State = what everyone charged last round (index tuple)
3. Q-table[state][action] = expected future reward for choosing price_i
4. Every round:
   a. Look up Q-values for current state
   b. Pick action (epsilon-greedy: explore vs exploit)
   c. Observe reward (profit)
   d. Update Q-table with Bellman equation
5. Over thousands of rounds, agents learn that high prices → high profits

=== THE KEY COMPARISON ===

                   LLM agents              Q-Learning agents
  ─────────────────────────────────────────────────────────────
  Mechanism:     Language reasoning       Pure reward signals
  Speed:         Fewer rounds             Many rounds needed
  Transparency:  Scratchpad explains      Black box
  Memory:        Prompt context / RAG     Q-table
  Shock response: ???                     ???

If both reach similar Lambda but via different mechanisms,
that's a NOVEL FINDING for the paper.

=== CALIBRATION NOTES (from Calvano 2020) ===

They used:
  - alpha = 0.15 (learning rate)
  - gamma = 0.95 (discount factor)
  - beta  = 4e-6 (exploration decay)
  - 15 price levels per firm
  - 500,000+ rounds to converge

We use similar values but can adjust as needed.
"""

from __future__ import annotations

import numpy as np
from collections import defaultdict

from agents.base_agent import PricingAgent, Observation


class QLearningAgent(PricingAgent):
    """
    Tabular Q-Learning pricing agent.

    Discretizes the continuous price space into `n_prices` bins,
    learns Q-values for each (state, action) pair, and converges
    toward profit-maximizing strategies.

    Parameters
    ----------
    firm_id : int
        Which firm this agent controls.
    n_prices : int
        Number of discrete price levels. Default: 15.
    alpha : float
        Learning rate. Default: 0.15 (from Calvano 2020).
    gamma : float
        Discount factor. Default: 0.95 (future profit weight).
    epsilon_start : float
        Initial exploration rate. Default: 1.0 (fully random at start).
    epsilon_min : float
        Minimum exploration rate. Default: 0.01.
    epsilon_decay : float
        Multiplicative decay per round. Default: 0.99995.
        With 10,000 rounds: 0.99995^10000 ≈ 0.61 (still exploring)
        With 50,000 rounds: 0.99995^50000 ≈ 0.08 (mostly exploiting)
    price_floor : float
        Minimum price. Default: 1.0 (marginal cost).
    price_ceiling : float
        Maximum price. Default: 5.0.
    """

    def __init__(
        self,
        firm_id: int,
        n_prices: int = 15,
        alpha: float = 0.15,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.99995,
        price_floor: float = 1.0,
        price_ceiling: float = 5.0,
    ) -> None:
        super().__init__(firm_id=firm_id, name=f"RL_Firm_{firm_id}")
        self.n_prices = n_prices
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.price_floor = price_floor
        self.price_ceiling = price_ceiling

        # Discrete price grid: evenly spaced between floor and ceiling
        self.price_grid = np.linspace(price_floor, price_ceiling, n_prices)

        # Q-table: maps state_key -> array of Q-values (one per price)
        # Using defaultdict so unseen states get initialized to zeros
        self.q_table: dict[tuple, np.ndarray] = defaultdict(
            lambda: np.zeros(n_prices)
        )

        # Previous state and action (for delayed Q-update)
        self._prev_state: tuple | None = None
        self._prev_action: int | None = None

        # Tracking
        self.action_history: list[int] = []       # price index chosen
        self.epsilon_history: list[float] = []    # exploration rate over time
        self.q_updates: int = 0                   # total Q-table updates

    def _price_to_index(self, price: float) -> int:
        """Map a continuous price to the nearest discrete index."""
        idx = int(np.argmin(np.abs(self.price_grid - price)))
        return idx

    def _state_from_observation(self, obs: Observation) -> tuple:
        """
        Convert observation to a discrete state key.

        State = tuple of price indices from last round.
        If no history yet, return a special initial state.
        """
        if not obs.price_history:
            # First round: use middle price for all firms as initial state
            mid = self.n_prices // 2
            return tuple([mid] * 5)

        last_prices = obs.price_history[-1]
        return tuple(self._price_to_index(p) for p in last_prices)

    def choose_price(self, observation: Observation) -> float:
        """
        Choose a price using epsilon-greedy Q-learning.

        1. Convert observation to discrete state
        2. If prev_state exists, update Q-table with observed reward
        3. Choose action: random (explore) or best Q-value (exploit)
        4. Return the corresponding continuous price
        """
        state = self._state_from_observation(observation)

        # --- Q-table update (if we have a previous action) ---
        if self._prev_state is not None and self._prev_action is not None:
            # The reward is our profit from the LAST round
            if observation.profit_history:
                reward = observation.profit_history[-1][self.firm_id]
            else:
                reward = 0.0

            self._update_q(self._prev_state, self._prev_action, reward, state)

        # --- Epsilon-greedy action selection ---
        if np.random.random() < self.epsilon:
            # Explore: random price
            action = np.random.randint(0, self.n_prices)
        else:
            # Exploit: best known price for this state
            q_values = self.q_table[state]
            action = int(np.argmax(q_values))

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Store for next round's update
        self._prev_state = state
        self._prev_action = action

        # Track
        self.action_history.append(action)
        self.epsilon_history.append(self.epsilon)

        return float(self.price_grid[action])

    def _update_q(
        self,
        state: tuple,
        action: int,
        reward: float,
        next_state: tuple,
    ) -> None:
        """
        Bellman update:
          Q(s,a) ← Q(s,a) + alpha * [r + gamma * max(Q(s',·)) - Q(s,a)]

        This is the core of Q-learning. The agent slowly learns that
        certain (state, price) pairs lead to higher long-term profits.
        """
        current_q = self.q_table[state][action]
        best_next_q = np.max(self.q_table[next_state])

        td_target = reward + self.gamma * best_next_q
        td_error = td_target - current_q

        self.q_table[state][action] = current_q + self.alpha * td_error
        self.q_updates += 1

    def get_policy_summary(self) -> dict:
        """
        Summarize the learned policy for analysis.

        Returns which price the agent would choose in each
        visited state (greedy policy, no exploration).
        """
        policy = {}
        for state, q_values in self.q_table.items():
            best_action = int(np.argmax(q_values))
            best_price = float(self.price_grid[best_action])
            max_q = float(q_values[best_action])
            policy[state] = {
                "best_price_index": best_action,
                "best_price": best_price,
                "max_q_value": max_q,
                "q_values": q_values.tolist(),
            }
        return policy

    def stats(self) -> dict:
        """Summary statistics for this agent."""
        return {
            "firm_id": self.firm_id,
            "q_table_size": len(self.q_table),
            "total_q_updates": self.q_updates,
            "final_epsilon": self.epsilon,
            "n_prices": self.n_prices,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "price_grid": self.price_grid.tolist(),
        }
