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

  async getHistory(dateStart = '', dateEnd = '') {
    const params = new URLSearchParams({ date_start: dateStart, date_end: dateEnd });
    const res = await fetch('/api/history?' + params);
    return res.ok ? res.json() : [];
  },

  async getAlerts() {
    const res = await fetch('/api/alerts');
    return res.ok ? res.json() : [];
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