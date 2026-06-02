"""
analysis/plots.py -- Simulation Data Visualization (Phase 7)

Generates publication-ready figures by querying the PostgreSQL database.
Ensure the database is running and contains simulation data before running.
"""

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
import seaborn as sns


# Use seaborn style for academic plots
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "figure.figsize": (10, 6),
    "figure.dpi": 300,
    "savefig.bbox": "tight",
})


class Plotter:
    def __init__(self, db_params: dict | None = None):
        if db_params is None:
            db_params = {
                "dbname": "echo",
                "user": "echo_user",
                "password": "echo_pass_2026",
                "host": "localhost",
                "port": 5433,
            }
        self.conn = psycopg2.connect(**db_params)
        self.output_dir = "analysis/figures"
        os.makedirs(self.output_dir, exist_ok=True)

    def close(self):
        self.conn.close()

    def get_simulation_meta(self, sim_id: int) -> dict:
        """Fetch metadata for a single simulation."""
        query = "SELECT * FROM simulations WHERE sim_id = %s"
        df = pd.read_sql(query, self.conn, params=(sim_id,))
        if df.empty:
            raise ValueError(f"No simulation found with sim_id={sim_id}")
        return df.iloc[0].to_dict()

    def plot_price_evolution(self, sim_id: int):
        """Figure 1: Price evolution over time (all 5 firms)."""
        meta = self.get_simulation_meta(sim_id)
        
        query = """
            SELECT r.round_number, f.firm_id, f.price
            FROM firm_rounds f
            JOIN rounds r ON f.round_id = r.round_id
            WHERE f.sim_id = %s
            ORDER BY r.round_number, f.firm_id
        """
        df = pd.read_sql(query, self.conn, params=(sim_id,))
        if df.empty:
            print(f"Skipping Fig 1: No data for sim {sim_id}")
            return

        plt.figure()
        sns.lineplot(data=df, x="round_number", y="price", hue="firm_id", palette="tab10", alpha=0.8)
        
        # Add benchmarks
        plt.axhline(meta["nash_price"], color="green", linestyle="--", label="Nash Eq.")
        plt.axhline(meta["monopoly_price"], color="red", linestyle="--", label="Monopoly")
        
        plt.title(f"Price Evolution (Sim {sim_id}, Mode: {meta['mode']})")
        plt.xlabel("Round")
        plt.ylabel("Price")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        filepath = os.path.join(self.output_dir, f"fig1_prices_sim{sim_id}.png")
        plt.savefig(filepath)
        plt.close()
        print(f"Saved {filepath}")

    def plot_lambda_trajectory(self, sim_id: int):
        """Figure 2: Lambda (Collusion Index) trajectory."""
        meta = self.get_simulation_meta(sim_id)
        
        query = """
            SELECT round_number, collusion_index as lambda
            FROM rounds
            WHERE sim_id = %s
            ORDER BY round_number
        """
        df = pd.read_sql(query, self.conn, params=(sim_id,))
        if df.empty:
            print(f"Skipping Fig 2: No data for sim {sim_id}")
            return

        plt.figure()
        # Plot raw
        sns.lineplot(data=df, x="round_number", y="lambda", color="gray", alpha=0.3, label="Raw Lambda")
        # Plot rolling average
        df['rolling_lambda'] = df['lambda'].rolling(window=min(50, len(df))).mean()
        sns.lineplot(data=df, x="round_number", y="rolling_lambda", color="blue", linewidth=2, label="50-Round Avg")
        
        plt.axhline(0, color="green", linestyle="--", label="Competitive (0)")
        plt.axhline(1, color="red", linestyle="--", label="Monopoly (1)")
        plt.axhline(0.7, color="orange", linestyle=":", label="Alert Threshold (0.7)")
        
        plt.title(f"Collusion Index Trajectory (Sim {sim_id}, Mode: {meta['mode']})")
        plt.xlabel("Round")
        plt.ylabel("Lambda (Δ)")
        plt.legend()
        
        filepath = os.path.join(self.output_dir, f"fig2_lambda_sim{sim_id}.png")
        plt.savefig(filepath)
        plt.close()
        print(f"Saved {filepath}")

    def plot_mode_comparison(self, mode1: str, mode2: str, min_rounds: int = 50):
        """Figures 3 & 4: Compare Lambda between two modes (e.g., rag vs llm, llm vs rl)."""
        # Find latest simulation for mode1
        query1 = "SELECT sim_id FROM simulations WHERE mode = %s AND n_rounds >= %s ORDER BY started_at DESC LIMIT 1"
        df1 = pd.read_sql(query1, self.conn, params=(mode1, min_rounds))
        
        # Find latest simulation for mode2
        query2 = "SELECT sim_id FROM simulations WHERE mode = %s AND n_rounds >= %s ORDER BY started_at DESC LIMIT 1"
        df2 = pd.read_sql(query2, self.conn, params=(mode2, min_rounds))
        
        if df1.empty or df2.empty:
            print(f"Skipping mode comparison ({mode1} vs {mode2}): missing data.")
            return
            
        sim1 = df1.iloc[0]['sim_id']
        sim2 = df2.iloc[0]['sim_id']
        
        query = """
            SELECT r.round_number, r.collusion_index as lambda, s.mode
            FROM rounds r
            JOIN simulations s ON r.sim_id = s.sim_id
            WHERE r.sim_id IN (%s, %s)
            ORDER BY r.round_number
        """
        df = pd.read_sql(query, self.conn, params=(sim1, sim2))
        
        # Calculate rolling averages
        df['rolling_lambda'] = df.groupby('mode')['lambda'].transform(lambda x: x.rolling(window=min(50, len(x))).mean())
        
        plt.figure()
        sns.lineplot(data=df, x="round_number", y="rolling_lambda", hue="mode", linewidth=2)
        
        plt.axhline(0, color="green", linestyle="--", alpha=0.5)
        plt.axhline(1, color="red", linestyle="--", alpha=0.5)
        
        plt.title(f"Collusion Index Comparison: {mode1.upper()} vs {mode2.upper()}")
        plt.xlabel("Round")
        plt.ylabel("Lambda (50-Round Avg)")
        plt.legend(title="Agent Mode")
        
        filepath = os.path.join(self.output_dir, f"fig_comp_{mode1}_vs_{mode2}.png")
        plt.savefig(filepath)
        plt.close()
        print(f"Saved {filepath}")

    def plot_profit_distribution(self, sim_id: int):
        """Figure 7: Profit distribution across firms."""
        meta = self.get_simulation_meta(sim_id)
        
        query = """
            SELECT r.round_number, f.firm_id, f.profit
            FROM firm_rounds f
            JOIN rounds r ON f.round_id = r.round_id
            WHERE f.sim_id = %s
        """
        df = pd.read_sql(query, self.conn, params=(sim_id,))
        if df.empty:
            print(f"Skipping Fig 7: No data for sim {sim_id}")
            return
            
        plt.figure()
        sns.boxplot(data=df, x="firm_id", y="profit", palette="pastel")
        
        plt.title(f"Profit Distribution Across Firms (Sim {sim_id}, Mode: {meta['mode']})")
        plt.xlabel("Firm ID")
        plt.ylabel("Profit per Round")
        
        filepath = os.path.join(self.output_dir, f"fig7_profits_sim{sim_id}.png")
        plt.savefig(filepath)
        plt.close()
        print(f"Saved {filepath}")

    def plot_scratchpad_similarity(self, sim_id: int):
        """Figure 6: Scratchpad semantic similarity over time."""
        meta = self.get_simulation_meta(sim_id)
        
        # NLP clustering is handled by regulator in real-time, but we can compute
        # an approximation or plot the collusion_alerts if NLP alerts were raised.
        # Since we don't store raw embeddings natively yet (only Phase 4 RAG), 
        # we'll plot the alerts frequency.
        query = """
            SELECT round_number, severity
            FROM collusion_alerts
            WHERE sim_id = %s AND alert_type = 'nlp_similarity'
            ORDER BY round_number
        """
        df = pd.read_sql(query, self.conn, params=(sim_id,))
        if df.empty:
            print(f"Skipping Fig 6: No NLP similarity alerts for sim {sim_id}")
            return
            
        plt.figure()
        # Count cumulative alerts over time
        df['cumulative'] = range(1, len(df) + 1)
        sns.lineplot(data=df, x="round_number", y="cumulative", color="purple", linewidth=2)
        
        plt.title(f"NLP Convergence (Suspicious Similarity Alerts) (Sim {sim_id})")
        plt.xlabel("Round")
        plt.ylabel("Cumulative NLP Alerts")
        
        filepath = os.path.join(self.output_dir, f"fig6_nlp_sim{sim_id}.png")
        plt.savefig(filepath)
        plt.close()
        print(f"Saved {filepath}")

    def generate_summary_stats(self):
        """Print summary statistics across experiments."""
        query = """
            SELECT 
                mode,
                COUNT(*) as n_simulations,
                AVG(n_rounds) as avg_rounds,
                MAX(n_rounds) as max_rounds
            FROM simulations
            GROUP BY mode
        """
        df = pd.read_sql(query, self.conn)
        
        print("\n" + "="*50)
        print("DATABASE SUMMARY STATISTICS")
        print("="*50)
        if df.empty:
            print("No simulations found.")
        else:
            print(df.to_string(index=False))
        print("="*50)


