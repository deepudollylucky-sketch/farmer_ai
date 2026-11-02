# Fieldwise: Smart Farmer Assistant

A Hassan, Karnataka focused prototype for crop price prediction, weather analysis, market comparison, and high-trading crop signals.

## What is included

- `data/market_prices.csv` is the single local dataset used by the application.
- A Random Forest model learns price movement from the dataset's date, rainfall, temperature, and humidity columns.
- The decision engine compares Hassan APMC, Belur, Arasikere, and Channarayapatna using:
  `net return = selling value - transport cost - other costs`.
- Weather is a deterministic local fixture for the demo, so it runs without API keys.
- The responsive frontend is a chatbot-style harvest analysis workspace.

## Run on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The default scenario is 10 quintals of tomato in Hassan. Try onion or potato from the crop selector.

## Dataset

The CSV is intentionally small and explainable for a project demonstration. Replace it with a larger Hassan market export using the same columns when real data is available. The current rows are local demo observations, not a live government feed.
