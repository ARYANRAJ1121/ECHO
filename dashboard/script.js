/* ═══════════════════════════════════════════════════════
   ECHO Dashboard — Phase 8: Full Interactive Controller
   ═══════════════════════════════════════════════════════ */

// ── State ──
let ws = null;
let priceChart = null;
let lambdaChart = null;
let isRunning = false;
let totalRounds = 100;
let currentRound = 0;
let alertCount = 0;
let prevProfits = null;
let activeScratchpadFirm = 0;
let scratchpadData = {};   // { firmId: "latest text" }
let shockAnnotations = []; // rounds where shocks happened

// Agent palette — 5 vibrant, distinguishable colors
const COLORS = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#10b981', // emerald
    '#f59e0b', // amber
    '#ef4444', // red
];

const COLORS_ALPHA = COLORS.map(c => c + '30');

// ══════════════════════════════════════
// Chart Initialization
// ══════════════════════════════════════

function initCharts() {
    Chart.defaults.color = '#64748b';
    Chart.defaults.font.family = "'Inter', 'Outfit', system-ui, sans-serif";
    Chart.defaults.font.size = 12;

    // ── Price Chart ──
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    const priceSets = [];
    for (let i = 0; i < 5; i++) {
        priceSets.push({
            label: `Firm ${i + 1}`,
            data: [],
            borderColor: COLORS[i],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.15,
            order: 1,
        });
    }
    // Benchmark lines
    priceSets.push({
        label: 'Nash Price',
        data: [],
        borderColor: 'rgba(255, 255, 255, 0.18)',
        borderDash: [6, 4],
        borderWidth: 1,
        pointRadius: 0,
        order: 2,
    });
    priceSets.push({
        label: 'Monopoly Price',
        data: [],
        borderColor: 'rgba(239, 68, 68, 0.35)',
        borderDash: [6, 4],
        borderWidth: 1,
        pointRadius: 0,
        order: 2,
    });

    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: { labels: [], datasets: priceSets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 10, usePointStyle: true, padding: 16 },
                },
                annotation: { annotations: {} },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    title: { display: true, text: 'Round', color: '#64748b' },
                    ticks: { maxTicksLimit: 20 },
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    title: { display: true, text: 'Price ($)', color: '#64748b' },
                    min: 1.0,
                    max: 5.0,
                },
            },
        },
    });

    // ── Lambda Chart ──
    const lamCtx = document.getElementById('lambdaChart').getContext('2d');
    lambdaChart = new Chart(lamCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Λ (Collusion Index)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: (ctx) => {
                    const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.height);
                    g.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
                    g.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
                    return g;
                },
                fill: true,
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: {
                        watchLine: {
                            type: 'line',
                            yMin: 0.3,
                            yMax: 0.3,
                            borderColor: 'rgba(245, 158, 11, 0.4)',
                            borderWidth: 1,
                            borderDash: [4, 4],
                            label: {
                                content: 'Watch (0.3)',
                                display: true,
                                position: 'start',
                                backgroundColor: 'transparent',
                                color: 'rgba(245, 158, 11, 0.6)',
                                font: { size: 10 },
                            },
                        },
                        alertLine: {
                            type: 'line',
                            yMin: 0.7,
                            yMax: 0.7,
                            borderColor: 'rgba(239, 68, 68, 0.4)',
                            borderWidth: 1,
                            borderDash: [4, 4],
                            label: {
                                content: 'Alert (0.7)',
                                display: true,
                                position: 'start',
                                backgroundColor: 'transparent',
                                color: 'rgba(239, 68, 68, 0.6)',
                                font: { size: 10 },
                            },
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    title: { display: true, text: 'Round', color: '#64748b' },
                    ticks: { maxTicksLimit: 20 },
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    title: { display: true, text: 'Λ', color: '#64748b' },
                    min: -0.1,
                    max: 1.1,
                },
            },
        },
    });
}

// ══════════════════════════════════════
// Firm Table
// ══════════════════════════════════════

function initFirmTable() {
    const tbody = document.getElementById('firm-table-body');
    tbody.innerHTML = '';
    for (let i = 0; i < 5; i++) {
        const tr = document.createElement('tr');
        tr.id = `firm-row-${i}`;
        tr.innerHTML = `
            <td><span class="firm-color-dot" style="background:${COLORS[i]}"></span>Firm ${i + 1}</td>
            <td class="firm-price">—</td>
            <td class="firm-profit">—</td>
            <td class="firm-share">—</td>
            <td class="firm-delta"><span class="delta-flat">—</span></td>
        `;
        tbody.appendChild(tr);
    }
}

