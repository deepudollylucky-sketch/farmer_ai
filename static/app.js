const form = document.getElementById('farm-form');
const results = document.getElementById('results');
const money = value => `₹${Number(value).toLocaleString('en-IN')}`;

function bindSubmissionHandlers() {
  const submitButton = document.getElementById('market-price-btn');

  if (submitButton) {
    submitButton.onclick = null;
    submitButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      submitForm();
    }, { once: false });
  }

  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      submitForm();
    }, { once: false });
  }
}

function renderWeatherCard(weather) {
  const temp = weather?.[0]?.temp_c ?? 35;
  const humidity = weather?.[0]?.humidity_pct ?? 26;
  const rainfall = weather?.[0]?.rainfall_mm ?? 0;
  const condition = weather?.[0]?.condition ?? 'Overcast clouds';

  return `
    <div class="weather-panel">
      <div class="weather-title">Local Weather</div>
      <div class="weather-grid">
        <div class="weather-card">
          <div class="weather-icon large">🌡️</div>
          <div class="weather-value">${temp}° C</div>
          <div class="weather-label">Temperature</div>
        </div>
        <div class="weather-card">
          <div class="weather-icon large">💧</div>
          <div class="weather-value">${humidity}%</div>
          <div class="weather-label">Humidity</div>
        </div>
        <div class="weather-card">
          <div class="weather-icon large">🌧️</div>
          <div class="weather-value">${rainfall} mm</div>
          <div class="weather-label">Rainfall</div>
        </div>
      </div>
      <div class="current-condition">Current condition: <strong>${condition}</strong></div>
    </div>
  `;
}

function renderRecommendationCards(data) {
  const cards = data.recommended_crops.map((item, index) => {
    const label = index === 0 ? 'Best Match' : index === 1 ? 'Second Choice' : 'Third Choice';
    return `
      <div class="recommendation-item">
        <div class="recommendation-header">
          <span class="badge">${label}</span>
        </div>
        <h3 class="crop-name">${item.crop}</h3>
        <p class="crop-note">${item.reason}</p>
        <div class="score-box">
          <span>Recommendation score:</span>
          <strong>${item.score}</strong>
        </div>
        <button type="button" class="secondary-button select-crop" data-crop="${item.crop}">Check Market Prices</button>
      </div>
    `;
  }).join('');

  return `
    <div class="result-card">
      ${renderWeatherCard(data.weather)}
      <div class="section-header-wrap">
        <div class="section-icon">🌱</div>
        <h2>Recommended Crops</h2>
      </div>
      <div class="recommendation-list">${cards}</div>
    </div>
  `;
}

