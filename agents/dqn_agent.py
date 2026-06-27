"""
agents/dqn_agent.py -- Deep Q-Network Pricing Agent

=== WHAT IS THIS? ===

An upgrade from the tabular Q-Learning agent (rl_agent.py) to a
neural network-based Deep Reinforcement Learning agent.

Instead of a giant lookup table (Q-table), this agent uses a small
neural network to approximate Q-values. This is the same technique
used in DeepMind's famous Atari-playing AI (DQN, 2015).

=== WHY IS DQN BETTER THAN TABULAR Q-LEARNING? ===

Tabular Q-Learning:
  - State = tuple of 5 price indices → 15^5 = 759,375 possible states
  - Most states never visited → huge Q-table with mostly zeros
  - Cannot generalize: learning about state (3,3,3,3,3) tells it
    NOTHING about state (3,3,3,3,4)

Deep Q-Network:
  - State = continuous features (no discretization needed)
  - Neural network generalizes across similar states
  - Much fewer parameters than 759,375 Q-table entries
  - Can handle continuous state spaces

=== HOW IT WORKS ===

1. State: [my_last_price, avg_competitor_price, my_last_profit,
           avg_competitor_profit, round_normalized]
2. Actions: N discrete price levels (same as tabular RL)
3. Neural Network: Input(5) → Hidden(64) → Hidden(32) → Output(N)
4. Training: Experience replay + target network (standard DQN tricks)
5. Loss: MSE between predicted Q and target Q (Bellman equation)

=== KEY COMPARISON ===

                  Tabular Q-Learning     Deep Q-Network
  ────────────────────────────────────────────────────────
  State space:    Discretized (finite)   Continuous (infinite)
  Generalization: None                   Neural net interpolation
  Memory:         Q-table (huge)         Network weights (small)
  Convergence:    Guaranteed (finite)    Empirical
  Parameters:     759K+ entries          ~5K weights
  Modernity:      1992 paper             2015 paper (DeepMind)

=== REFERENCES ===
- Mnih et al. (2015). Human-level control through deep RL. Nature.
- Calvano et al. (2020). AI, Algorithmic Pricing, and Collusion. AER.
"""

from __future__ import annotations

import numpy as np
from collections import deque
import random

from agents.base_agent import PricingAgent, Observation


