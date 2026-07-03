// ── State ──────────────────────────────────────
let forecastChart = null;
let selectedCity    = 'karachi';
let selectedProfile = 'general';

// ── Helpers ────────────────────────────────────
function categoryClass(category) {
  if (!category) return '';
  const c = category.toLowerCase();
  if (c.includes('good'))      return 'good';
  if (c.includes('moderate'))  return 'moderate';
  if (c.includes('sensitive')) return 'sensitive';
  if (c.includes('unhealthy')) return 'unhealthy';
  if (c.includes('hazardous')) return 'hazardous';
  return '';
}

function categoryColor(category) {
  const map = {
    good:      '#22c55e',
    moderate:  '#eab308',
    sensitive: '#f97316',
    unhealthy: '#ef4444',
    hazardous: '#a855f7',
  };
  return map[categoryClass(category)] || '#4f9cf9';
}

function aqiFromPm25(pm25) {
  if (pm25 == null) return '--';
  if (pm25 <= 12.0)  return Math.round((50 / 12.0) * pm25);
  if (pm25 <= 35.4)  return Math.round(50  + (50  / 23.4) * (pm25 - 12.0));
  if (pm25 <= 55.4)  return Math.round(100 + (50  / 20.0) * (pm25 - 35.4));
  if (pm25 <= 150.4) return Math.round(150 + (50  / 94.9) * (pm25 - 55.4));
  if (pm25 <= 250.4) return Math.round(200 + (100 / 99.9) * (pm25 - 150.4));
  return 300;
}

function now() {
  return new Date().toLocaleTimeString('en-PK', { hour: '2-digit', minute: '2-digit' });
}

// ── Dashboard: All 3 city cards ────────────────
async function loadDashboard() {
  try {
    const res  = await fetch('/api/dashboard');
    const data = await res.json();

    ['karachi', 'lahore', 'islamabad'].forEach(city => {
      const d   = data[city];
      const cls = categoryClass(d.category);

      // Card colour strip
      const card = document.getElementById(`card-${city}`);
      card.className = `city-card ${cls}`;

      // AQI
      document.getElementById(`aqi-${city}`).textContent = aqiFromPm25(d.pm25);

      // PM2.5
      document.getElementById(`pm25-${city}`).textContent = `PM2.5: ${d.pm25} μg/m³`;

      // Category badge
      const badge = document.getElementById(`cat-${city}`);
      badge.textContent = d.category;
      badge.className   = `category-badge ${cls}`;

      // Pollutants
      document.getElementById(`pol-${city}`).innerHTML = `
        PM10: ${d.pm10 ?? '--'} μg/m³<br>
        Ozone: ${d.ozone ?? '--'} μg/m³<br>
        NO₂: ${d.nitrogen_dioxide ?? '--'} μg/m³
      `;
    });

    document.getElementById('last-updated').textContent = `Last updated: ${now()}`;
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}

// ── Forecast chart ──────────────────────────────
async function loadForecast(city) {
  try {
    const res  = await fetch(`/api/forecast/${city}`);
    const data = await res.json();

    if (!data.success) {
      document.getElementById('forecast-summary').textContent = data.error;
      return;
    }

    const current   = data.current_pm25;
    const predicted = data.predicted_pm25_24h;
    const labels    = ['Now', '+3h', '+6h', '+9h', '+12h', '+18h', '+24h'];

    // Interpolate smooth curve between current and predicted
    const points = labels.map((_, i) => {
      const t = i / (labels.length - 1);
      return Math.round((current + (predicted - current) * t) * 10) / 10;
    });

    const color = categoryColor(data.forecast_category);

    document.getElementById('forecast-summary').textContent =
      `Current: ${current} μg/m³ → Predicted in 24h: ${predicted} μg/m³ (${data.forecast_category})`;

    if (forecastChart) forecastChart.destroy();

    const ctx = document.getElementById('forecastChart').getContext('2d');
    forecastChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'PM2.5 (μg/m³)',
          data: points,
          borderColor: color,
          backgroundColor: color + '22',
          borderWidth: 2.5,
          pointBackgroundColor: color,
          pointRadius: 4,
          fill: true,
          tension: 0.4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#8b90a8' }, grid: { color: '#2e3248' } },
          y: { ticks: { color: '#8b90a8' }, grid: { color: '#2e3248' },
               title: { display: true, text: 'PM2.5 μg/m³', color: '#8b90a8' } },
        },
      },
    });
  } catch (e) {
    console.error('Forecast error:', e);
  }
}

