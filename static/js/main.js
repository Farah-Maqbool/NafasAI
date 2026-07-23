// ── Auth helpers ────────────────────────────────
function getToken() {
  return localStorage.getItem('nafasai_token');
}

function getUser() {
  const u = localStorage.getItem('nafasai_user');
  return u ? JSON.parse(u) : null;
}

function logout() {
  localStorage.removeItem('nafasai_token');
  localStorage.removeItem('nafasai_user');
  window.location.href = '/login';
}

// ── Auth guard ──────────────────────────────────
function checkAuth() {
  const token = getToken();
  const user  = getUser();
  if (!token || !user) {
    window.location.href = '/login';
    return false;
  }

  // Pre-fill city and profile from saved preferences
  document.getElementById('city-select').value    = user.default_city || 'karachi';
  document.getElementById('profile-select').value = user.health_profile || 'general';

  // Show personalized greeting in header
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('last-updated').textContent = `${greeting}, ${user.name}`;

  return true;
}

let forecastChart  = null;
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

function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>)+/g, match => `<ul>${match}</ul>`)
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

const ALL_CITIES = ['karachi', 'lahore', 'islamabad', 'peshawar', 'quetta', 'faisalabad', 'multan'];

async function loadDashboard() {
  try {
    const res  = await fetch('/api/dashboard');
    const data = await res.json();
    const user = getUser();
    const defaultCity = user?.default_city || 'karachi';
    const container = document.getElementById('city-cards-container');

    container.innerHTML = '';

    ALL_CITIES.forEach(city => {
      const d   = data[city];
      if (!d || !d.success) return;
      const cls = categoryClass(d.category);
      const isDefault = city === defaultCity;

      const card = document.createElement('div');
      card.className = `city-card ${cls} ${isDefault ? 'default-city' : ''}`;
      card.id = `card-${city}`;
      card.innerHTML = `
        <div class="city-name">
          ${city.charAt(0).toUpperCase() + city.slice(1)}
          ${isDefault ? '<span class="default-badge">Your City</span>' : ''}
        </div>
        <div class="aqi-value">${aqiFromPm25(d.pm25)}</div>
        <div class="aqi-label">AQI</div>
        <div class="pm25-value">PM2.5: ${d.pm25} μg/m³</div>
        <div class="category-badge ${cls}">${d.category}</div>
        <div class="pollutants">
          PM10: ${d.pm10 ?? '--'} μg/m³<br>
          Ozone: ${d.ozone ?? '--'} μg/m³<br>
          NO₂: ${d.nitrogen_dioxide ?? '--'} μg/m³
        </div>
      `;
      container.appendChild(card);
    });

    const now = new Date().toLocaleTimeString('en-PK', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('last-updated').textContent = `Last updated: ${now}`;
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}

// ── Forecast ───────────────────────────────────
async function loadForecast(city) {
  try {
    const res  = await fetch(`/api/forecast/${city}`);
    const data = await res.json();

    if (!data.success) {
      document.getElementById('forecast-summary').textContent = data.error || 'Unavailable';
      return;
    }

    const current   = data.current_pm25;
    const predicted = data.predicted_pm25_24h;
    const labels    = ['Now', '+3h', '+6h', '+9h', '+12h', '+18h', '+24h'];
    const points    = labels.map((_, i) => {
      const t = i / (labels.length - 1);
      return Math.round((current + (predicted - current) * t) * 10) / 10;
    });
    const color = categoryColor(data.forecast_category);

    document.getElementById('forecast-summary').textContent =
      `Now: ${current} μg/m³ → 24h: ${predicted} μg/m³ (${data.forecast_category})`;

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
          y: {
            ticks: { color: '#8b90a8' },
            grid:  { color: '#2e3248' },
            title: { display: true, text: 'PM2.5 μg/m³', color: '#8b90a8' }
          },
        },
      },
    });
  } catch (e) {
    console.error('Forecast error:', e);
  }
}

