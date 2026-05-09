// static/js/main.js
const DOM = {
  temp:       document.getElementById('val-temp'),
  pression:   document.getElementById('val-pression'),
  debit:      document.getElementById('val-debit'),
  conversion: document.getElementById('val-conversion'),
  clock:      document.getElementById('clock'),
  offline:    document.getElementById('offline-banner'),
  status:     document.getElementById('status-badge'),
};

// Horloge temps réel
setInterval(() => {
  DOM.clock.textContent = new Date().toLocaleTimeString('fr');
}, 1000);

// Mise à jour des KPI cards
function updateKPIs(data) {
  if (!data) {
    // Serveur offline → afficher "---"
    ['temp','pression','debit','conversion'].forEach(k => {
      DOM[k].textContent = '---';
      DOM[k].classList.add('value-offline');
    });
    DOM.offline.classList.add('show');
    DOM.status.style.opacity = '0.4';
    return;
  }
  DOM.offline.classList.remove('show');
  DOM.status.style.opacity = '1';

  DOM.temp.textContent       = data.temperature.toFixed(1);
  DOM.pression.textContent   = data.pression.toFixed(2);
  DOM.debit.textContent      = data.debit.toFixed(1);
  DOM.conversion.textContent = data.conversion.toFixed(1);

  ['temp','pression','debit','conversion'].forEach(k => DOM[k].classList.remove('value-offline'));

  // Mettre à jour les graphiques (définis dans charts.js)
  updateCharts(data);
}

// ─── Polling toutes les 2 secondes ───
async function poll() {
  const data = await API.getLiveData();
  updateKPIs(data);
}
poll();
setInterval(poll, 2000);