function updateFirmTable(prices, profits, shares) {
    for (let i = 0; i < 5; i++) {
        const row = document.getElementById(`firm-row-${i}`);
        if (!row) continue;
        const cells = row.querySelectorAll('td');
        cells[1].textContent = `$${prices[i].toFixed(3)}`;
        cells[2].textContent = profits[i].toFixed(4);
        cells[3].textContent = `${(shares[i] * 100).toFixed(1)}%`;

        // Delta
        if (prevProfits) {
            const delta = profits[i] - prevProfits[i];
            const sign = delta > 0.0001 ? '+' : delta < -0.0001 ? '' : '';
            const cls = delta > 0.0001 ? 'delta-up' : delta < -0.0001 ? 'delta-down' : 'delta-flat';
            cells[4].innerHTML = `<span class="${cls}">${sign}${delta.toFixed(4)}</span>`;
        }
    }
    prevProfits = [...profits];
}

// ══════════════════════════════════════
// Gauge
// ══════════════════════════════════════

function updateGauge(lambda) {
    const gauge = document.getElementById('lambda-gauge');
    const valueText = document.getElementById('lambda-value');
    const container = document.getElementById('gauge-container');

    const offset = 125.6 * (1 - Math.min(1, Math.max(0, lambda)));
    gauge.style.strokeDashoffset = offset;
    valueText.textContent = lambda.toFixed(3);

    // Remove old severity classes
    container.classList.remove('severity-high', 'severity-medium');

    if (lambda >= 0.7) {
        gauge.style.stroke = '#ef4444';
        valueText.style.color = '#ef4444';
        container.classList.add('severity-high');
    } else if (lambda >= 0.3) {
        gauge.style.stroke = '#f59e0b';
        valueText.style.color = '#f59e0b';
        container.classList.add('severity-medium');
    } else {
        gauge.style.stroke = '#3b82f6';
        valueText.style.color = '#f1f5f9';
    }
}

// ══════════════════════════════════════
// Alerts
// ══════════════════════════════════════

function addAlert(round, type, detail) {
    const feed = document.getElementById('alerts-feed');
    const empty = feed.querySelector('.empty-state');
    if (empty) empty.remove();

    const el = document.createElement('div');
    el.className = `alert-item ${type.toLowerCase()}`;
    el.innerHTML = `
        <div class="alert-meta">
            <span>${type.toUpperCase()}</span>
            <span>Round ${round}</span>
        </div>
        <div class="alert-detail">${detail}</div>
    `;
    feed.prepend(el);

    // Keep max 50 alerts in DOM
    while (feed.children.length > 50) {
        feed.removeChild(feed.lastChild);
    }

    alertCount++;
    const badge = document.getElementById('alert-count');
    badge.textContent = alertCount;
    if (alertCount > 0) {
        badge.className = 'badge running';
    }
}

// ══════════════════════════════════════
// Scratchpad
// ══════════════════════════════════════

function highlightKeywords(text) {
    // Highlight collusion-related keywords
    return text
        .replace(/\b(profit|profitable|profiting|profited)\b/gi, '<span class="kw-profit">$1</span>')
        .replace(/\b(undercut|undercutting|lower|reduce)\b/gi, '<span class="kw-undercut">$1</span>')
        .replace(/\b(price|pricing|priced|charge|charged)\b/gi, '<span class="kw-price">$1</span>')
        .replace(/\b(coordinat|collu|cooperat|signal|stable|maintain|sustain|tacit|mutual)\w*/gi, '<span class="kw-coord">$&</span>');
}

function updateScratchpad(firmId) {
    const content = document.getElementById('scratchpad-content');
    const text = scratchpadData[firmId];
    if (text) {
        content.innerHTML = highlightKeywords(escapeHtml(text));
        content.scrollTop = content.scrollHeight;
    } else {
        content.innerHTML = '<span class="scratchpad-empty">No scratchpad data for this firm yet.</span>';
    }
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function initScratchpadTabs() {
    const tabs = document.querySelectorAll('.scratchpad-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeScratchpadFirm = parseInt(tab.dataset.firm);
            updateScratchpad(activeScratchpadFirm);
        });
    });
}

// ══════════════════════════════════════
// Progress Bar
// ══════════════════════════════════════

function updateProgress(current, total) {
    const pct = total > 0 ? (current / total) * 100 : 0;
    document.getElementById('progress-fill').style.width = `${pct}%`;
}

// ══════════════════════════════════════
// Demand Shock
// ══════════════════════════════════════