// ── Trend stats ─────────────────────────────────
async function loadTrend(city) {
  try {
    const res  = await fetch(`/api/trend/${city}`);
    const data = await res.json();

    const summary = document.getElementById('trend-summary');
    const stats   = document.getElementById('trend-stats');

    if (!data.success || data.total_readings === 0) {
      summary.textContent = data.message || 'No historical data yet — check back soon.';
      stats.innerHTML = '';
      return;
    }

    summary.textContent = data.message;
    stats.innerHTML = `
      <div class="stat-box">
        <div class="stat-label">7-Day Average</div>
        <div class="stat-value">${data.average_pm25}</div>
        <div style="font-size:0.72rem;color:#8b90a8">μg/m³</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">7-Day Max</div>
        <div class="stat-value">${data.maximum_pm25}</div>
        <div style="font-size:0.72rem;color:#8b90a8">μg/m³</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">7-Day Min</div>
        <div class="stat-value">${data.minimum_pm25}</div>
        <div style="font-size:0.72rem;color:#8b90a8">μg/m³</div>
      </div>
    `;
  } catch (e) {
    console.error('Trend error:', e);
  }
}

// ── Health advisory ─────────────────────────────
async function loadHealth(city, profile) {
  try {
    // Get current PM2.5 for health calculation
    const aqi  = await fetch('/api/dashboard').then(r => r.json());
    const pm25 = aqi[city]?.pm25 ?? 0;

    const res  = await fetch('/api/forecast/' + city).then(r => r.json());
    const forecast_pm25 = res.predicted_pm25_24h ?? null;

    const body = await fetch('/api/health', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pm25, forecast_pm25, profile }),
    }).then(r => r.json());

    const el = document.getElementById('health-content');

    if (!body.success) {
      el.innerHTML = `<p class="placeholder">${body.error}</p>`;
      return;
    }

    el.innerHTML = `
      <div class="mask-rec">🧢 ${body.mask_recommendation}</div>
      <ul class="precaution-list">
        ${body.precautions.map(p => `<li>${p}</li>`).join('')}
      </ul>
    `;
  } catch (e) {
    console.error('Health error:', e);
  }
}

// ── Chat ────────────────────────────────────────
async function sendMessage() {
  const input    = document.getElementById('chat-input');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  appendMessage(question, 'user');

  const thinking = appendMessage('NafasAI is thinking...', 'bot thinking');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        city:    selectedCity,
        profile: selectedProfile,
      }),
    });
    const data = await res.json();
    thinking.remove();

    if (data.success) {
      appendMessage(data.answer, 'bot');
    } else {
      appendMessage('Sorry, something went wrong. Please try again.', 'bot');
    }
  } catch (e) {
    thinking.remove();
    appendMessage('Connection error. Please try again.', 'bot');
  }
}

function appendMessage(text, type) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `message ${type}`;
  
  // Convert basic markdown to HTML
  const formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
    .replace(/\*(.*?)\*/g, '<em>$1</em>')               // *italic*
    .replace(/^- (.+)$/gm, '<li>$1</li>')               // - list items
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')          // wrap list
    .replace(/\n/g, '<br>');                             // line breaks

  div.innerHTML = `<div class="message-bubble">${formatted}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

// ── Health route (POST) needs to be added to app.py ──
// We call it here so add this route to Flask:
// @app.route("/api/health", methods=["POST"])

// ── Load all ────────────────────────────────────
async function loadAll() {
  selectedCity    = document.getElementById('city-select').value;
  selectedProfile = document.getElementById('profile-select').value;

  await Promise.all([
    loadDashboard(),
    loadForecast(selectedCity),
    loadTrend(selectedCity),
    loadHealth(selectedCity, selectedProfile),
  ]);
}

// ── City/profile change listeners ───────────────
document.getElementById('city-select').addEventListener('change', loadAll);
document.getElementById('profile-select').addEventListener('change', loadAll);

// ── Init ────────────────────────────────────────
loadAll();
setInterval(loadAll, 5 * 60 * 1000); // auto-refresh every 5 minutes