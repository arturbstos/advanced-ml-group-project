import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { API_URL } from './config.js?v=4';

const ADMIN_UID = "0WnmxZOQMrQElTSW9Zms23Zwd0y1";

function toast(msg, ok = true) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.style.borderColor = ok ? 'var(--green)' : 'var(--red)';
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 3000);
}

document.addEventListener("DOMContentLoaded", () => {
    // Tab switching
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.admin-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        });
    });

    const checkInterval = setInterval(() => {
        if (!window.firebaseAuth) return;
        clearInterval(checkInterval);

        onAuthStateChanged(window.firebaseAuth, async (user) => {
            if (!user || user.uid !== ADMIN_UID) {
                document.body.innerHTML = '<div style="font-family:monospace;color:#ef4444;padding:80px;text-align:center;">Access denied.</div>';
                return;
            }
            const token = await user.getIdToken();
            loadAnalytics(token);
            loadPlaybook(token);
            wireAddEntry(token);
        });
    }, 100);
});

async function loadAnalytics(token) {
    try {
        const res = await fetch(`${API_URL}/api/admin/analytics`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) return;
        const { total_30d, daily } = await res.json();

        document.getElementById('stat-total').textContent = total_30d;

        const todayKey = new Date().toISOString().slice(0, 10);
        const todayEntry = daily.find(d => d.date === todayKey);
        document.getElementById('stat-today').textContent = todayEntry?.analyses ?? 0;

        const peak = Math.max(...daily.map(d => d.analyses));
        document.getElementById('stat-peak').textContent = peak;

        const barsEl = document.getElementById('chart-bars');
        barsEl.innerHTML = '';
        daily.forEach(d => {
            const bar = document.createElement('div');
            bar.className = 'chart-bar';
            bar.style.height = peak > 0 ? `${Math.max(4, (d.analyses / peak) * 80)}px` : '4px';
            bar.title = `${d.date}: ${d.analyses}`;
            barsEl.appendChild(bar);
        });
    } catch (e) {
        console.error('Analytics load failed:', e);
    }
}

async function loadPlaybook(token) {
    const listEl = document.getElementById('playbook-list');
    try {
        const res = await fetch(`${API_URL}/api/playbook`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed');
        const { entries } = await res.json();
        listEl.innerHTML = '';
        entries.forEach(e => {
            const row = document.createElement('div');
            row.className = 'playbook-row';
            row.innerHTML = `
                <span class="playbook-id mono">${e.id}</span>
                <span class="playbook-type">${e.clause_type}</span>
                <span class="playbook-risk ${e.risk_level}">${e.risk_level.toUpperCase()}</span>
                <button class="admin-btn danger btn-delete" data-id="${e.id}" style="margin-left:auto;">Delete</button>
            `;
            listEl.appendChild(row);
        });
        listEl.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', () => deleteEntry(btn.dataset.id, token));
        });
    } catch {
        listEl.innerHTML = '<div style="font-family:var(--font-mono);font-size:12px;color:var(--red);">Failed to load playbook.</div>';
    }
}

async function deleteEntry(id, token) {
    if (!confirm(`Delete playbook entry ${id}?`)) return;
    const res = await fetch(`${API_URL}/api/admin/playbook/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        toast(`Deleted ${id}`);
        loadPlaybook(token);
    } else {
        toast('Delete failed', false);
    }
}

function wireAddEntry(token) {
    document.getElementById('btn-add-entry').addEventListener('click', async () => {
        const statusEl = document.getElementById('add-status');
        const body = {
            id:                  document.getElementById('f-id').value.trim(),
            clause_type:         document.getElementById('f-type').value.trim(),
            risk_level:          document.getElementById('f-risk').value,
            statute_ref:         document.getElementById('f-statute').value.trim(),
            pattern_description: document.getElementById('f-pattern').value.trim(),
            legal_reasoning:     document.getElementById('f-reasoning').value.trim(),
            recommended_redline: document.getElementById('f-redline').value.trim(),
        };
        if (!body.id || !body.clause_type || !body.pattern_description || !body.legal_reasoning) {
            statusEl.textContent = 'Fill in all required fields.';
            statusEl.style.color = 'var(--red)';
            return;
        }
        statusEl.textContent = '$ Generating embedding...';
        statusEl.style.color = 'var(--muted)';
        try {
            const res = await fetch(`${API_URL}/api/admin/playbook`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) {
                statusEl.textContent = data.detail || 'Error';
                statusEl.style.color = 'var(--red)';
                return;
            }
            statusEl.textContent = '';
            toast(`Added ${data.id}`);
            // Clear form
            ['f-id','f-type','f-statute','f-pattern','f-reasoning','f-redline'].forEach(id => {
                document.getElementById(id).value = '';
            });
            loadPlaybook(token);
        } catch {
            statusEl.textContent = 'Request failed.';
            statusEl.style.color = 'var(--red)';
        }
    });
}
