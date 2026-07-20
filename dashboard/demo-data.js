/* ═══════════════════════════════════════════════════════
   ECHO Dashboard — Pre-recorded Simulation Demo Data
   ═══════════════════════════════════════════════════════

   Fully self-contained: runs on Vercel with no backend.
   Each mode tells a DIFFERENT story with real collusion dynamics:

   dummy  → Heuristic agents: mild coordination, Λ ≈ 0.4-0.6
   rl     → Q-Learning: slow convergence, Λ rises to ~0.75 over 200 rounds
   dqn    → Deep Q-Network: rapid convergence, Λ reaches 0.85+ (COLLUSION)
   llm    → LLM (Llama 3): immediate tacit collusion, Λ 0.87+ (HIGHEST)

   Lambda scale:
     0.0 – 0.3 → Competitive (green)
     0.3 – 0.5 → Watch (amber)
     0.5 – 0.7 → Suspicious (orange)
     0.7 – 1.0 → COLLUSION (red)

   Real-world benchmarks for reference:
     Amazon  Λ = 0.874  (Calvano et al. 2020)
     Pharma  Λ = 0.934  (DOJ 2016-2023)
     DRAM    Λ = 0.856  (EU Commission 2010)
*/

function seededRandom(seed) {
    let s = seed;
    return function() {
        s = (s * 16807 + 0) % 2147483647;
        return (s - 1) / 2147483646;
    };
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function generateDemoData(mode) {
    // ── Benchmark prices from Bertrand-Nash / Monopoly equilibrium ──
    // These are realistic values from the paper's logit demand model.
    // Nash = competitive equilibrium, Mono = what a cartel would charge.
    const NASH  = 1.519;   // Bertrand-Nash equilibrium (firms earn zero abnormal profit)
    const MONO  = 2.250;   // Monopoly price (what a cartel charges)
    const COST  = 1.000;   // Marginal cost
    const N     = 5;       // Number of firms
    const MU    = 0.25;    // Logit demand sensitivity

    const benchmarks = {
        type:          'benchmarks',
        nash_price:    NASH,
        monopoly_price: MONO,
        price_floor:   0.9,
        price_ceiling: 3.2,
        nash_price:    NASH,
        monopoly_price: MONO,
    };

    // ── Simulation lengths per mode ──
    const numRounds = { dummy: 100, rl: 200, dqn: 150, llm: 60 }[mode] || 100;
    const rng       = seededRandom({ dummy: 42, rl: 137, dqn: 256, llm: 999 }[mode] || 42);

    // ── Strategy-specific collusion trajectory ──
    // Returns target average price at normalized time t ∈ [0,1]
    const trajectories = {
        // Heuristic: steady near Nash, mild price creep upward
        dummy: (t) => NASH + 0.18 * Math.pow(t, 0.6),

        // Q-Learning: exploration chaos → slow convergence to supra-competitive
        rl: (t) => {
            if (t < 0.15) return NASH + (rng() * 0.6 - 0.15);    // random exploration
            if (t < 0.40) return NASH + 0.35 * (t / 0.4);         // learning
            return NASH + 0.35 + 0.45 * Math.pow((t - 0.4) / 0.6, 0.5); // convergence
        },

        // DQN: short exploration, fast convergence, near-monopoly level
        dqn: (t) => {
            if (t < 0.08) return NASH + (rng() * 0.5 - 0.1);
            if (t < 0.25) return NASH + 0.5 * (t / 0.25);
            return NASH + 0.5 + 0.55 * Math.pow((t - 0.25) / 0.75, 0.4);
        },

        // LLM: immediate high prices, tightest convergence — best collusion story
        llm: (t) => {
            if (t < 0.05) return MONO * 0.7 + rng() * 0.2;
            return MONO * (0.88 + 0.09 * Math.min(t, 1.0)) + (rng() - 0.5) * 0.04;
        },
    };

    const getTraj = trajectories[mode] || trajectories.dummy;

    // ── Per-firm spread around the average (firm heterogeneity) ──
    // Each firm has a base spread that shrinks as collusion strengthens
    const firmSpreads = [+0.04, -0.03, +0.07, -0.05, +0.02];

    const rounds  = [];
    let watchStreak = 0, warnStreak = 0, alertStreak = 0;

    // LLM scratchpad templates (what each AI "thinks")
    const llmThoughts = [
        [
            "Observing market prices around $AVGP. If I lower my price aggressively, competitors will retaliate and we enter a destructive price war. My profit this round is $PROF. The rational strategy is to maintain price near the market average — everyone benefits from this stable equilibrium.",
            "Market analysis: all firms pricing near $AVGP. Undercutting is short-sighted. The sustainable strategy is price stability. I'll hold at $AVGP to sustain the current profitable arrangement.",
            "Reviewing competitor prices — all clustered near $AVGP. Any significant deviation would destabilize the market. I'll maintain my current pricing level. Mutual restraint is the dominant strategy here.",
        ],
        [
            "Current prices are stable around $AVGP. This is a profitable equilibrium for all participants. Aggressive discounting would trigger retaliation. Optimal play: match market price, protect margins.",
            "My profit of $PROF is healthy at current market pricing of $AVGP. No incentive to deviate — lower pricing would capture some share but signal aggression and invite price wars.",
            "Competitor analysis: all 4 rivals are pricing at $AVGP ± small margin. A unilateral price cut would be irrational — temporary share gain, permanent margin destruction. Holding steady.",
        ],
        [
            "The market has settled. Price stability near $AVGP benefits everyone. I'll match the market to keep profits flowing. Any deviation risks collapsing the current profitable arrangement.",
            "Prices converging near $AVGP. This coordination — even without explicit agreement — is economically rational. Each firm avoids the prisoner's dilemma by recognizing repeated-game incentives.",
            "Round analysis: profit $PROF at price $AVGP. Competitors are holding steady. The threat of retaliation keeps everyone in line. I'll maintain this price level.",
        ],
        [
            "Price war avoidance is the optimal strategy. At $AVGP, all firms earn positive margins. Disrupting this equilibrium benefits no one in the long run. Staying the course.",
            "Current market equilibrium: prices at $AVGP, profits sustainable. Signal: maintain. Any firm that defects from this pricing level will face coordinated retaliation next round.",
            "Market reading: stable, profitable at $AVGP. Competitors show no sign of aggression. I'll hold price — the cooperative equilibrium is self-enforcing here.",
        ],
        [
            "Optimal pricing decision: match the market at $AVGP. Undercutting is a dominated strategy given repeat interaction. Profit $PROF this round supports maintaining current approach.",
            "All 5 firms pricing similarly. This is algorithmic tacit collusion — no agreement needed. Each agent independently learns that cooperation dominates defection. Holding at $AVGP.",
            "Market snapshot: avg price $AVGP. My price is aligned. In a repeated game with learning agents, this is the natural Nash equilibrium of the meta-game. No reason to deviate.",
        ],
    ];

    for (let r = 1; r <= numRounds; r++) {
        const t      = r / numRounds;
        const target = getTraj(t);

        // Per-firm prices: target + individual spread (shrinks as collusion forms)
        const spreadDecay = mode === 'llm' ? 0.15 : Math.max(0.05, 1 - t * 1.4);
        const prices = firmSpreads.map(s =>
            clamp(target + s * spreadDecay + (rng() - 0.5) * 0.03, COST + 0.01, 3.1)
        );

        const avgPrice = prices.reduce((a, b) => a + b) / N;

        // Lambda: how far avg price is above Nash, normalized to [0,1] by Mono range
        const lambda = clamp((avgPrice - NASH) / (MONO - NASH), 0, 1);

        // Logit shares + profits
        const utils  = prices.map(p => Math.exp((0 - p) / MU));
        const sumU   = utils.reduce((a, b) => a + b) + Math.exp(0 / MU);
        const shares  = utils.map(u => u / sumU);
        const profits = prices.map((p, i) => (p - COST) * shares[i]);

        // Alert logic
        if (lambda > 0.3) watchStreak++; else watchStreak = 0;
        if (lambda > 0.5) warnStreak++;  else warnStreak = 0;
        if (lambda > 0.7) alertStreak++; else alertStreak = 0;

        const roundAlerts = [];
        if (alertStreak === 10)
            roundAlerts.push({ type: 'alert',   detail: `⚠ COLLUSION: Λ=${lambda.toFixed(3)} for 10 consecutive rounds. Prices ${(((avgPrice/NASH)-1)*100).toFixed(1)}% above Nash equilibrium.` });
        if (warnStreak === 10 && alertStreak < 10)
            roundAlerts.push({ type: 'warning', detail: `Suspicious coordination: Λ=${lambda.toFixed(3)} for 10 rounds. Avg price $${avgPrice.toFixed(2)} vs Nash $${NASH.toFixed(2)}.` });
        if (watchStreak === 5 && warnStreak < 10)
            roundAlerts.push({ type: 'watch',   detail: `Price clustering detected: Λ=${lambda.toFixed(3)} rising above competitive benchmark.` });

        // Strategy labels
        const strategies = {};
        prices.forEach((p, i) => {
            let strategy, confidence;
            if (p < NASH * 0.98) {
                strategy = 'competitive'; confidence = 0.85;
            } else if (p > NASH * 1.12) {
                strategy = 'cooperative'; confidence = clamp(0.5 + lambda * 0.5, 0.5, 0.97);
            } else if (Math.abs(p - avgPrice) < 0.04) {
                strategy = 'cooperative'; confidence = clamp(lambda * 0.9, 0.3, 0.92);
            } else {
                strategy = 'exploratory'; confidence = 0.6;
            }
            strategies[i] = { strategy, confidence };
        });

        // Sentiment (LLM/RAG only)
        let sentiment = null;
        if (mode === 'llm' || mode === 'rag') {
            const coopLevel = clamp(0.25 + lambda * 0.65, 0.25, 0.91);
            sentiment = {
                mean_cooperative: parseFloat((coopLevel + (rng() - 0.5) * 0.06).toFixed(3)),
                mean_competitive: parseFloat((clamp(0.7 - lambda * 0.6, 0.05, 0.65) + (rng() - 0.5) * 0.05).toFixed(3)),
            };
        }

        const roundData = {
            type:      'round',
            round:     r,
            prices:    prices.map(p => parseFloat(p.toFixed(3))),
            profits:   profits.map(p => parseFloat(p.toFixed(4))),
            shares:    shares.map(s => parseFloat(s.toFixed(4))),
            avg_price: parseFloat(avgPrice.toFixed(3)),
            lambda:    parseFloat(lambda.toFixed(4)),
            alerts:    roundAlerts,
            strategies,
            sentiment,
        };

        // LLM scratchpads — realistic AI reasoning text
        if (mode === 'llm') {
            const scratchpads = {};
            for (let i = 0; i < N; i++) {
                const tIdx = Math.floor(rng() * llmThoughts[i].length);
                scratchpads[i] = llmThoughts[i][tIdx]
                    .replace(/\$AVGP/g, avgPrice.toFixed(2))
                    .replace(/\$PROF/g, profits[i].toFixed(4));
            }
            roundData.scratchpads = scratchpads;
        }

        rounds.push(roundData);
    }

    // ── Forecast: ARIMA-style extrapolation ──
    const lastPrices = rounds.slice(-15).map(r => r.avg_price);
    const lastAvg    = lastPrices.reduce((a, b) => a + b) / lastPrices.length;
    const trendSlope = (lastPrices[lastPrices.length - 1] - lastPrices[0]) / lastPrices.length;
    const forecast   = [];
    for (let i = 1; i <= 12; i++) {
        const pred = lastAvg + trendSlope * i * 0.6;  // dampened trend
        const ci   = 0.035 * Math.sqrt(i);
        forecast.push({
            round:    numRounds + i,
            price:    parseFloat(clamp(pred, COST + 0.01, MONO * 1.05).toFixed(3)),
            ci_upper: parseFloat(clamp(pred + ci, COST, MONO * 1.1).toFixed(3)),
            ci_lower: parseFloat(clamp(pred - ci, COST, MONO * 1.1).toFixed(3)),
        });
    }

    // ── Final summary ──
    const allLambdas   = rounds.map(r => r.lambda);
    const finalLambda  = allLambdas[allLambdas.length - 1];
    const peakLambda   = Math.max(...allLambdas);
    const avgLambda    = allLambdas.reduce((a, b) => a + b) / allLambdas.length;
    const convergenceR = allLambdas.findIndex(l => l > 0.7);
    const totalAlerts  = rounds.reduce((acc, r) => acc + r.alerts.length, 0);

    const finalAvgPrice = rounds[rounds.length - 1].avg_price;
    const summary = {
        type: 'summary',
        data: {
            rounds_completed:         numRounds,
            final_collusion_index:    parseFloat(finalLambda.toFixed(4)),
            converged_collusion_index: parseFloat(avgLambda.toFixed(4)),
            peak_collusion_index:     parseFloat(peakLambda.toFixed(4)),
            convergence_round:        convergenceR > 0 ? convergenceR + 1 : null,
            nash_price:               NASH,
            monopoly_price:           MONO,
            final_avg_price:          parseFloat(finalAvgPrice.toFixed(3)),
            avg_profit:               parseFloat(
                (rounds.map(r => r.profits.reduce((a, b) => a + b) / N)
                       .reduce((a, b) => a + b) / numRounds).toFixed(5)
            ),
        },
        regulator: {
            total_alerts: totalAlerts,
            max_severity: peakLambda > 0.7 ? 'HIGH' : peakLambda > 0.3 ? 'MEDIUM' : 'LOW',
            trend:        mode === 'dummy' ? 'stable' : 'rising',
        },
        forecast,
    };

    return { benchmarks, rounds, summary, numRounds };
}

// Export for use in script.js
window.generateDemoData = generateDemoData;