// ── Trend ──────────────────────────────────────
async function loadTrend(city) {
  try {
    const res  = await fetch(`/api/trend/${city}`);
    const data = await res.json();
    const summary = document.getElementById('trend-summary');
    const stats   = document.getElementById('trend-stats');

    if (!data.success || data.total_readings === 0) {
      summary.textContent = data.message || 'No historical data yet.';
      stats.innerHTML = '';
      return;
    }

    summary.textContent = data.message;
    stats.innerHTML = `
      <div class="stat-box">
        <div class="stat-label">Average</div>
        <div class="stat-value">${data.average_pm25}</div>
        <div style="font-size:0.7rem;color:#8b90a8">μg/m³</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Maximum</div>
        <div class="stat-value">${data.maximum_pm25}</div>
        <div style="font-size:0.7rem;color:#8b90a8">μg/m³</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Minimum</div>
        <div class="stat-value">${data.minimum_pm25}</div>
        <div style="font-size:0.7rem;color:#8b90a8">μg/m³</div>
      </div>
    `;
  } catch (e) {
    console.error('Trend error:', e);
  }
}

// ── Health ─────────────────────────────────────
async function loadHealth(city, profile) {
  try {
    const aqi  = await fetch('/api/dashboard').then(r => r.json());
    const pm25 = aqi[city]?.pm25 ?? 0;
    const fc   = await fetch(`/api/forecast/${city}`).then(r => r.json());
    const forecast_pm25 = fc.predicted_pm25_24h ?? null;

    const body = await fetch('/api/health', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ pm25, forecast_pm25, profile }),
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

// ── Chat ───────────────────────────────────────
async function sendMessage() {
  const input    = document.getElementById('chat-input');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  appendMessage(question, 'user');
  const thinking = appendMessage('NafasAI is thinking...', 'bot thinking');

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question, city: selectedCity, profile: selectedProfile }),
    });
    const data = await res.json();
    thinking.remove();

    if (data.success && data.answer) {
      appendMessage(data.answer, 'bot');
    } else {
      appendMessage(data.error || 'NafasAI is temporarily unavailable. Please try again.', 'bot');
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

  const isUser = type.includes('user');
  const avatar = isUser ? '👤' : '🌬️';
  const formatted = isUser ? text : formatMarkdown(text);

  div.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-bubble">${formatted}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function useSuggestion(btn) {
  document.getElementById('chat-input').value = btn.textContent;
  sendMessage();
}

// ── Update chat context labels ─────────────────
function updateChatContext() {
  document.getElementById('chat-city-label').textContent =
    selectedCity.charAt(0).toUpperCase() + selectedCity.slice(1);
  document.getElementById('chat-profile-label').textContent =
    document.getElementById('profile-select').options[
      document.getElementById('profile-select').selectedIndex
    ].text;
}

// ── Load all ───────────────────────────────────
async function loadAll() {
  selectedCity    = document.getElementById('city-select').value;
  selectedProfile = document.getElementById('profile-select').value;
  updateChatContext();

  await Promise.all([
    loadDashboard(),
    loadForecast(selectedCity),
    loadTrend(selectedCity),
    loadHealth(selectedCity, selectedProfile),
  ]);
}

async function saveDefaults() {
  const token = getToken();
  if (!token) return;

  const btn = document.querySelector('.btn-save-default');
  btn.textContent = 'Saving...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/save-defaults', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        city:           selectedCity,
        health_profile: selectedProfile
      })
    });
    const data = await res.json();

    if (data.success) {
      // Update localStorage so next refresh uses new defaults
      const user = getUser();
      user.default_city   = selectedCity;
      user.health_profile = selectedProfile;
      localStorage.setItem('nafasai_user', JSON.stringify(user));

      btn.textContent = '✓ Saved';
      btn.classList.add('saved');

      // Reset button after 2 seconds
      setTimeout(() => {
        btn.textContent = '💾 Save as Default';
        btn.classList.remove('saved');
        btn.disabled = false;
      }, 2000);
    } else {
      btn.textContent = '💾 Save as Default';
      btn.disabled = false;
    }
  } catch (e) {
    btn.textContent = '💾 Save as Default';
    btn.disabled = false;
  }
}

// ── Listeners ──────────────────────────────────
document.getElementById('city-select').addEventListener('change', loadAll);
document.getElementById('profile-select').addEventListener('change', loadAll);

// ── Init ───────────────────────────────────────
if (checkAuth()) {
  loadAll();
  setInterval(loadAll, 5 * 60 * 1000);
}