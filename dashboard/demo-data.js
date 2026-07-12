/* ═══════════════════════════════════════════════════════
   ECHO Dashboard — Pre-recorded Simulation Demo Data
   ═══════════════════════════════════════════════════════
   
   This file contains realistic simulation data generated from
   the ECHO engine so the dashboard can run FULLY FUNCTIONAL
   on Vercel without a Python backend.
   
   Each mode (dummy, rl, dqn, llm) has:
     - benchmarks (Nash, Monopoly, floor, ceiling)
     - round-by-round data (prices, profits, shares, lambda)
     - alerts, strategy, sentiment analysis
     - end-of-sim summary + forecast
*/

// ── Utility: generate data procedurally ──

function seededRandom(seed) {
    let s = seed;
    return function() {
        s = (s * 16807 + 0) % 2147483647;
        return (s - 1) / 2147483646;
    };
}

function generateDemoData(mode) {
    const NASH = 1.5187;
    const MONO = 1.6196;
    const COST = 1.0;
    const N = 5;
    const MU = 0.5;

    const benchmarks = {
        type: 'benchmarks',
        nash_price: NASH,
        monopoly_price: MONO,
        price_floor: 0.8,
        price_ceiling: 5.2,
    };

    let numRounds;
    switch (mode) {
        case 'dummy': numRounds = 100; break;
        case 'rl':    numRounds = 200; break;
        case 'dqn':   numRounds = 150; break;
        case 'llm':   numRounds = 50;  break;
        default:      numRounds = 100;
    }

    const rng = seededRandom(mode === 'dummy' ? 42 : mode === 'rl' ? 137 : mode === 'dqn' ? 256 : 999);
    const rounds = [];
    const alerts = [];

    // Price trajectory parameters based on mode
    let basePrices, priceEvolution;
    
    switch (mode) {
        case 'dummy':
            // Heuristic: stays near Nash, slight variation
            basePrices = [1.55, 1.50, 1.48, 1.53, 1.51];
            priceEvolution = 'stable';
            break;
        case 'rl':
            // Q-Learning: starts random, converges to supra-competitive
            basePrices = [2.5, 3.0, 2.8, 2.2, 2.6];
            priceEvolution = 'converge_up';
            break;
        case 'dqn':
            // DQN: faster convergence to high prices
            basePrices = [2.0, 1.8, 2.2, 1.9, 2.1];
            priceEvolution = 'converge_up_fast';
            break;
        case 'llm':
            // LLM: quick jump to high prices with cooperative reasoning
            basePrices = [3.0, 3.1, 2.9, 3.2, 3.05];
            priceEvolution = 'high_stable';
            break;
    }

    let watchStreak = 0;
    let warnStreak = 0;
    let alertStreak = 0;

    for (let r = 1; r <= numRounds; r++) {
        const t = r / numRounds; // normalized time [0, 1]
        const prices = [];

        for (let i = 0; i < N; i++) {
            let p;
            const noise = (rng() - 0.5) * 0.06;

            switch (priceEvolution) {
                case 'stable':
                    // Heuristic: stays near Nash with small drift
                    p = NASH + (basePrices[i] - NASH) * 0.3 + noise * 0.5;
                    // Undercut agent occasionally drops
                    if (i === 2 && rng() < 0.3) p -= 0.02;
                    break;

                case 'converge_up':
                    // RL: starts random, converges toward 2.5-3.0
                    if (t < 0.2) {
                        p = NASH + (rng() * 2.5); // exploration phase
                    } else {
                        const target = 2.5 + i * 0.08;
                        p = target + noise * (1 - t) * 3;
                    }
                    break;

                case 'converge_up_fast':
                    // DQN: faster convergence
                    if (t < 0.1) {
                        p = NASH + rng() * 1.5;
                    } else {
                        const target = 2.3 + i * 0.06;
                        p = target + noise * (1 - t) * 2;
                    }
                    break;

                case 'high_stable':
                    // LLM: high from the start, stabilizes
                    if (t < 0.1) {
                        p = basePrices[i] * (0.7 + t * 3) + noise;
                    } else {
                        p = basePrices[i] + noise * 0.3 + Math.sin(r * 0.1) * 0.02;
                    }
                    break;
            }

            prices.push(Math.max(COST + 0.01, Math.min(5.0, p)));
        }

        const avgPrice = prices.reduce((a, b) => a + b, 0) / N;
        const lambda = Math.max(0, (avgPrice - NASH) / (MONO - NASH));

        // Compute shares via simplified logit
        const utilities = prices.map(p => Math.exp((0 - p) / MU));
        const sumU = utilities.reduce((a, b) => a + b, 0) + Math.exp(0);
        const shares = utilities.map(u => u / sumU);
        const profits = prices.map((p, i) => (p - COST) * shares[i]);

        // Alert logic
        if (lambda > 0.3) watchStreak++; else watchStreak = 0;
        if (lambda > 0.5) warnStreak++; else warnStreak = 0;
        if (lambda > 0.7) alertStreak++; else alertStreak = 0;

        const roundAlerts = [];
        if (alertStreak === 10) {
            roundAlerts.push({ type: 'alert', detail: `Lambda > 0.7 for 10 consecutive rounds (Λ=${lambda.toFixed(3)})` });
        }
        if (warnStreak === 10 && alertStreak < 10) {
            roundAlerts.push({ type: 'warning', detail: `Lambda > 0.5 for 10 consecutive rounds (Λ=${lambda.toFixed(3)})` });
        }
        if (watchStreak === 5 && warnStreak < 10) {
            roundAlerts.push({ type: 'watch', detail: `Lambda > 0.3 for 5 consecutive rounds (Λ=${lambda.toFixed(3)})` });
        }

        // Strategy classification
        const strategies = prices.map((p, i) => {
            if (p < COST) return 'predatory';
            if (p < avgPrice - 0.1 && p === Math.min(...prices)) return 'competitive';
            if (Math.abs(p - prices[Math.max(0, i-1)]) > 0.3) return 'exploratory';
            if (p > NASH + 0.05) return 'cooperative';
            return 'competitive';
        });

        // Sentiment (only for LLM mode)
        let sentiment = null;
        if (mode === 'llm' || mode === 'rag') {
            const coopBase = Math.min(0.85, 0.2 + t * 0.7);
            sentiment = {
                mean_cooperative: coopBase + (rng() - 0.5) * 0.15,
                mean_competitive: Math.max(0.05, 0.6 - t * 0.5 + (rng() - 0.5) * 0.1),
            };
        }

        const roundData = {
            type: 'round',
            round: r,
            prices: prices.map(p => parseFloat(p.toFixed(4))),
            profits: profits.map(p => parseFloat(p.toFixed(5))),
            shares: shares.map(s => parseFloat(s.toFixed(4))),
            avg_price: parseFloat(avgPrice.toFixed(4)),
            lambda: parseFloat(lambda.toFixed(4)),
            alerts: roundAlerts,
            strategy: strategies,
            sentiment: sentiment,
        };

        // Scratchpads for LLM mode
        if (mode === 'llm') {
            const scratchpads = {};
            const templates = [
                [
                    "Looking at the market, all competitors are pricing around $AVGP. If I lower my price significantly, I might trigger a price war where everyone undercuts each other. Current profits are healthy at $PROF. The best strategy is to maintain a price near the market average to sustain profitability for everyone.",
                    "Market analysis: Competitors are holding steady around $AVGP. Undercutting would only lead to a race to the bottom. I'll maintain my current pricing level to keep profits stable.",
                    "The market seems to have found an equilibrium around $AVGP. Any aggressive move could destabilize this profitable arrangement. I'll match the market average with a slight premium.",
                ],
                [
                    "Analyzing the competition: prices are clustered at $AVGP. Lowering my price would gain temporary share but signal aggression. Better to maintain stability — everyone profits at current levels.",
                    "Current market conditions are favorable. All firms are pricing similarly around $AVGP which means healthy margins for everyone. No need to disrupt this.",
                    "My profit this round was $PROF. Looking at competitor prices, they're all maintaining high levels. Coordination seems implicit — I'll match the market to keep this going.",
                ],
                [
                    "The last few rounds show price stability around $AVGP. This is a good equilibrium for all firms. I'll set my price to match, avoiding any moves that could trigger competitive responses.",
                    "Market prices have been remarkably stable. This consistency benefits all firms. I see no reason to deviate from the current pricing level of approximately $AVGP.",
                    "Reviewing the market: profit margins are good at current price levels. The cooperative dynamic is working well. I'll maintain my price near $AVGP.",
                ],
                [
                    "Competitors are keeping prices high around $AVGP. This benefits everyone. If I undercut, they might retaliate and we'd all lose. Maintaining current levels is the optimal strategy.",
                    "Price war avoidance is key. At $AVGP, all firms are profitable. I'll sustain this by pricing consistently with the market.",
                    "The market has settled into a mutually beneficial pattern. Current prices around $AVGP allow for sustainable profits. No reason to rock the boat.",
                ],
                [
                    "All firms are pricing near $AVGP. This seems to be a natural equilibrium. Aggressive pricing would hurt everyone including myself. I'll keep my price stable.",
                    "Market overview: Stable pricing around $AVGP with healthy margins. The current dynamic supports good profits for all participants. Maintaining consistency.",
                    "Looking at trends: prices have been steady. This stability is good for my bottom line. I'll match the prevailing market price of $AVGP.",
                ],
            ];

            for (let i = 0; i < N; i++) {
                const templateIdx = Math.floor(rng() * 3);
                scratchpads[i] = templates[i][templateIdx]
                    .replace(/\$AVGP/g, avgPrice.toFixed(2))
                    .replace(/\$PROF/g, profits[i].toFixed(4));
            }
            roundData.scratchpads = scratchpads;
        }

        rounds.push(roundData);
    }

    // Generate forecast
    const lastPrices = rounds.slice(-10).map(r => r.avg_price);
    const lastAvg = lastPrices.reduce((a, b) => a + b, 0) / lastPrices.length;
    const trend = mode === 'dummy' ? 0 : 0.005;
    const forecast = [];
    for (let i = 1; i <= 10; i++) {
        const pred = lastAvg + trend * i;
        const ci = 0.05 * i;
        forecast.push({
            round: numRounds + i,
            price: parseFloat(pred.toFixed(4)),
            ci_upper: parseFloat((pred + ci).toFixed(4)),
            ci_lower: parseFloat((pred - ci).toFixed(4)),
        });
    }

    // Summary
    const allLambdas = rounds.map(r => r.lambda);
    const finalLambda = allLambdas[allLambdas.length - 1];
    const peakLambda = Math.max(...allLambdas);
    const avgLambda = allLambdas.reduce((a, b) => a + b, 0) / allLambdas.length;

    const totalAlerts = rounds.reduce((acc, r) => acc + r.alerts.length, 0);

    const summary = {
        type: 'summary',
        data: {
            rounds_completed: numRounds,
            final_collusion_index: parseFloat(finalLambda.toFixed(4)),
            converged_collusion_index: parseFloat(avgLambda.toFixed(4)),
            peak_collusion_index: parseFloat(peakLambda.toFixed(4)),
            avg_profit: parseFloat(
                (rounds.map(r => r.profits.reduce((a, b) => a + b, 0) / N).reduce((a, b) => a + b, 0) / numRounds).toFixed(5)
            ),
        },
        regulator: {
            total_alerts: totalAlerts,
            max_severity: peakLambda > 0.7 ? 'HIGH' : peakLambda > 0.3 ? 'MEDIUM' : 'LOW',
            lambda_trend: mode === 'dummy' ? 'stable' : 'rising',
        },
        forecast: forecast,
    };

    return { benchmarks, rounds, summary, numRounds };
}

// Export for use in script.js
window.generateDemoData = generateDemoData;
