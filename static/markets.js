const harvestInput = document.getElementById('expected-harvest');
const cultivationInput = document.getElementById('cultivation-cost');
const travelInput = document.getElementById('travel-cost');
const tableBody = document.getElementById('market-table-body');
const summary = document.getElementById('best-market-summary');
const formatMoney = value => `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

function updateMarketEstimates() {
  const harvest = Math.max(0, Number(harvestInput.value) || 0);
  const cultivationCost = Math.max(0, Number(cultivationInput.value) || 0);
  const travelRate = Math.max(0, Number(travelInput.value) || 0);
  const rows = [...tableBody.querySelectorAll('tr')].map((row) => ({
    market: row.dataset.market,
    district: row.dataset.district,
    date: row.dataset.date,
    minPrice: Number(row.dataset.min),
    maxPrice: Number(row.dataset.max),
    price: Number(row.dataset.price),
    distance: Number(row.dataset.distance),
  })).map((row) => ({
    ...row,
    travel: row.distance * travelRate * 2,
    net: harvest * row.price - cultivationCost - row.distance * travelRate * 2,
  })).sort((first, second) => second.net - first.net);

  const winner = rows[0];
  const bestPrice = Math.max(...rows.map((row) => row.price));
  summary.innerHTML = winner
    ? `Highest estimated net profit using approximate straight-line distance: <strong>${formatMoney(winner.net)}</strong> at <strong>${winner.market}</strong>.`
    : 'No district market data is available.';

  tableBody.innerHTML = rows.map((row) => `
    <tr class="${row === winner ? 'best-row' : ''}">
      <td>${row.market}</td>
      <td>${row.district}</td>
      <td>${row.date}</td>
      <td>${formatMoney(row.minPrice)}</td>
      <td>${formatMoney(row.maxPrice)}</td>
      <td>${formatMoney(row.price)}${row.price === bestPrice ? '<span class="table-badge">★ Best price</span>' : ''}</td>
      <td>${row.distance.toFixed(1)}</td>
      <td>${formatMoney(row.travel)}</td>
      <td>${formatMoney(row.net)}${row === winner ? '<span class="table-badge profit-badge">★ Best estimated profit</span>' : ''}</td>
    </tr>
  `).join('');
}

[harvestInput, cultivationInput, travelInput].forEach((input) => {
  input.addEventListener('input', updateMarketEstimates);
});

updateMarketEstimates();