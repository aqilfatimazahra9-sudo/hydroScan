// static/js/api.js
const API = {
  // Données live du réacteur
  async getLiveData() {
    try {
      const res = await fetch('/api/live-data');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } catch {
      return null; // null = serveur offline
    }
  },

  async getHuiles() {
    const res = await fetch('/api/huiles');
    return res.ok ? res.json() : [];
  },

  async getHuile(id) {
    const res = await fetch(`/api/huiles/${id}`);
    return res.ok ? res.json() : null;
  },

  async updateHuile(id, data) {
    const res = await fetch(`/api/huiles/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.ok;
  },

  async startMonitoring(huileId) {
    const res = await fetch('/api/monitoring/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ huile_id: huileId })
    });
    return res.ok ? res.json() : null;
  },

  async stopMonitoring() {
    const res = await fetch('/api/monitoring/stop', { method: 'POST' });
    return res.ok;
  },

  async getHistory(dateStart = '', dateEnd = '') {
    const params = new URLSearchParams({ date_start: dateStart, date_end: dateEnd });
    const res = await fetch('/api/history?' + params);
    return res.ok ? res.json() : [];
  },

  async getAlerts() {
    const res = await fetch('/api/alerts');
    return res.ok ? res.json() : [];
  },

  async resolveAlert(id) {
    const res = await fetch(`/api/alerts/${id}/resolve`, { method: 'PUT' });
    return res.ok;
  },

  async updateThresholds(data) {
    const res = await fetch('/api/thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.ok;
  },

  exportCSV()  { window.location.href = '/api/export/csv'; },
  exportPDF()  { window.location.href = '/api/export/pdf'; }
};
