# 🌬️ NafasAI

> An AI-powered air quality decision assistant for Pakistan — built for the Gen AI Academy APAC Cohort 2 Hackathon.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Cloud%20Run-4f9cf9?style=for-the-badge)](https://nafasai-615016998122.us-central1.run.app)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)](https://python.org)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-BigQuery%20%7C%20Cloud%20Run-orange?style=for-the-badge)](https://cloud.google.com)

---

## 🧠 What is NafasAI?

Every morning, millions of people in Pakistan step outside without knowing if the air is safe to breathe. Parents send children to school, asthma patients go to work, and families plan outdoor activities — all without knowing what the air is doing to their health that day.

**NafasAI solves this.**

Instead of showing raw numbers like PM2.5 and AQI and leaving you to figure out what they mean, NafasAI lets you ask in plain language:

> *"Is it safe for my asthmatic daughter to play outside this evening in Karachi?"*

And gives you a direct, personalized answer grounded in real live data — in English or Urdu.

---

## 🏙️ Cities Covered

| City | Coordinates |
|---|---|
| Karachi | 24.86°N, 67.01°E |
| Lahore | 31.55°N, 74.35°E |
| Islamabad | 33.72°N, 73.06°E |

---

## ✨ Features

- **Live AQI Dashboard** — Real-time PM2.5, PM10, Ozone, NO₂ for all three cities
- **24h AI Forecast** — XGBoost model predicts PM2.5 24 hours ahead
- **Natural Language Chat** — Ask anything in English or Urdu, powered by Gemini + ADK
- **Health Advisory** — Personalized advice for asthma, children, elderly, pregnant, heart disease, outdoor exercise profiles
- **7-Day Historical Trend** — Powered by BigQuery data collected hourly via GitHub Actions
- **GPU-Accelerated Analytics** — NVIDIA RAPIDS (cuDF) delivers 10.81x speedup over pandas at 1M rows

---

## 🏗️ Architecture

```
Open-Meteo Historical API          Open-Meteo Live API
(2024–2026, 65K rows)              (called at query time)
        │                                   │
        ▼                                   ▼
  XGBoost Training              Current reading + 48h history
  (per city model)              for forecast model
        │                                   │
        ▼                                   ▼
  city_models.pkl               24h PM2.5 prediction
                                            │
GitHub Actions (hourly)                     ▼
        │                         Gemini ADK Agent
        ▼                         (4 tools orchestrated)
   BigQuery                                 │
   (historical trend)                       ▼
        │                         Flask App (Cloud Run)
        └──────────────────────────────────►│
                                            ▼
                                    User gets answer
```

---

## 🛠️ Tech Stack

### Google Cloud
| Service | Purpose |
|---|---|
| **BigQuery** | Stores hourly air quality readings for trend analytics |
| **Cloud Run** | Hosts the Flask web application |
| **Cloud Build** | Builds and deploys Docker container |
| **Gemini 2.5 Flash** | Powers the natural language AI agent |
| **Agent Development Kit (ADK)** | Orchestrates multi-tool agent workflow |

### NVIDIA Acceleration
| Tool | Purpose |
|---|---|
| **NVIDIA RAPIDS (cuDF)** | GPU-accelerated data processing |
| **XGBoost** | GPU-compatible gradient boosting for forecast model |

### Data & ML
| Tool | Purpose |
|---|---|
| **Open-Meteo API** | Real-time and historical air quality data |
| **XGBoost** | Per-city 24h PM2.5 forecast model |
| **scikit-learn** | Model evaluation metrics |
| **pandas / numpy** | Data processing |

---

## ⚡ RAPIDS GPU Benchmark

Processing 500K–1M rows of air quality data using NVIDIA RAPIDS vs pandas:

| Dataset Size | Pandas (CPU) | cuDF (GPU) | Speedup |
|---|---|---|---|
| 10,000 rows | 0.073s | 4.629s | 0.02x (GPU overhead) |
| 100,000 rows | 0.196s | 0.066s | **2.95x** |
| 500,000 rows | 0.879s | 0.131s | **6.72x** |
| 1,000,000 rows | 2.318s | 0.215s | **10.81x** |

> GPU acceleration becomes increasingly critical as NafasAI scales to nationwide, multi-year monitoring.

---

## 🤖 Forecast Model Performance

Separate XGBoost model trained per city on 65,736 real hourly readings (Jan 2024 – Jul 2026):

| City | MAE | RMSE | R² | Note |
|---|---|---|---|---|
| Karachi | 6.99 μg/m³ | 9.79 μg/m³ | 0.35 | Low variance city (σ=12.9) — MAE is primary metric |
| Lahore | 20.52 μg/m³ | 31.30 μg/m³ | 0.69 | High pollution volatility (max 365 μg/m³) |
| Islamabad | 8.64 μg/m³ | 11.63 μg/m³ | 0.70 | Best balanced performance |

---

## 🤖 ADK Agent Tools

The NafasAI agent orchestrates four tools:

| Tool | Purpose |
|---|---|
| `current_aqi` | Fetches live PM2.5, PM10, ozone, CO, NO₂, SO₂ from Open-Meteo |
| `forecast` | Runs XGBoost model on last 48h readings, predicts 24h ahead |
| `trend` | Queries BigQuery for 7-day historical statistics |
| `health` | Maps PM2.5 + user profile to specific health advice |

---

## 📁 Project Structure

```
nafasai-hackathon/
├── app.py                          # Flask web application
├── Dockerfile                      # Container definition for Cloud Run
├── requirements.txt
├── data_pipeline/
│   └── fetch_aqi.py                # Hourly data collection script
├── intelligence/
│   ├── nafasai_agent.py            # ADK agent + ask_nafas() function
│   ├── nafasai_prompt.py           # Agent system prompt
│   ├── session.py                  # ADK session service
│   └── tools/
│       ├── current_aqi.py          # Tool 1: Live AQI
│       ├── forecast.py             # Tool 2: 24h forecast
│       ├── trend.py                # Tool 3: Historical trend
│       └── health.py               # Tool 4: Health advisory
├── modeling/
│   ├── city_models.pkl             # Trained XGBoost models (3 cities)
│   ├── feature_names.pkl           # Feature list used during training
│   └── model_metrics.pkl           # Evaluation metrics per city
├── templates/
│   └── index.html                  # Single-page dashboard UI
├── static/
│   ├── css/style.css
│   └── js/main.js
├── assets/
│   ├── rapids_benchmark.png        # GPU benchmark chart
│   ├── feature_importance.png      # XGBoost feature importance
│   └── actual_vs_predicted.png     # Forecast accuracy chart
└── .github/
    └── workflows/
        └── fetch_aqi.yml           # GitHub Actions hourly scheduler
```

---

## 🚀 Run Locally

### Prerequisites
- Python 3.11+
- Google Cloud SDK authenticated (`gcloud auth application-default login`)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Setup

```bash
# Clone the repo
git clone https://github.com/Farah-Maqbool/-Air-Quality-Health-Risk-Advisor.git
cd -Air-Quality-Health-Risk-Advisor

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GCP_PROJECT_ID=nafasai-hackathon > .env
echo GEMINI_API_KEY=your_key_here >> .env

# Run
python app.py
```

Open **http://localhost:8080** in your browser.

---

## ☁️ Deployment

Deployed on **Google Cloud Run** via Docker container:

```bash
gcloud run deploy nafasai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars GCP_PROJECT_ID=nafasai-hackathon,GEMINI_API_KEY=your_key
```

**Live URL:** https://nafasai-615016998122.us-central1.run.app

---

## 📊 Data Pipeline

Hourly air quality data is automatically collected via **GitHub Actions** and stored in BigQuery:

- **Source:** Open-Meteo Air Quality API (free, no key required)
- **Fields:** PM2.5, PM10, CO, NO₂, SO₂, Ozone, Dust, UV Index, AQI (calculated)
- **Schedule:** Every hour, 24/7, fully cloud-based (no local machine needed)
- **Storage:** Google BigQuery — `nafasai-hackathon.air_quality.karachi_readings`

---

## 👩‍💻 Author

**Farah Maqbool**
[GitHub](https://github.com/Farah-Maqbool)