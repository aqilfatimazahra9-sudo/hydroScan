// static/js/charts.js
const MAX_POINTS = 30; // fenêtre glissante de 30 points

// Config commune pour tous les graphiques
const baseConfig = (label, color) => ({
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label,
      data: [],
      borderColor: color,
      backgroundColor: color + '18',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      fill: true,
    }]
  },
  options: {
    animation: false,          // désactivé pour le refresh 2s
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index', intersect: false,
        callbacks: { label: ctx => ` ${ctx.parsed.y}` }
      }
    },
    scales: {
      x: { ticks: { color: '#9aa0a6', maxTicksLimit: 6, font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { ticks: { color: '#9aa0a6', font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: 'rgba(255,255,255,0.06)' } }
    }
  }
});

const charts = {
  temp:       new Chart(document.getElementById('chart-temp'),       baseConfig('Temp °C',    '#00d4ff')),
  pression:   new Chart(document.getElementById('chart-pression'),   baseConfig('Pression bar','#7b61ff')),
  debit:      new Chart(document.getElementById('chart-debit'),      baseConfig('Débit Nm³/h','#00e676')),
  conversion: new Chart(document.getElementById('chart-conversion'), baseConfig('Conversion %','#ffb300')),
};

// Mise à jour des 4 charts d'un coup
function updateCharts(data) {
  const time = new Date().toLocaleTimeString('fr', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const map = {
    temp: data.temperature,
    pression: data.pression,
    debit: data.debit,
    conversion: data.conversion
  };
  Object.entries(map).forEach(([key, value]) => {
    const c = charts[key];
    c.data.labels.push(time);
    c.data.datasets[0].data.push(value);
    if (c.data.labels.length > MAX_POINTS) {
      c.data.labels.shift();
      c.data.datasets[0].data.shift();
    }
    c.update('none'); // 'none' = pas d'animation entre updates
  });
}