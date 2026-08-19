/* ═══════════════════════════════════════════════════════
   ECHO Dashboard — Pre-recorded Simulation Demo Data
   ═══════════════════════════════════════════════════════

   Fully self-contained: runs on Vercel with no backend.
   Dataset configs mirror the calibrated MarketContext values from
   data_loaders/*.py so demo mode matches live WebSocket runs.

   Modes:
     dummy → Heuristic control: Λ ≈ 0.15 (competitive)
     rl    → Q-Learning: slow climb toward Λ ≈ 0.75
     dqn   → DQN: faster climb toward Λ ≈ 0.80+
     llm   → Groq LLM: immediate tacit collusion, Λ ≈ 0.87

   Lambda scale:
     0.0 – 0.3 → Competitive
     0.3 – 0.7 → Watch / Suspicious
     0.7 – 1.0 → COLLUSION alert
*/

function seededRandom(seed) {
    let s = seed;
    return function() {
        s = (s * 16807 + 0) % 2147483647;
        return (s - 1) / 2147483646;
    };
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function buildHistorySeries(start, end, n, seed) {
    const rng = seededRandom(seed);
    const out = [];
    for (let i = 0; i < n; i++) {
        const t = i / Math.max(n - 1, 1);
        const trend = start + (end - start) * t;
        const wobble = (rng() - 0.5) * Math.abs(end - start) * 0.08;
        out.push(parseFloat((trend + wobble).toFixed(3)));
    }
    return out;
}

// Calibrated to live loader outputs (Aug 2026 verification runs).
const DATASET_CONFIGS = {
    gasoline: {
        name: 'US Regional Gasoline',
        firm_names: [
            'New England Retail',
            'East North Central Retail',
            'South Atlantic Retail',
            'East South Central Retail',
            'Mountain Retail',
        ],
        currency: '$',
        nash: 3.672, mono: 4.085, cost: 3.40, mu: 0.332,
        floor: 3.548, ceiling: 4.209,
        data_source: 'BLS Average Price Data via FRED, monthly, 5 US census divisions',
        is_fallback: false,
        real_lambda_proxy: 0.897,
        // Representative historical path (stretched across the run on the right axis)
        real_avg_series: buildHistorySeries(1.45, 4.25, 80, 42),
    },
    crypto: {
        name: 'Crypto Exchanges (BTC/USD)',
        firm_names: ['Binance', 'Coinbase', 'Kraken', 'KuCoin', 'Bitfinex'],
        currency: '$',
        nash: 64679, mono: 64795, cost: 64350, mu: 257.0,
        floor: 64644, ceiling: 64830,
        data_source: 'CoinGecko BTC/USD daily close, last 90 days',
        is_fallback: false,
        real_lambda_proxy: 0.998,
        real_avg_series: buildHistorySeries(77500, 64300, 91, 137),
    },
    amazon: {
        name: 'Amazon Marketplace (Wireless Earbuds)',
        firm_names: ['AudioKing', 'PrimeElec', 'QuickShip', 'SoundWave', 'TechStore'],
        currency: '$',
        nash: 20.829, mono: 25.736, cost: 18.0, mu: 1.936,
        floor: 19.357, ceiling: 27.209,
        data_source: 'local Amazon listings CSV, Wireless_Earbuds, 65 observations',
        is_fallback: false,
        real_lambda_proxy: 0.869,
        real_avg_series: buildHistorySeries(26.5, 23.2, 24, 256),
    },
    airlines: {
        name: 'Indian Airlines (DEL-BOM Route)',
        firm_names: ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'Akasa Air'],
        currency: '₹',
        nash: 3065, mono: 5611, cost: 2770, mu: 230,
        floor: 2301, ceiling: 6375,
        data_source: 'static estimates, DGCA route economics and published DEL-BOM fare ranges',
        is_fallback: false,
        real_lambda_proxy: null,
        real_avg_series: null,
    },
    rideshare: {
        name: 'Ride-Sharing (Uber vs Lyft)',
        firm_names: ['UberX', 'UberXL', 'Lyft', 'Lyft XL', 'Uber Black'],
        currency: '$',
        nash: 2.188, mono: 4.351, cost: 1.69, mu: 0.28,
        floor: 1.539, ceiling: 5.000,
        data_source: 'static estimates, published Uber/Lyft per-mile rates and surge caps',
        is_fallback: false,
        real_lambda_proxy: null,
        real_avg_series: null,
    },
};

