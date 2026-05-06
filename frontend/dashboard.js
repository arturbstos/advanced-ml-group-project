import { onAuthStateChanged, signOut, updatePassword, deleteUser, reauthenticateWithCredential, EmailAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { API_URL } from './config.js?v=3';

let reportModal = null;

document.addEventListener("DOMContentLoaded", () => {
    const loadingEl = document.getElementById('dashboard-loading');
    const emptyStateEl = document.getElementById('empty-state');
    const gridEl = document.getElementById('analysis-grid');
    const btnLogout = document.getElementById('btn-logout');

    // Create modal
    createReportModal();

    let authChecked = false;

    // Wait for auth to initialize
    const checkAuthInterval = setInterval(() => {
        if (window.firebaseAuth) {
            clearInterval(checkAuthInterval);
            
            onAuthStateChanged(window.firebaseAuth, async (user) => {
                if (!user) {
                    // Not logged in -> redirect to home
                    window.location.href = "index.html";
                    return;
                }
                
                if (!authChecked) {
                    authChecked = true;
                    await fetchAnalyses(user);
                }
            });

            btnLogout.onclick = () => {
                signOut(window.firebaseAuth).then(() => {
                    window.location.href = "index.html";
                });
            };

            // Account modal
            const accountModal = document.getElementById('account-modal');
            document.getElementById('btn-account').onclick = () => {
                document.getElementById('account-email').textContent = user.email || '';
                accountModal.style.display = 'block';
            };
            document.getElementById('account-modal-close').onclick = () => {
                accountModal.style.display = 'none';
            };
            accountModal.addEventListener('click', e => { if (e.target === accountModal) accountModal.style.display = 'none'; });

            document.getElementById('btn-change-password').onclick = async () => {
                const pw = document.getElementById('new-password').value;
                const msg = document.getElementById('password-msg');
                msg.style.display = 'block';
                if (pw.length < 6) { msg.style.color = '#ef4444'; msg.textContent = 'Password must be at least 6 characters.'; return; }
                try {
                    await updatePassword(user, pw);
                    msg.style.color = '#22c55e'; msg.textContent = 'Password updated successfully.';
                    document.getElementById('new-password').value = '';
                } catch (e) {
                    if (e.code === 'auth/requires-recent-login') {
                        msg.style.color = '#eab308'; msg.textContent = 'Please log out and log back in before changing your password.';
                    } else {
                        msg.style.color = '#ef4444'; msg.textContent = e.message;
                    }
                }
            };

            document.getElementById('btn-delete-account').onclick = async () => {
                if (!confirm('Are you sure? This will permanently delete your account and all your analyses.')) return;
                try {
                    const token = await user.getIdToken();
                    // Delete all Firestore data first
                    const analyses = await fetch(`${API_URL}/api/analyses`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json());
                    await Promise.all(analyses.map(a => fetch(`${API_URL}/api/analyses/${a.id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } })));
                    await deleteUser(user);
                    window.location.href = 'index.html';
                } catch (e) {
                    if (e.code === 'auth/requires-recent-login') {
                        alert('Please log out and log back in before deleting your account.');
                    } else {
                        alert('Failed to delete account: ' + e.message);
                    }
                }
            };
        }
    }, 100);

    async function fetchAnalyses(user) {
        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_URL}/api/analyses`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!res.ok) throw new Error("Failed to fetch analyses");
            
            const analyses = await res.json();
            loadingEl.classList.add('hidden');
            
            if (!analyses || analyses.length === 0) {
                emptyStateEl.classList.remove('hidden');
                return;
            }
            
            renderGrid(analyses);
        } catch (error) {
            console.error(error);
            loadingEl.textContent = "$ Error loading analyses. Please try again later.";
        }
    }

    let allAnalyses = [];

    function applyFilters() {
        const query = document.getElementById('search-input').value.toLowerCase();
        const risk = document.getElementById('filter-risk').value;
        const filtered = allAnalyses.filter(a => {
            const nameMatch = (a.filename || '').toLowerCase().includes(query);
            const highCount = a.high_risk_count || 0;
            const medCount = a.medium_risk_count || 0;
            const riskMatch =
                risk === 'all' ||
                (risk === 'high' && highCount > 0) ||
                (risk === 'medium' && medCount > 0) ||
                (risk === 'clear' && highCount === 0 && medCount === 0);
            return nameMatch && riskMatch;
        });
        gridEl.innerHTML = '';
        filtered.forEach(renderCard);
        if (filtered.length === 0) {
            gridEl.innerHTML = '<p class="mono" style="color:var(--text-muted);padding:20px 0;">No analyses match your search.</p>';
        }
    }

    function renderGrid(analyses) {
        allAnalyses = analyses;
        const controls = document.getElementById('dashboard-controls');
        controls.style.display = 'flex';
        controls.classList.remove('hidden');
        document.getElementById('search-input').addEventListener('input', applyFilters);
        document.getElementById('filter-risk').addEventListener('change', applyFilters);
        gridEl.innerHTML = '';
        analyses.forEach(renderCard);
    }

    function renderCard(analysis) {
            const date = new Date(analysis.timestamp).toLocaleDateString(undefined, { 
                year: 'numeric', month: 'short', day: 'numeric' 
            });

            const card = document.createElement('div');
            card.className = 'analysis-card';
            
            const highCount = analysis.high_risk_count || 0;
            const medCount = analysis.medium_risk_count || 0;
            
            let statsHtml = '';
            if (highCount > 0) statsHtml += `<span class="stat-pill stat-high">${highCount} HIGH</span>`;
            if (medCount > 0) statsHtml += `<span class="stat-pill stat-med">${medCount} MED</span>`;
            if (highCount === 0 && medCount === 0) statsHtml += `<span class="stat-pill stat-low">ALL CLEAR</span>`;

            card.innerHTML = `
                <div class="analysis-meta mono" style="display:flex;justify-content:space-between;align-items:center;">
                    <span>${date}</span>
                    <button class="btn-delete-analysis mono" title="Delete analysis" style="background:none;border:none;color:#666;cursor:pointer;font-size:1rem;padding:0 4px;line-height:1;" data-id="${analysis.id}">✕</button>
                </div>
                <div class="analysis-title">${analysis.filename || 'Unknown Contract'}</div>
                <div class="analysis-stats mono">${statsHtml}</div>
            `;

            card.querySelector('.btn-delete-analysis').addEventListener('click', async (e) => {
                e.stopPropagation();
                if (!confirm(`Delete "${analysis.filename}"?`)) return;
                try {
                    const token = await window.firebaseAuth.currentUser.getIdToken();
                    await fetch(`${API_URL}/api/analyses/${analysis.id}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    card.remove();
                    if (gridEl.children.length === 0) emptyStateEl.classList.remove('hidden');
                } catch {
                    alert('Failed to delete analysis. Please try again.');
                }
            });

            card.onclick = () => {
                if (analysis.report && analysis.report.findings) {
                    showReportModal(analysis);
                } else if (analysis.report && analysis.report.brief) {
                    // Legacy: report saved without structured findings
                    downloadBrief(analysis.report.brief, analysis.filename);
                } else {
                    showLegacyCard(card, analysis);
                }
            };
            
            gridEl.appendChild(card);
    }

    function downloadBrief(briefContent, originalFilename) {
        const blob = new Blob([briefContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const name = originalFilename ? originalFilename.replace('.pdf', '') : 'contract';
        a.download = `${name}_brief.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
});

function showLegacyCard(card, analysis) {
    const existing = card.querySelector('.legacy-notice');
    if (existing) { existing.remove(); return; }
    const notice = document.createElement('div');
    notice.className = 'legacy-notice';
    notice.style.cssText = 'margin-top:10px;padding:8px;background:rgba(234,179,8,0.1);border:1px solid rgba(234,179,8,0.3);border-radius:6px;color:#eab308;font-size:0.8rem;font-family:JetBrains Mono,monospace;';
    notice.textContent = 'Full report not available for this entry. Re-analyze the contract to see detailed findings.';
    card.appendChild(notice);
}

function createReportModal() {
    const modal = document.createElement('div');
    modal.id = 'report-modal';
    modal.style.cssText = `
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 9999;
        overflow-y: auto;
    `;

    modal.innerHTML = `
        <div style="min-height: 100%; display: flex; align-items: center; justify-content: center; padding: 20px;">
            <div style="background: var(--bg-main); max-width: 900px; width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); max-height: 90vh; overflow-y: auto; position: relative;">
                <div style="position: sticky; top: 0; padding: 20px; background: var(--bg-main); border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; z-index: 10;">
                    <h2 id="modal-title" style="color: var(--text-main); margin: 0; font-size: 1.3rem;"></h2>
                    <button id="btn-close-modal" style="background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">✕</button>
                </div>
                <div style="padding: 30px;">
                    <div id="modal-profile" style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px; font-family: 'JetBrains Mono', monospace;"></div>
                    <div id="modal-summary" style="display: flex; gap: 10px; margin-bottom: 30px;"></div>
                    <div id="modal-findings" style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 30px;"></div>
                    <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; margin-top: 20px;">
                        <h3 style="color: var(--text-main); margin-top: 0;">Negotiation Brief</h3>
                        <pre id="modal-brief" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; margin: 0;"></pre>
                        <button id="btn-download-modal" style="margin-top: 15px; padding: 10px 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; border-radius: 6px; cursor: pointer; font-weight: 600; font-family: 'JetBrains Mono', monospace;">↓ Download Brief</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        #report-modal[data-open] {
            display: flex !important;
        }
        #report-modal[data-open] > div > div {
            animation: slideUp 0.3s ease;
        }
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(modal);
    reportModal = modal;

    modal.querySelector('#btn-close-modal').addEventListener('click', closeReportModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeReportModal();
    });
}

function showReportModal(analysis) {
    const report = analysis.report;
    if (!report) return;

    const modal = reportModal;
    const title = modal.querySelector('#modal-title');
    const profile = modal.querySelector('#modal-profile');
    const summaryDiv = modal.querySelector('#modal-summary');
    const findingsDiv = modal.querySelector('#modal-findings');
    const briefDiv = modal.querySelector('#modal-brief');
    const btnDownload = modal.querySelector('#btn-download-modal');

    // Set title
    title.textContent = analysis.filename || 'Contract Analysis';

    // Set profile
    profile.textContent = report.profile || '';

    // Set summary pills
    summaryDiv.innerHTML = '';
    const counts = report.summary || {};
    [['high', 'HIGH'], ['medium', 'MED'], ['low', 'LOW']].forEach(([key, label]) => {
        if (counts[key]) {
            const pill = document.createElement('span');
            pill.style.cssText = `
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 600;
                font-family: 'JetBrains Mono', monospace;
            `;

            if (key === 'high') {
                pill.style.cssText += `background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2);`;
            } else if (key === 'medium') {
                pill.style.cssText += `background: rgba(234, 179, 8, 0.1); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.2);`;
            } else {
                pill.style.cssText += `background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2);`;
            }
            pill.textContent = `${counts[key]} ${label}`;
            summaryDiv.appendChild(pill);
        }
    });

    // Set findings
    findingsDiv.innerHTML = '';
    (report.findings || []).forEach((f) => {
        const card = document.createElement('div');
        card.style.cssText = `
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
        `;
        if (f.risk === 'high') card.style.borderLeftColor = '#ef4444';
        else if (f.risk === 'medium') card.style.borderLeftColor = '#eab308';
        else card.style.borderLeftColor = '#22c55e';
        card.style.borderLeftWidth = '4px';

        const summary = document.createElement('div');
        summary.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            user-select: none;
        `;

        const badge = document.createElement('span');
        badge.style.cssText = `
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
            min-width: 50px;
        `;
        if (f.risk === 'high') {
            badge.style.cssText += `background: #ef4444; color: white;`;
        } else if (f.risk === 'medium') {
            badge.style.cssText += `background: #eab308; color: #000;`;
        } else {
            badge.style.cssText += `background: #22c55e; color: #000;`;
        }
        badge.textContent = f.risk;

        const titleSpan = document.createElement('span');
        titleSpan.style.color = 'var(--text-main)';
        titleSpan.style.fontWeight = '600';
        titleSpan.textContent = f.title;

        summary.appendChild(badge);
        summary.appendChild(titleSpan);

        const details = document.createElement('div');
        details.style.cssText = `
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.5;
        `;

        let detailsHtml = '';
        if (f.clause) detailsHtml += `<div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 4px; margin: 10px 0; font-style: italic; color: var(--text-main);">"${f.clause}"</div>`;
        if (f.body) detailsHtml += `<p style="margin: 10px 0; color: var(--text-main);">${f.body}</p>`;
        if (f.redline) detailsHtml += `<div style="background: rgba(34, 197, 94, 0.1); padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 3px solid #22c55e;">→ <strong>${f.redline}</strong></div>`;
        if (f.statute) detailsHtml += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);"><strong>⚖ ${f.statute}</strong></div>`;

        details.innerHTML = detailsHtml;

        card.appendChild(summary);
        card.appendChild(details);
        findingsDiv.appendChild(card);
    });

    // Set brief
    briefDiv.textContent = report.brief || '';

    // Download handler
    btnDownload.onclick = () => {
        const blob = new Blob([report.brief || ''], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const name = analysis.filename ? analysis.filename.replace('.pdf', '') : 'contract';
        a.download = `${name}_brief.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Show modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeReportModal() {
    if (reportModal) {
        reportModal.style.display = 'none';
        document.body.style.overflow = '';
    }
}