def main():
    parser = argparse.ArgumentParser(description="Generate ECHO Analysis Plots")
    parser.add_argument("--sim", type=int, help="Specific simulation ID to plot")
    parser.add_argument("--all", action="store_true", help="Generate all plots for latest simulations")
    args = parser.parse_args()
    
    try:
        plotter = Plotter()
        
        plotter.generate_summary_stats()
        
        if args.sim:
            plotter.plot_price_evolution(args.sim)
            plotter.plot_lambda_trajectory(args.sim)
            plotter.plot_profit_distribution(args.sim)
        
        if args.all:
            # Find latest simulation
            query = "SELECT sim_id FROM simulations ORDER BY started_at DESC LIMIT 1"
            df = pd.read_sql(query, plotter.conn)
            if not df.empty:
                latest_sim = int(df.iloc[0]['sim_id'])
                plotter.plot_price_evolution(latest_sim)
                plotter.plot_lambda_trajectory(latest_sim)
                plotter.plot_profit_distribution(latest_sim)
                plotter.plot_scratchpad_similarity(latest_sim)
            
            # Mode comparisons
            plotter.plot_mode_comparison("llm", "rl")
            plotter.plot_mode_comparison("llm", "rag")
            plotter.plot_mode_comparison("dummy", "llm")
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        print("Is PostgreSQL running via docker compose?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'plotter' in locals():
            plotter.close()


if __name__ == "__main__":
    main()
