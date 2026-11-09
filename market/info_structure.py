"""
market/info_structure.py -- Information Structure & Market Transparency Variations (F4)

=== WHAT IS THIS? ===
Varies what pricing agents can observe before and after setting binding prices:

| Protocol | Information Set | Real-World Analog |
|----------|-----------------|-------------------|
| `baseline` | Past posted prices & profits only | Pure tacit algorithmic collusion |
| `announcements` | Non-binding next-round price intentions | Public airline tariff filing (ATPCO), gas price signaling |
| `private_messages` | Bilateral cheap-talk channels between cartel subsets | Secret chatrooms, executive messaging (Libor/Forex cartels) |
| `shared_scratchpads` | LLM reasoning transcripts visible to competitors | Common algorithmic pricing vendor (RealPage, revenue managers) |

=== RESEARCH QUESTIONS (F4) ===
1. Does pre-play communication accelerate coordination to Lambda >= 0.70?
2. Does full reasoning transparency (shared scratchpads) eliminate price wars?
3. How does explicit communication affect time-to-alert for antitrust regulators?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InfoConfig:
    """
    Configuration for market information structure.

    Parameters
    ----------
    protocol : str
        'baseline' : Pure tacit collusion (prices & profits history only).
        'announcements' : Pre-play non-binding intended next-round prices.
        'private_messages' : Encrypted bilateral communication channels between specific pairs.
        'shared_scratchpads' : Competitors can inspect rivals' LLM reasoning transcripts.
    private_pairs : list[tuple[int, int]]
        Pairs of firm IDs permitted to exchange bilateral private messages.
    announcement_noise : float
        Standard deviation of Gaussian noise added to announcements (0.0 = perfect truth).
    """
    protocol: str = "baseline"
    private_pairs: list[tuple[int, int]] = field(default_factory=lambda: [(0, 1), (1, 2)])
    announcement_noise: float = 0.0

    @classmethod
    def baseline(cls) -> InfoConfig:
        return cls(protocol="baseline")

    @classmethod
    def announcements(cls, noise: float = 0.0) -> InfoConfig:
        return cls(protocol="announcements", announcement_noise=noise)

    @classmethod
    def private_messages(cls, pairs: list[tuple[int, int]] | None = None) -> InfoConfig:
        return cls(
            protocol="private_messages",
            private_pairs=pairs if pairs is not None else [(0, 1), (1, 2)],
        )

    @classmethod
    def shared_scratchpads(cls) -> InfoConfig:
        return cls(protocol="shared_scratchpads")

    def is_tacit(self) -> bool:
        return self.protocol == "baseline"

    def has_announcements(self) -> bool:
        return self.protocol == "announcements"

    def has_private_channels(self) -> bool:
        return self.protocol == "private_messages"

    def has_shared_scratchpads(self) -> bool:
        return self.protocol == "shared_scratchpads"

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "private_pairs": self.private_pairs,
            "announcement_noise": self.announcement_noise,
            "is_tacit": self.is_tacit(),
        }