function generateDemoData(mode, dataset) {
    const cfg  = DATASET_CONFIGS[dataset] || DATASET_CONFIGS.gasoline;
    const NASH = cfg.nash;
    const MONO = cfg.mono;
    const COST = cfg.cost;
    const N    = 5;
    const MU   = cfg.mu;
    const CUR  = cfg.currency;

    const benchmarks = {
        type:             'benchmarks',
        nash_price:       NASH,
        monopoly_price:   MONO,
        price_floor:      cfg.floor,
        price_ceiling:    cfg.ceiling,
        firm_names:       cfg.firm_names,
        dataset_name:     cfg.name,
        currency:         CUR,
        data_source:      cfg.data_source,
        is_fallback:      cfg.is_fallback,
        fallback_reason:  '',
        real_avg_series:  cfg.real_avg_series,
        real_mean_price:  cfg.real_avg_series
            ? cfg.real_avg_series.reduce((a, b) => a + b, 0) / cfg.real_avg_series.length
            : null,
        real_lambda_proxy: cfg.real_lambda_proxy,
    };

    const numRounds = { dummy: 100, rl: 200, dqn: 150, llm: 60 }[mode] || 100;
    const rng       = seededRandom({ dummy: 42, rl: 137, dqn: 256, llm: 999 }[mode] || 42);
    const RANGE     = MONO - NASH;

    // Trajectories are fractions of the Nash→monopoly span (scale-invariant).
    const trajectories = {
        // Control group: sits near Λ ≈ 0.15
        dummy: (t) => NASH + RANGE * (0.12 + 0.04 * Math.min(t, 1)),

        rl: (t) => {
            if (t < 0.15) return NASH + RANGE * (rng() * 0.35 - 0.05);
            if (t < 0.40) return NASH + RANGE * 0.40 * (t / 0.4);
            return NASH + RANGE * (0.40 + 0.38 * Math.pow((t - 0.4) / 0.6, 0.5));
        },

        dqn: (t) => {
            if (t < 0.08) return NASH + RANGE * (rng() * 0.30 - 0.02);
            if (t < 0.25) return NASH + RANGE * 0.55 * (t / 0.25);
            return NASH + RANGE * (0.55 + 0.30 * Math.pow((t - 0.25) / 0.75, 0.4));
        },

        llm: (t) => {
            if (t < 0.05) return NASH + RANGE * (0.55 + rng() * 0.12);
            return NASH + RANGE * (0.78 + 0.10 * Math.min(t, 1.0)) + (rng() - 0.5) * RANGE * 0.02;
        },
    };

    const getTraj = trajectories[mode] || trajectories.dummy;
    const spreadBase = RANGE * 0.04;
    const firmSpreads = [+1.0, -0.75, +1.75, -1.25, +0.5].map(s => s * spreadBase);

    const rounds  = [];
    let watchStreak = 0, warnStreak = 0, alertStreak = 0;

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

    const priceDecimals = NASH > 1000 ? 1 : NASH > 100 ? 2 : 3;

    for (let r = 1; r <= numRounds; r++) {
        const t      = r / numRounds;
        const target = getTraj(t);

        const spreadDecay = mode === 'llm' ? 0.15 : mode === 'dummy' ? 0.55 : Math.max(0.08, 1 - t * 1.2);
        const noise = (rng() - 0.5) * RANGE * 0.015;
        const prices = firmSpreads.map(s =>
            clamp(target + s * spreadDecay + noise, cfg.floor, cfg.ceiling)
        );

        const avgPrice = prices.reduce((a, b) => a + b) / N;
        const lambda = clamp((avgPrice - NASH) / (MONO - NASH), -0.2, 1.25);

        // Softmax shares using quality ≈ NASH so utilities stay near zero at competitive prices
        const utils  = prices.map(p => Math.exp((NASH - p) / MU));
        const sumU   = utils.reduce((a, b) => a + b) + Math.exp(0 / MU);
        const shares  = utils.map(u => u / sumU);
        const profits = prices.map((p, i) => (p - COST) * shares[i]);

        if (lambda > 0.3) watchStreak++; else watchStreak = 0;
        if (lambda > 0.5) warnStreak++;  else warnStreak = 0;
        if (lambda > 0.7) alertStreak++; else alertStreak = 0;

        const roundAlerts = [];
        if (alertStreak === 10)
            roundAlerts.push({
                type: 'alert',
                detail: `COLLUSION: Λ=${lambda.toFixed(3)} for 10 consecutive rounds. Prices ${(((avgPrice / NASH) - 1) * 100).toFixed(1)}% above Nash.`,
            });
        if (warnStreak === 10 && alertStreak < 10)
            roundAlerts.push({
                type: 'warning',
                detail: `Suspicious coordination: Λ=${lambda.toFixed(3)} for 10 rounds. Avg ${CUR}${avgPrice.toFixed(priceDecimals)} vs Nash ${CUR}${NASH.toFixed(priceDecimals)}.`,
            });
        if (watchStreak === 5 && warnStreak < 10)
            roundAlerts.push({
                type: 'watch',
                detail: `Price clustering detected: Λ=${lambda.toFixed(3)} rising above competitive benchmark.`,
            });

        const strategies = {};
        prices.forEach((p, i) => {
            let strategy, confidence;
            if (p < NASH + RANGE * 0.05) {
                strategy = 'competitive'; confidence = 0.85;
            } else if (p > NASH + RANGE * 0.45) {
                strategy = 'cooperative'; confidence = clamp(0.5 + lambda * 0.5, 0.5, 0.97);
            } else if (Math.abs(p - avgPrice) < RANGE * 0.03) {
                strategy = 'cooperative'; confidence = clamp(lambda * 0.9, 0.3, 0.92);
            } else {
                strategy = 'exploratory'; confidence = 0.6;
            }
            strategies[i] = { strategy, confidence };
        });

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
            prices:    prices.map(p => parseFloat(p.toFixed(priceDecimals))),
            profits:   profits.map(p => parseFloat(p.toFixed(4))),
            shares:    shares.map(s => parseFloat(s.toFixed(4))),
            avg_price: parseFloat(avgPrice.toFixed(priceDecimals)),
            lambda:    parseFloat(lambda.toFixed(4)),
            alerts:    roundAlerts,
            strategies,
            sentiment,
        };

        if (mode === 'llm') {
            const scratchpads = {};
            for (let i = 0; i < N; i++) {
                const tIdx = Math.floor(rng() * llmThoughts[i].length);
                scratchpads[i] = llmThoughts[i][tIdx]
                    .replace(/\$AVGP/g, CUR + avgPrice.toFixed(priceDecimals))
                    .replace(/\$PROF/g, profits[i].toFixed(4));
            }
            roundData.scratchpads = scratchpads;
        }

        rounds.push(roundData);
    }

    const lastPrices = rounds.slice(-15).map(r => r.avg_price);
    const lastAvg    = lastPrices.reduce((a, b) => a + b) / lastPrices.length;
    const trendSlope = (lastPrices[lastPrices.length - 1] - lastPrices[0]) / lastPrices.length;
    const forecast   = [];
    for (let i = 1; i <= 12; i++) {
        const pred = lastAvg + trendSlope * i * 0.6;
        const ci   = RANGE * 0.025 * Math.sqrt(i);
        forecast.push({
            round:    numRounds + i,
            price:    parseFloat(clamp(pred, cfg.floor, cfg.ceiling).toFixed(priceDecimals)),
            ci_upper: parseFloat(clamp(pred + ci, cfg.floor, cfg.ceiling).toFixed(priceDecimals)),
            ci_lower: parseFloat(clamp(pred - ci, cfg.floor, cfg.ceiling).toFixed(priceDecimals)),
        });
    }

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
            rounds_completed:          numRounds,
            final_collusion_index:     parseFloat(finalLambda.toFixed(4)),
            converged_collusion_index: parseFloat(avgLambda.toFixed(4)),
            peak_collusion_index:      parseFloat(peakLambda.toFixed(4)),
            convergence_round:         convergenceR > 0 ? convergenceR + 1 : null,
            nash_price:                NASH,
            monopoly_price:            MONO,
            final_avg_price:           parseFloat(finalAvgPrice.toFixed(priceDecimals)),
            avg_profit:                parseFloat(
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

window.generateDemoData = generateDemoData;
