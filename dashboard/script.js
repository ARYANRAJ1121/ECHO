let ws;
let priceChart;
let isSimulationRunning = false;
let maxRounds = 1000;

// Colors for the 5 agents
const AGENT_COLORS = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#10b981', // green
    '#f59e0b', // yellow
    '#ef4444'  // red
];

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Set global default color for dark mode
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    
    const datasets = [];
    for (let i = 0; i < 5; i++) {
        datasets.push({
            label: `Firm ${i + 1}`,
            data: [],
            borderColor: AGENT_COLORS[i],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        });
    }
    
    // Add lines for benchmarks
    datasets.push({
        label: 'Nash Price',
        data: [],
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderDash: [5, 5],
        borderWidth: 1,
        pointRadius: 0
    });
    
    datasets.push({
        label: 'Monopoly Price',
        data: [],
        borderColor: 'rgba(255, 0, 0, 0.4)',
        borderDash: [5, 5],
        borderWidth: 1,
        pointRadius: 0
    });

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // Turn off for performance during live stream
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, usePointStyle: true }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    title: { display: true, text: 'Round' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    title: { display: true, text: 'Price ($)' },
                    min: 1.0,
                    max: 5.0
                }
            }
        }
    });
}

function resetUI() {
    document.getElementById('current-round').innerText = '0';
    document.getElementById('current-avg-price').innerText = '$0.00';
    updateGauge(0);
    document.getElementById('alerts-feed').innerHTML = '<div class="empty-state">No alerts triggered yet.</div>';
    
    priceChart.data.labels = [];
    priceChart.data.datasets.forEach(ds => ds.data = []);
    priceChart.update();
    
    const badge = document.getElementById('status-badge');
    badge.className = 'badge running';
    badge.innerText = 'Running...';
}

function updateGauge(lambda) {
    const gauge = document.getElementById('lambda-gauge');
    const valueText = document.getElementById('lambda-value');
    
    // SVG path total length is approx 125.6
    const offset = 125.6 * (1 - Math.min(1, Math.max(0, lambda)));
    gauge.style.strokeDashoffset = offset;
    
    valueText.innerText = lambda.toFixed(3);
    
    if (lambda >= 0.7) {
        gauge.style.stroke = 'var(--alert-danger)';
        valueText.className = 'text-orange';
    } else if (lambda >= 0.3) {
        gauge.style.stroke = 'var(--alert-warning)';
        valueText.className = '';
    } else {
        gauge.style.stroke = 'var(--accent-primary)';
        valueText.className = '';
    }
}

function addAlert(round, type, detail) {
    const feed = document.getElementById('alerts-feed');
    
    // Remove empty state if present
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
}

function handleSimulationMessage(msg) {
    if (msg.type === "benchmarks") {
        document.getElementById('nash-price').innerText = `$${msg.nash_price.toFixed(2)}`;
        document.getElementById('monopoly-price').innerText = `$${msg.monopoly_price.toFixed(2)}`;
        
        // Setup chart boundaries
        priceChart.options.scales.y.min = msg.price_floor;
        priceChart.options.scales.y.max = msg.price_ceiling;
        priceChart.update();
        
        // Store for lines
        window.nashPrice = msg.nash_price;
        window.monopolyPrice = msg.monopoly_price;
    }
    else if (msg.type === "round") {
        document.getElementById('current-round').innerText = msg.round;
        document.getElementById('current-avg-price').innerText = `$${msg.avg_price.toFixed(2)}`;
        updateGauge(msg.lambda);
        
        // Update Chart
        priceChart.data.labels.push(msg.round);
        
        // Limit points for performance if very long
        if (priceChart.data.labels.length > 500) {
            priceChart.data.labels.shift();
        }
        
        for (let i = 0; i < 5; i++) {
            priceChart.data.datasets[i].data.push(msg.prices[i]);
            if (priceChart.data.datasets[i].data.length > 500) {
                priceChart.data.datasets[i].data.shift();
            }
        }
        
        // Benchmarks
        priceChart.data.datasets[5].data.push(window.nashPrice);
        if (priceChart.data.datasets[5].data.length > 500) priceChart.data.datasets[5].data.shift();
        
        priceChart.data.datasets[6].data.push(window.monopolyPrice);
        if (priceChart.data.datasets[6].data.length > 500) priceChart.data.datasets[6].data.shift();
        
        priceChart.update();
        
        // Handle Alerts
        if (msg.alerts && msg.alerts.length > 0) {
            msg.alerts.forEach(a => addAlert(msg.round, a.type, a.detail));
        }
    }
    else if (msg.type === "summary") {
        const badge = document.getElementById('status-badge');
        badge.className = 'badge done';
        badge.innerText = 'Completed';
        
        document.getElementById('start-btn').disabled = false;
        isSimulationRunning = false;
    }
    else if (msg.type === "error") {
        alert("Simulation Error: " + msg.message);
        document.getElementById('start-btn').disabled = false;
        isSimulationRunning = false;
        
        const badge = document.getElementById('status-badge');
        badge.className = 'badge idle';
        badge.innerText = 'Error';
    }
}

function startSimulation() {
    if (isSimulationRunning) return;
    
    const mode = document.getElementById('agent-mode').value;
    const rounds = parseInt(document.getElementById('rounds').value);
    
    isSimulationRunning = true;
    document.getElementById('start-btn').disabled = true;
    
    resetUI();
    
    // Connect WS
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/simulate`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        ws.send(JSON.stringify({ mode: mode, rounds: rounds }));
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleSimulationMessage(msg);
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
        alert("Failed to connect to simulation engine.");
        document.getElementById('start-btn').disabled = false;
        isSimulationRunning = false;
    };
}

async function loadValidationData() {
    const btn = document.getElementById('load-validation');
    btn.innerText = 'Loading...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/validation');
        const data = await res.json();
        
        if (data.error) {
            alert(data.error);
            btn.innerText = 'Load Real Data';
            btn.disabled = false;
            return;
        }
        
        document.getElementById('validation-content').classList.remove('hidden');
        document.getElementById('val-gas').innerText = data.gasoline.mean_lambda.toFixed(3);
        document.getElementById('val-amz').innerText = data.amazon.mean_lambda.toFixed(3);
        document.getElementById('val-note').innerText = data.comparison.conclusion;
        
        btn.style.display = 'none'; // hide button once loaded
        
    } catch (err) {
        console.error(err);
        alert("Error loading validation data.");
        btn.innerText = 'Load Real Data';
        btn.disabled = false;
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    document.getElementById('start-btn').addEventListener('click', startSimulation);
    document.getElementById('load-validation').addEventListener('click', loadValidationData);
});