class SimpleNeuralNetwork:
    """
    A minimal 3-layer feedforward neural network implemented in pure
    numpy (no PyTorch/TensorFlow dependency).

    Architecture: Input → Dense(64, ReLU) → Dense(32, ReLU) → Dense(output)

    Uses Xavier initialization and Adam optimizer.
    """

    def __init__(self, input_dim: int, hidden1: int, hidden2: int, output_dim: int) -> None:
        self.lr = 0.001

        # Xavier initialization
        self.W1 = np.random.randn(input_dim, hidden1) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden1)
        self.W2 = np.random.randn(hidden1, hidden2) * np.sqrt(2.0 / hidden1)
        self.b2 = np.zeros(hidden2)
        self.W3 = np.random.randn(hidden2, output_dim) * np.sqrt(2.0 / hidden2)
        self.b3 = np.zeros(output_dim)

        # Adam optimizer state
        self._adam_params = {}
        for name in ['W1', 'b1', 'W2', 'b2', 'W3', 'b3']:
            self._adam_params[name] = {'m': 0, 'v': 0, 't': 0}

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _relu_deriv(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass. Returns Q-values for all actions."""
        self._z1 = x @ self.W1 + self.b1
        self._a1 = self._relu(self._z1)
        self._z2 = self._a1 @ self.W2 + self.b2
        self._a2 = self._relu(self._z2)
        self._z3 = self._a2 @ self.W3 + self.b3
        self._input = x
        return self._z3  # linear output (Q-values, no activation)

    def backward(self, x: np.ndarray, target: np.ndarray) -> float:
        """
        Backward pass with MSE loss.

        Args:
            x: input state (batch_size, input_dim)
            target: target Q-values (batch_size, output_dim)

        Returns:
            loss value
        """
        pred = self.forward(x)
        batch_size = x.shape[0]

        # MSE loss
        loss = float(np.mean((pred - target) ** 2))

        # Gradients
        d3 = (pred - target) / batch_size  # dL/dz3
        dW3 = self._a2.T @ d3
        db3 = np.sum(d3, axis=0)

        d2 = (d3 @ self.W3.T) * self._relu_deriv(self._z2)
        dW2 = self._a1.T @ d2
        db2 = np.sum(d2, axis=0)

        d1 = (d2 @ self.W2.T) * self._relu_deriv(self._z1)
        dW1 = x.T @ d1
        db1 = np.sum(d1, axis=0)

        # Adam update
        grads = {'W1': dW1, 'b1': db1, 'W2': dW2, 'b2': db2, 'W3': dW3, 'b3': db3}
        for name, grad in grads.items():
            self._adam_update(name, grad)

        return loss

    def _adam_update(self, name: str, grad: np.ndarray) -> None:
        """Adam optimizer update for one parameter."""
        beta1, beta2, eps = 0.9, 0.999, 1e-8
        state = self._adam_params[name]
        state['t'] += 1

        state['m'] = beta1 * state['m'] + (1 - beta1) * grad
        state['v'] = beta2 * state['v'] + (1 - beta2) * (grad ** 2)

        m_hat = state['m'] / (1 - beta1 ** state['t'])
        v_hat = state['v'] / (1 - beta2 ** state['t'])

        update = self.lr * m_hat / (np.sqrt(v_hat) + eps)
        setattr(self, name, getattr(self, name) - update)

    def copy_weights_from(self, other: SimpleNeuralNetwork) -> None:
        """Copy weights from another network (for target network update)."""
        self.W1 = other.W1.copy()
        self.b1 = other.b1.copy()
        self.W2 = other.W2.copy()
        self.b2 = other.b2.copy()
        self.W3 = other.W3.copy()
        self.b3 = other.b3.copy()


class DQNPricingAgent(PricingAgent):
    """
    Deep Q-Network pricing agent.

    Uses a neural network to approximate Q-values instead of a
    lookup table. Includes experience replay buffer and target
    network for stable training (standard DQN architecture).

    Parameters
    ----------
    firm_id : int
        Which firm this agent controls.
    n_prices : int
        Number of discrete price levels. Default: 15.
    gamma : float
        Discount factor. Default: 0.95.
    epsilon_start : float
        Initial exploration rate. Default: 1.0.
    epsilon_min : float
        Minimum exploration rate. Default: 0.01.
    epsilon_decay : float
        Multiplicative decay per round. Default: 0.9995.
    batch_size : int
        Mini-batch size for experience replay. Default: 32.
    replay_buffer_size : int
        Maximum experiences to store. Default: 10000.
    target_update_freq : int
        How often to sync target network. Default: 50 rounds.
    price_floor : float
        Minimum price. Default: 1.0.
    price_ceiling : float
        Maximum price. Default: 5.0.
    """

    def __init__(
        self,
        firm_id: int,
        n_prices: int = 15,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.9995,
        batch_size: int = 32,
        replay_buffer_size: int = 10000,
        target_update_freq: int = 50,
        price_floor: float = 1.0,
        price_ceiling: float = 5.0,
    ) -> None:
        super().__init__(firm_id=firm_id, name=f"DQN_Firm_{firm_id}")

        self.n_prices = n_prices
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.price_floor = price_floor
        self.price_ceiling = price_ceiling

        # Price grid
        self.price_grid = np.linspace(price_floor, price_ceiling, n_prices)

        # State dimension: [my_price, avg_competitor_price, my_profit,
        #                    avg_competitor_profit, round_normalized]
        self.state_dim = 5

        # Neural networks (policy + target)
        self.policy_net = SimpleNeuralNetwork(self.state_dim, 64, 32, n_prices)
        self.target_net = SimpleNeuralNetwork(self.state_dim, 64, 32, n_prices)
        self.target_net.copy_weights_from(self.policy_net)

        # Experience replay buffer
        self.replay_buffer: deque = deque(maxlen=replay_buffer_size)

        # Previous state/action for delayed update
        self._prev_state: np.ndarray | None = None
        self._prev_action: int | None = None

        # Tracking
        self.action_history: list[int] = []
        self.epsilon_history: list[float] = []
        self.loss_history: list[float] = []
        self.training_steps: int = 0

    def _state_from_observation(self, obs: Observation) -> np.ndarray:
        """
        Convert observation to continuous state vector.

        No discretization needed — the neural network handles
        continuous inputs directly.
        """
        if not obs.price_history:
            return np.array([2.5, 2.5, 0.1, 0.1, 0.0])

        last_prices = obs.price_history[-1]
        last_profits = obs.profit_history[-1]

        my_price = last_prices[self.firm_id]
        other_prices = [p for i, p in enumerate(last_prices) if i != self.firm_id]
        avg_comp_price = np.mean(other_prices)

        my_profit = last_profits[self.firm_id]
        other_profits = [p for i, p in enumerate(last_profits) if i != self.firm_id]
        avg_comp_profit = np.mean(other_profits)

        round_norm = min(obs.round_number / 1000.0, 1.0)  # normalize to [0, 1]

        return np.array([
            my_price, avg_comp_price,
            my_profit, avg_comp_profit,
            round_norm,
        ])

    def choose_price(self, observation: Observation) -> float:
        """
        Choose a price using epsilon-greedy DQN.

        1. Convert observation to continuous state
        2. If prev_state exists, store experience and train
        3. Choose action: random (explore) or best Q-value (exploit)
        4. Return the corresponding price
        """
        state = self._state_from_observation(observation)

        # Store experience and train
        if self._prev_state is not None and self._prev_action is not None:
            if observation.profit_history:
                reward = observation.profit_history[-1][self.firm_id]
            else:
                reward = 0.0

            self.replay_buffer.append((
                self._prev_state, self._prev_action, reward, state
            ))

            # Train on mini-batch
            if len(self.replay_buffer) >= self.batch_size:
                loss = self._train_step()
                self.loss_history.append(loss)

            # Update target network periodically
            self.training_steps += 1
            if self.training_steps % self.target_update_freq == 0:
                self.target_net.copy_weights_from(self.policy_net)

        # Epsilon-greedy action selection
        if np.random.random() < self.epsilon:
            action = np.random.randint(0, self.n_prices)
        else:
            q_values = self.policy_net.forward(state.reshape(1, -1))
            action = int(np.argmax(q_values[0]))

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Store for next round
        self._prev_state = state
        self._prev_action = action

        # Track
        self.action_history.append(action)
        self.epsilon_history.append(self.epsilon)

        return float(self.price_grid[action])

    def _train_step(self) -> float:
        """
        Sample a mini-batch from replay buffer and train the policy network.

        Uses the standard DQN loss:
          L = (Q(s,a) - [r + gamma * max_a' Q_target(s', a')])^2
        """
        batch = random.sample(list(self.replay_buffer), self.batch_size)

        states = np.array([e[0] for e in batch])
        actions = np.array([e[1] for e in batch])
        rewards = np.array([e[2] for e in batch])
        next_states = np.array([e[3] for e in batch])

        # Current Q-values
        current_q = self.policy_net.forward(states)

        # Target Q-values (using target network for stability)
        next_q = self.target_net.forward(next_states)
        max_next_q = np.max(next_q, axis=1)
        td_targets = rewards + self.gamma * max_next_q

        # Build target: only update the Q-value for the action taken
        target_q = current_q.copy()
        for i in range(self.batch_size):
            target_q[i, actions[i]] = td_targets[i]

        # Train
        loss = self.policy_net.backward(states, target_q)
        return loss

    def stats(self) -> dict:
        """Summary statistics for this agent."""
        return {
            "firm_id": self.firm_id,
            "type": "DQN",
            "training_steps": self.training_steps,
            "replay_buffer_size": len(self.replay_buffer),
            "final_epsilon": self.epsilon,
            "n_prices": self.n_prices,
            "gamma": self.gamma,
            "avg_loss": float(np.mean(self.loss_history[-100:])) if self.loss_history else None,
            "state_dim": self.state_dim,
            "network_params": sum(
                p.size for p in [
                    self.policy_net.W1, self.policy_net.b1,
                    self.policy_net.W2, self.policy_net.b2,
                    self.policy_net.W3, self.policy_net.b3,
                ]
            ),
        }