function renderProfitAnalysis(data, selectedCrop) {
  const rows = data.market_rows || [];
  const location = [
    document.getElementById('village').value.trim(),
    document.getElementById('taluk').value.trim(),
    document.getElementById('district').value,
  ].filter(Boolean).join(', ');

  results.innerHTML = `
    <section class="market-final">
      <header class="market-final-header">
        <h2><span aria-hidden="true">📈</span> Karnataka Market Prices</h2>
        <p class="market-crop">${selectedCrop}</p>
        <p class="market-location">Farm location: <strong>${location}</strong></p>
      </header>

      <div class="market-final-content">
        <p class="market-disclaimer"><strong>Note:</strong> Included market prices are demo samples, not live prices. Profit figures are estimates, not guarantees.</p>
        <section class="profit-estimator" aria-labelledby="profit-estimator-title">
          <h3 id="profit-estimator-title">Estimate your profit by market</h3>
          <p>Travel expense and net profit update automatically. Starting harvest and cultivation-cost estimates use your farm area; edit them below.</p>
          <div class="profit-inputs">
            <label>
              <span>Expected total harvest (quintals)</span>
              <input id="expected-harvest" type="number" min="0" step="0.1" value="${(Number(data.land_area || 4.8) * 20).toFixed(1)}">
            </label>
            <label>
              <span>Total cultivation cost (₹)</span>
              <input id="cultivation-cost" type="number" min="0" step="100" value="${Number(data.land_area || 4.8) * 25000}">
            </label>
            <label>
              <span>Transport cost (₹ per km, for the full load)</span>
              <input id="travel-cost" type="number" min="0" step="1" value="25">
            </label>
          </div>
          <p id="best-market-summary" class="best-market-summary" aria-live="polite"></p>
        </section>

        <div class="market-table-scroll">
          <table class="market-table final-market-table">
            <thead>
              <tr>
                <th>Market</th><th>District</th><th>Date</th><th>Min ₹/q</th><th>Max ₹/q</th><th>Modal ₹/q</th>
                <th>Estimated one-way distance (km)</th><th>Estimated travel expense (₹)</th><th>Estimated net profit (₹)</th>
              </tr>
            </thead>
            <tbody id="market-table-body"></tbody>
          </table>
        </div>
        <p class="market-footnote">Distances are approximate. Travel expense assumes a round trip at the entered rate for the full load. Market prices are illustrative demo values; actual prices, transport charges, fees, and profit may differ.</p>
      </div>
    </section>
  `;

  const updateMarketTable = () => {
    const harvest = Math.max(0, Number(document.getElementById('expected-harvest').value) || 0);
    const cultivationCost = Math.max(0, Number(document.getElementById('cultivation-cost').value) || 0);
    const travelRate = Math.max(0, Number(document.getElementById('travel-cost').value) || 0);
    const today = new Date().toLocaleDateString('en-CA');
    const calculated = rows.map((market) => {
      const price = Number(market.price_per_quintal) || 0;
      const travel = Number(market.distance_km) * travelRate * 2;
      const net = harvest * price - cultivationCost - travel;
      return {
        ...market,
        district: market.market.replace(/\s+(APMC|Market)$/i, ''),
        minPrice: Math.round(price * 0.85 / 10) * 10,
        maxPrice: Math.round(price * 1.05 / 10) * 10,
        travel,
        net,
      };
    }).sort((first, second) => second.net - first.net);
    const winner = calculated[0];
    const bestPrice = Math.max(...calculated.map((market) => market.price_per_quintal));

    document.getElementById('best-market-summary').innerHTML = winner
      ? `Highest estimated net profit using approximate straight-line distance: <strong>${money(winner.net)}</strong> at <strong>${winner.market}</strong>.`
      : 'No market price data is available.';
    document.getElementById('market-table-body').innerHTML = calculated.map((market) => `
      <tr class="${market === winner ? 'best-row' : ''}">
        <td>${market.market}</td>
        <td>${market.district}</td>
        <td>${today}</td>
        <td>${money(market.minPrice)}</td>
        <td>${money(market.maxPrice)}</td>
        <td>${money(market.price_per_quintal)}${market.price_per_quintal === bestPrice ? '<span class="table-badge">★ Best price</span>' : ''}</td>
        <td>${Number(market.distance_km).toFixed(1)}</td>
        <td>${money(market.travel)}</td>
        <td>${money(market.net)}${market === winner ? '<span class="table-badge profit-badge">★ Best estimated profit</span>' : ''}</td>
      </tr>
    `).join('');
  };

  ['expected-harvest', 'cultivation-cost', 'travel-cost'].forEach((inputId) => {
    document.getElementById(inputId).addEventListener('input', updateMarketTable);
  });
  updateMarketTable();
}

async function submitForm() {
  results.classList.remove('hidden');
  const payload = {
    crop: document.getElementById('district').value,
    location: document.getElementById('district').value,
    quantity: document.getElementById('land-area').value || 4.8,
    district: document.getElementById('district').value,
    taluk: document.getElementById('taluk').value || 'hassan',
    village: document.getElementById('village').value || 'malali',
    soilType: document.getElementById('soil-type').value,
    waterAvailability: document.getElementById('water-availability').value,
    landArea: document.getElementById('land-area').value || 4.8,
  };

  results.innerHTML = '<div class="loading-state">Checking weather and crop suitability...</div>';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis failed');

    const weatherHtml = renderWeatherCard(data.weather);
    const recommendationHtml = renderRecommendationCards(data);
    results.innerHTML = `${weatherHtml}${recommendationHtml}`;
    results.classList.remove('hidden');

    document.querySelectorAll('.select-crop').forEach((button) => {
      button.addEventListener('click', () => {
        const selectedCrop = button.dataset.crop;
        renderProfitAnalysis(data, selectedCrop);
      });
    });
  } catch (error) {
    results.innerHTML = `<div class="info-card"><p>${error.message}</p></div>`;
    results.classList.remove('hidden');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bindSubmissionHandlers, { once: true });
} else {
  bindSubmissionHandlers();
}