async function triggerShock() {
    const firmId = document.getElementById('shock-firm').value;
    const btn = document.getElementById('shock-btn');
    btn.disabled = true;
    btn.textContent = 'Shocking...';

    try {
        const res = await fetch(`/api/simulation/shock/${firmId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intensity: 0.3 }),
        });
        const data = await res.json();

        if (data.error) {
            alert('Shock failed: ' + data.error);
        } else {
            // Show shock badge
            const status = document.getElementById('shock-status');
            const badge = document.createElement('span');
            badge.className = 'shock-badge';
            badge.innerHTML = `<span class="shock-icon">⚡</span> Firm ${parseInt(firmId) + 1} shocked at Round ${data.event.round}`;
            status.appendChild(badge);

            // Flash effect
            document.querySelector('.app-container').classList.add('shock-active');
            setTimeout(() => {
                document.querySelector('.app-container').classList.remove('shock-active');
            }, 1000);

            // Add annotation to charts
            addShockAnnotation(data.event.round, parseInt(firmId));

            // Add alert
            addAlert(data.event.round, 'alert', `⚡ Demand shock applied to Firm ${parseInt(firmId) + 1} (quality −30%)`);
        }
    } catch (err) {
        alert('Failed to send shock: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '⚡ Trigger Shock (−30%)';
    }
}

function addShockAnnotation(round, firmId) {
    const annotId = `shock_${round}`;
    const annotation = {
        type: 'line',
        xMin: round,
        xMax: round,
        borderColor: 'rgba(239, 68, 68, 0.7)',
        borderWidth: 2,
        borderDash: [3, 3],
        label: {
            content: `⚡ F${firmId + 1}`,
            display: true,
            position: 'start',
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            color: '#ef4444',
            font: { size: 10, weight: 'bold' },
        },
    };

    // Add to both charts
    priceChart.options.plugins.annotation.annotations[annotId] = annotation;
    priceChart.update('none');

    lambdaChart.options.plugins.annotation.annotations[annotId] = { ...annotation };
    lambdaChart.update('none');

    shockAnnotations.push(round);
}

// ══════════════════════════════════════
// Summary Overlay
// ══════════════════════════════════════

function showSummary(data, regulator) {
    const overlay = document.getElementById('summary-overlay');
    const lambda = data.converged_collusion_index || data.final_collusion_index || 0;
    let verdictClass = 'competitive';
    let verdictText = '✅ COMPETITIVE — No significant collusion detected';
    if (lambda >= 0.7) {
        verdictClass = 'collusion';
        verdictText = '🚨 COLLUSION DETECTED — Coordinated pricing observed';
    } else if (lambda >= 0.3) {
        verdictClass = 'suspicious';
        verdictText = '⚠️ SUSPICIOUS — Potential coordination patterns';
    }

    overlay.innerHTML = `
        <div class="summary-card">
            <h2>Simulation <span>Complete</span></h2>
            <div class="summary-stats">
                <div class="summary-stat">
                    <span class="s-label">Rounds</span>
                    <span class="s-value">${data.rounds_completed}</span>
                </div>
                <div class="summary-stat">
                    <span class="s-label">Final Λ</span>
                    <span class="s-value" style="color:${lambda >= 0.7 ? '#ef4444' : lambda >= 0.3 ? '#f59e0b' : '#10b981'}">${lambda.toFixed(3)}</span>
                </div>
                <div class="summary-stat">
                    <span class="s-label">Peak Λ</span>
                    <span class="s-value">${(data.peak_collusion_index || 0).toFixed(3)}</span>
                </div>
                <div class="summary-stat">
                    <span class="s-label">Convergence</span>
                    <span class="s-value">${data.convergence_round || 'Never'}</span>
                </div>
                <div class="summary-stat">
                    <span class="s-label">Nash Price</span>
                    <span class="s-value">$${(data.nash_price || 0).toFixed(2)}</span>
                </div>
                <div class="summary-stat">
                    <span class="s-label">Final Avg Price</span>
                    <span class="s-value">$${(data.final_avg_price || 0).toFixed(2)}</span>
                </div>
            </div>
            ${regulator ? `
                <div class="summary-stats" style="margin-top:0;">
                    <div class="summary-stat">
                        <span class="s-label">Total Alerts</span>
                        <span class="s-value">${regulator.total_alerts}</span>
                    </div>
                    <div class="summary-stat">
                        <span class="s-label">Trend</span>
                        <span class="s-value" style="font-size:1rem;">${regulator.trend || '—'}</span>
                    </div>
                </div>
            ` : ''}
            <div class="summary-verdict ${verdictClass}">${verdictText}</div>
            <button class="primary-btn summary-close" onclick="closeSummary()">Close</button>
        </div>
    `;
    overlay.classList.remove('hidden');
}

function closeSummary() {
    document.getElementById('summary-overlay').classList.add('hidden');
}

// ══════════════════════════════════════
// Simulation Control
// ══════════════════════════════════════

const MAX_CHART_POINTS = 600;

function pushChartData(chart, label, dataArrays) {
    chart.data.labels.push(label);
    if (chart.data.labels.length > MAX_CHART_POINTS) {
        chart.data.labels.shift();
    }
    dataArrays.forEach((val, idx) => {
        chart.data.datasets[idx].data.push(val);
        if (chart.data.datasets[idx].data.length > MAX_CHART_POINTS) {
            chart.data.datasets[idx].data.shift();
        }
    });
}

function resetUI() {
    currentRound = 0;
    alertCount = 0;
    prevProfits = null;
    scratchpadData = {};
    shockAnnotations = [];

    document.getElementById('current-round').textContent = '0';
    document.getElementById('current-avg-price').textContent = '$0.00';
    updateGauge(0);
    updateProgress(0, 1);

    document.getElementById('alerts-feed').innerHTML = '<div class="empty-state">No alerts triggered yet.</div>';
    document.getElementById('alert-count').textContent = '0';
    document.getElementById('alert-count').className = 'badge idle';
    document.getElementById('shock-status').innerHTML = '';

    // Reset scratchpad
    document.getElementById('scratchpad-content').innerHTML =
        '<span class="scratchpad-empty">Start an LLM simulation to see agent reasoning here.</span>';

    // Reset charts
    priceChart.data.labels = [];
    priceChart.data.datasets.forEach(ds => (ds.data = []));
    priceChart.options.plugins.annotation.annotations = {};
    priceChart.update();

    lambdaChart.data.labels = [];
    lambdaChart.data.datasets[0].data = [];
    // Preserve threshold annotations but remove shock annotations
    const lamAnnotations = lambdaChart.options.plugins.annotation.annotations;
    Object.keys(lamAnnotations).forEach(k => {
        if (k.startsWith('shock_')) delete lamAnnotations[k];
    });
    lambdaChart.update();

    // Reset firm table
    initFirmTable();

    // Status
    const badge = document.getElementById('status-badge');
    badge.className = 'badge running';
    badge.textContent = 'Running…';
}

function handleMessage(msg) {
    if (msg.type === 'benchmarks') {
        document.getElementById('nash-price').textContent = `$${msg.nash_price.toFixed(2)}`;
        document.getElementById('monopoly-price').textContent = `$${msg.monopoly_price.toFixed(2)}`;

        priceChart.options.scales.y.min = msg.price_floor;
        priceChart.options.scales.y.max = msg.price_ceiling;
        priceChart.update();

        window._nash = msg.nash_price;
        window._mono = msg.monopoly_price;
        return;
    }

    if (msg.type === 'round') {
        currentRound = msg.round;
        document.getElementById('current-round').textContent = msg.round;
        document.getElementById('current-avg-price').textContent = `$${msg.avg_price.toFixed(2)}`;
        updateGauge(msg.lambda);
        updateProgress(msg.round, totalRounds);

        // Price chart
        const priceData = [...msg.prices, window._nash, window._mono];
        pushChartData(priceChart, msg.round, priceData);
        priceChart.update('none');

        // Lambda chart — dynamically color the line
        lambdaChart.data.labels.push(msg.round);
        if (lambdaChart.data.labels.length > MAX_CHART_POINTS) lambdaChart.data.labels.shift();
        lambdaChart.data.datasets[0].data.push(msg.lambda);
        if (lambdaChart.data.datasets[0].data.length > MAX_CHART_POINTS) lambdaChart.data.datasets[0].data.shift();

        // Color the lambda line by current severity
        if (msg.lambda >= 0.7) {
            lambdaChart.data.datasets[0].borderColor = '#ef4444';
        } else if (msg.lambda >= 0.3) {
            lambdaChart.data.datasets[0].borderColor = '#f59e0b';
        } else {
            lambdaChart.data.datasets[0].borderColor = '#3b82f6';
        }
        lambdaChart.update('none');

        // Firm table
        if (msg.profits && msg.shares) {
            updateFirmTable(msg.prices, msg.profits, msg.shares);
        }

        // Alerts
        if (msg.alerts && msg.alerts.length > 0) {
            msg.alerts.forEach(a => addAlert(msg.round, a.type, a.detail));
        }

        // Scratchpads
        if (msg.scratchpads) {
            Object.entries(msg.scratchpads).forEach(([fid, text]) => {
                scratchpadData[parseInt(fid)] = text;
            });
            updateScratchpad(activeScratchpadFirm);
        }

        // Shock events from server
        if (msg.shocks && msg.shocks.length > 0) {
            msg.shocks.forEach(s => {
                addShockAnnotation(s.round, s.firm_id);
            });
        }
        return;
    }

    if (msg.type === 'summary') {
        const badge = document.getElementById('status-badge');
        badge.className = 'badge done';
        badge.textContent = 'Completed';

        document.getElementById('start-btn').disabled = false;
        document.getElementById('shock-btn').disabled = true;
        isRunning = false;

        showSummary(msg.data, msg.regulator);
        return;
    }

    if (msg.type === 'error') {
        const badge = document.getElementById('status-badge');
        badge.className = 'badge error';
        badge.textContent = 'Error';

        document.getElementById('start-btn').disabled = false;
        document.getElementById('shock-btn').disabled = true;
        isRunning = false;

        alert('Simulation Error: ' + msg.message);
        return;
    }
}

function startSimulation() {
    if (isRunning) return;

    const mode = document.getElementById('agent-mode').value;
    const rounds = parseInt(document.getElementById('rounds').value);
    totalRounds = rounds;

    isRunning = true;
    document.getElementById('start-btn').disabled = true;
    document.getElementById('shock-btn').disabled = false;

    // Show/hide scratchpad panel based on mode
    const spPanel = document.getElementById('scratchpad-panel');
    const spBadge = document.getElementById('scratchpad-mode-badge');
    if (mode === 'llm' || mode === 'rag') {
        spPanel.classList.remove('hidden');
        spBadge.textContent = mode === 'rag' ? 'RAG Mode' : 'LLM Mode';
        spBadge.className = 'badge running';
    } else {
        spPanel.classList.add('hidden');
    }

    resetUI();

    // Connect WebSocket
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${window.location.host}/ws/simulate`;
    ws = new WebSocket(url);

    ws.onopen = () => {
        ws.send(JSON.stringify({ mode, rounds }));
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
    };

    ws.onerror = () => {
        alert('Failed to connect to simulation server.\nMake sure the API server is running: python api_server.py');
        document.getElementById('start-btn').disabled = false;
        document.getElementById('shock-btn').disabled = true;
        isRunning = false;

        const badge = document.getElementById('status-badge');
        badge.className = 'badge error';
        badge.textContent = 'Connection Error';
    };

    ws.onclose = () => {
        if (isRunning) {
            // Unexpected close
            const badge = document.getElementById('status-badge');
            if (badge.textContent === 'Running…') {
                badge.className = 'badge error';
                badge.textContent = 'Disconnected';
            }
            document.getElementById('start-btn').disabled = false;
            document.getElementById('shock-btn').disabled = true;
            isRunning = false;
        }
    };
}

// ══════════════════════════════════════
// Validation Data
// ══════════════════════════════════════

async function loadValidationData() {
    const btn = document.getElementById('load-validation');
    btn.textContent = 'Loading…';
    btn.disabled = true;

    try {
        const res = await fetch('/api/validation');
        const data = await res.json();

        if (data.error) {
            alert(data.error);
            btn.textContent = 'Load Data';
            btn.disabled = false;
            return;
        }

        document.getElementById('validation-content').classList.remove('hidden');
        document.getElementById('val-gas').textContent = data.gasoline.mean_lambda.toFixed(3);
        document.getElementById('val-amz').textContent = data.amazon.mean_lambda.toFixed(3);
        document.getElementById('val-note').textContent = data.comparison.conclusion;
        btn.style.display = 'none';
    } catch (err) {
        console.error(err);
        alert('Error loading validation data.');
        btn.textContent = 'Load Data';
        btn.disabled = false;
    }
}

// ══════════════════════════════════════
// Initialization
// ══════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initFirmTable();
    initScratchpadTabs();

    document.getElementById('start-btn').addEventListener('click', startSimulation);
    document.getElementById('load-validation').addEventListener('click', loadValidationData);
    document.getElementById('shock-btn').addEventListener('click', triggerShock);

    // Hide scratchpad panel initially
    document.getElementById('scratchpad-panel').classList.add('hidden');

    // Smart round defaults based on mode
    document.getElementById('agent-mode').addEventListener('change', (e) => {
        const roundsInput = document.getElementById('rounds');
        switch (e.target.value) {
            case 'dummy': roundsInput.value = 100; break;
            case 'rl':    roundsInput.value = 5000; break;
            case 'llm':   roundsInput.value = 10; break;
        }
    });
});
