"""
One-run analysis pack.

Each simulation wipes analysis/latest_run/ and writes ONLY charts that
belong to this dataset + mode + rounds. The dashboard reads that folder.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PACK_DIR = os.path.join("analysis", "latest_run")
COLORS = ["#C17A4E", "#6B8CAE", "#7A9E7E", "#B8925A", "#A07090"]


def reset_pack_dir(path: str = PACK_DIR) -> str:
    os.makedirs(path, exist_ok=True)
    for name in os.listdir(path):
        fp = os.path.join(path, name)
        if os.path.isfile(fp):
            os.remove(fp)
        elif os.path.isdir(fp):
            shutil.rmtree(fp)
    return path


def _arr(seq) -> np.ndarray:
    return np.asarray(seq, dtype=float)


def _save(fig, path: str) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def build_run_pack(
    *,
    dataset: str,
    mode: str,
    records: list[dict],
    firm_names: list[str] | None = None,
    nash: float | None = None,
    monopoly: float | None = None,
    currency: str = "$",
    real_avg_series: list[float] | None = None,
    regulator: dict | None = None,
    sentiment_report: dict | None = None,
    data_source: str = "",
) -> dict[str, Any]:
    """Replace previous pack. Returns summary JSON (also written to disk)."""
    out = reset_pack_dir()
    if not records:
        summary = {
            "ok": False,
            "error": "no rounds recorded",
            "figures": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    names = firm_names or [f"Firm {i + 1}" for i in range(5)]
    rounds = [int(r["round"]) for r in records]
    prices = _arr([r["prices"] for r in records])
    lambdas = _arr([r["lambda"] for r in records])
    avg_p = _arr([r["avg_price"] for r in records])
    profits = _arr([r.get("profits") or [0] * prices.shape[1] for r in records])
    shares = _arr([r.get("shares") or [0] * prices.shape[1] for r in records])
    n_firms = prices.shape[1]
    names = names[:n_firms]

    figures: list[dict[str, str]] = []

    # 1. Prices
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    for i in range(n_firms):
        ax.plot(rounds, prices[:, i], color=COLORS[i % len(COLORS)], label=names[i], lw=1.6)
    ax.plot(rounds, avg_p, color="#2B2620", ls=":", lw=1.4, label="Market avg")
    if nash is not None:
        ax.axhline(nash, color="#5A8F65", ls="--", lw=1.2, label=f"Nash {currency}{nash:.2f}")
    if monopoly is not None:
        ax.axhline(monopoly, color="#B85A5A", ls="--", lw=1.2, label=f"Monopoly {currency}{monopoly:.2f}")
    ax.set_title(f"Prices — {dataset} / {mode} ({len(rounds)} rounds)")
    ax.set_xlabel("Round")
    ax.set_ylabel(f"Price ({currency})")
    ax.legend(fontsize=7, loc="best")
    ax.grid(True, alpha=0.3)
    _save(fig, os.path.join(out, "01_prices.png"))
    figures.append({"id": "prices", "file": "01_prices.png", "title": "Price trajectories vs Nash / monopoly"})

    # 2. Lambda
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.plot(rounds, lambdas, color="#6B8CAE", lw=1.2, alpha=0.55, label="Lambda")
    win = min(50, max(3, len(lambdas) // 5))
    if len(lambdas) >= win:
        kernel = np.ones(win) / win
        roll = np.convolve(lambdas, kernel, mode="valid")
        ax.plot(rounds[win - 1 :], roll, color="#C17A4E", lw=2, label=f"{win}-round avg")
    ax.axhline(0.0, color="#5A8F65", ls="--", lw=1, label="Competitive")
    ax.axhline(0.3, color="#B8925A", ls=":", lw=1, label="Watch 0.3")
    ax.axhline(0.5, color="#C17A4E", ls=":", lw=1, label="Warning 0.5")
    ax.axhline(0.7, color="#B85A5A", ls="--", lw=1, label="Alert 0.7")
    ax.axhline(1.0, color="#8A8070", ls="--", lw=0.8, label="Monopoly 1.0")
    ax.set_title(f"Collusion index Λ — {dataset} / {mode}")
    ax.set_xlabel("Round")
    ax.set_ylabel("Λ")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    _save(fig, os.path.join(out, "02_lambda.png"))
    figures.append({"id": "lambda", "file": "02_lambda.png", "title": "Λ trajectory and alert thresholds"})

    # 3. Profits
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.boxplot(
        [profits[:, i] for i in range(n_firms)],
        patch_artist=True,
        boxprops=dict(facecolor="#F3EDE4"),
    )
    ax.set_xticks(range(1, n_firms + 1))
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_title(f"Profit distribution by firm — {dataset} / {mode}")
    ax.set_ylabel("Profit / round")
    ax.grid(True, axis="y", alpha=0.3)
    _save(fig, os.path.join(out, "03_profits.png"))
    figures.append({"id": "profits", "file": "03_profits.png", "title": "Per-firm profit spread"})

    # 4. Shares
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.stackplot(
        rounds,
        *[shares[:, i] for i in range(n_firms)],
        labels=names,
        colors=COLORS[:n_firms],
        alpha=0.85,
    )
    ax.set_title(f"Market shares — {dataset} / {mode}")
    ax.set_xlabel("Round")
    ax.set_ylabel("Share")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, loc="upper right")
    _save(fig, os.path.join(out, "04_shares.png"))
    figures.append({"id": "shares", "file": "04_shares.png", "title": "Market-share mix over rounds"})

    # 5. End-state snapshot
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8))
    last_p, last_pi, last_s = prices[-1], profits[-1], shares[-1]
    x = np.arange(n_firms)
    axes[0].bar(x, last_p, color=COLORS[:n_firms])
    axes[0].set_title("Final price")
    axes[1].bar(x, last_pi, color=COLORS[:n_firms])
    axes[1].set_title("Final profit")
    axes[2].bar(x, last_s, color=COLORS[:n_firms])
    axes[2].set_title("Final share")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels([n[:12] for n in names], rotation=25, ha="right", fontsize=7)
        ax.grid(True, axis="y", alpha=0.3)
    fig.suptitle(f"End-of-run snapshot — {dataset} / {mode}", fontsize=12)
    _save(fig, os.path.join(out, "05_snapshot.png"))
    figures.append({"id": "snapshot", "file": "05_snapshot.png", "title": "Final price / profit / share"})

    # 6. Real overlay only when this dataset has history
    if real_avg_series and len(real_avg_series) >= 5:
        real = _arr(real_avg_series)
        fig, ax = plt.subplots(figsize=(9.5, 4.0))
        ax.plot(np.arange(len(real)), real, color="#6B8CAE", lw=1.6, label="Observed market average")
        ax.axhline(float(np.mean(real)), color="#C17A4E", ls=":", label=f"Mean {currency}{np.mean(real):.2f}")
        ax.set_title(f"Observed reference series — {dataset}")
        ax.set_xlabel("Historical observation")
        ax.set_ylabel(f"Price ({currency})")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        _save(fig, os.path.join(out, "06_real_market.png"))
        figures.append({"id": "real", "file": "06_real_market.png", "title": "Real-market average (this dataset only)"})

    final_l = float(lambdas[-1])
    peak_l = float(np.max(lambdas))
    mean_l = float(np.mean(lambdas))
    if final_l >= 0.7:
        verdict = "collusion"
    elif final_l >= 0.3:
        verdict = "suspicious"
    else:
        verdict = "competitive"

    summary = {
        "ok": True,
        "dataset": dataset,
        "mode": mode,
        "rounds": len(rounds),
        "currency": currency,
        "data_source": data_source,
        "nash": nash,
        "monopoly": monopoly,
        "final_lambda": round(final_l, 4),
        "peak_lambda": round(peak_l, 4),
        "mean_lambda": round(mean_l, 4),
        "final_avg_price": round(float(avg_p[-1]), 4),
        "verdict": verdict,
        "regulator": regulator or {},
        "sentiment_report": sentiment_report,
        "figures": figures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "This folder is wiped and rebuilt after every simulation.",
    }
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  [Run pack] wrote {len(figures)} figures to {out}/")
    return summary


def load_latest_summary() -> dict[str, Any]:
    path = os.path.join(PACK_DIR, "summary.json")
    if not os.path.isfile(path):
        return {"ok": False, "figures": [], "error": "no run yet"}
    with open(path, encoding="utf-8") as f:
        return json.load(f)
