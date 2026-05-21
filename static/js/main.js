// static/js/main.js
const DOM = {
  temp:       document.getElementById('val-temp'),
  pression:   document.getElementById('val-pression'),
  debit:      document.getElementById('val-debit'),
  conversion: document.getElementById('val-conversion'),
  clock:      document.getElementById('clock'),
  offline:    document.getElementById('offline-banner'),
  status:     document.getElementById('status-badge'),
  note:       document.getElementById('monitor-note'),
  startBtn:   document.getElementById('btn-start-monitor'),
  stopBtn:    document.getElementById('btn-stop-monitor'),
  huileSelect: document.getElementById('huile-select'),
};

let monitoringTimer = null;
let monitoringRunning = false;
const MONITORING_INTERVAL_MS = 20 * 1000;

setInterval(() => {
  DOM.clock.textContent = new Date().toLocaleTimeString('fr');
}, 1000);

function resetKPIs() {
  ['temp','pression','debit','conversion'].forEach(k => {
    DOM[k].textContent = '---';
    DOM[k].classList.add('value-offline');
  });
}

function setWaitingState(message = 'En attente. Cliquez sur Demarrer pour lancer la simulation.') {
  monitoringRunning = false;
  DOM.startBtn.disabled = false;
  DOM.stopBtn.disabled = true;
  DOM.status.textContent = 'En attente';
  DOM.status.style.opacity = '0.65';
  DOM.offline.classList.remove('show');
  DOM.note.textContent = message;
  resetKPIs();
}

function setRunningState() {
  monitoringRunning = true;
  DOM.startBtn.disabled = true;
  DOM.stopBtn.disabled = false;
  DOM.status.textContent = 'Reacteur Live';
  DOM.status.style.opacity = '1';
  DOM.offline.classList.remove('show');
  DOM.note.textContent = 'Simulation en cours. Les mesures sont generees toutes les 20 secondes.';
}

function setOfflineState() {
  resetKPIs();
  DOM.offline.classList.add('show');
  DOM.status.style.opacity = '0.4';
  DOM.note.textContent = 'Serveur indisponible ou monitoring non demarre.';
}

function updateKPIs(data) {
  if (!data) {
    setOfflineState();
    return;
  }

  DOM.offline.classList.remove('show');
  DOM.status.style.opacity = '1';
  DOM.temp.textContent       = data.temperature.toFixed(1);
  DOM.pression.textContent   = data.pression.toFixed(2);
  DOM.debit.textContent      = data.debit.toFixed(1);
  DOM.conversion.textContent = data.conversion.toFixed(1);

  ['temp','pression','debit','conversion'].forEach(k => DOM[k].classList.remove('value-offline'));
  updateCharts(data);

  if (data.stopped) {
    stopLocalSimulation(data.stop_reason || 'Parametre maximum depasse.');
  }
}

async function poll() {
  if (!monitoringRunning) return;
  const data = await API.getLiveData();
  updateKPIs(data);
}

async function startSimulation() {
  if (monitoringRunning) return;

  const huileId = parseInt(DOM.huileSelect.value, 10);
  if (!huileId) {
    DOM.note.textContent = 'Selectionnez un type d huile avant de demarrer.';
    return;
  }

  const started = await API.startMonitoring(huileId);
  if (!started) {
    setOfflineState();
    return;
  }

  setRunningState();
  await poll();
  monitoringTimer = setInterval(poll, MONITORING_INTERVAL_MS);
}

async function stopSimulation() {
  if (monitoringTimer) {
    clearInterval(monitoringTimer);
    monitoringTimer = null;
  }

  await API.stopMonitoring();
  setWaitingState('Simulation arretee. Cliquez sur Demarrer pour relancer le monitoring.');
}

function stopLocalSimulation(reason) {
  if (monitoringTimer) {
    clearInterval(monitoringTimer);
    monitoringTimer = null;
  }

  monitoringRunning = false;
  DOM.startBtn.disabled = false;
  DOM.stopBtn.disabled = true;
  DOM.status.textContent = 'Arret automatique';
  DOM.status.style.opacity = '1';
  DOM.note.textContent = `Simulation arretee automatiquement: ${reason}`;
  window.alert(`Arret automatique: ${reason}`);
}

async function checkActiveMonitoring() {
  try {
    const res = await fetch('/api/monitoring/status');
    const status = res.ok ? await res.json() : null;
    if (!status || !status.running || monitoringRunning) return;

    DOM.huileSelect.value = status.huile_id;
    setRunningState();
    DOM.note.textContent = `Batch #${status.session_id} toujours en cours (${status.huile}). Mesures toutes les 20 secondes.`;
    await poll();
    monitoringTimer = setInterval(poll, MONITORING_INTERVAL_MS);
  } catch {
    // Si le statut n'est pas disponible, on garde l'etat attente.
  }
}

async function loadHuiles() {
  const huiles = await API.getHuiles();
  DOM.huileSelect.innerHTML = huiles.map(h => (
    `<option value="${h.id}">${h.nom} - ${h.temperature.opt}C, ${h.pression.opt} bar, ${h.debit_h2.opt} Nm3/h</option>`
  )).join('');

  if (!huiles.length) {
    DOM.startBtn.disabled = true;
    DOM.note.textContent = 'Aucun type d huile trouve dans la base de donnees.';
    return;
  }

  await checkActiveMonitoring();
}

setWaitingState();
loadHuiles();

