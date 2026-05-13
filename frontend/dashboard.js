import { onAuthStateChanged, signOut, updatePassword, deleteUser, reauthenticateWithCredential, EmailAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { API_URL } from './config.js?v=4';

let reportModal = null;

document.addEventListener("DOMContentLoaded", () => {
    const loadingEl = document.getElementById('dashboard-loading');
    const emptyStateEl = document.getElementById('empty-state');
    const gridEl = document.getElementById('analysis-grid');
    const btnLogout = document.getElementById('btn-logout');

    // Create modal
    createReportModal();

    // Show upgrade outcome banner and clean URL
    const _params = new URLSearchParams(window.location.search);
    if (_params.get('upgrade') === 'success') {
        const banner = document.createElement('div');
        banner.style.cssText = 'position:fixed;top:72px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:12px 24px;border-radius:6px;font-family:JetBrains Mono,monospace;font-size:13px;z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.4)';
        banner.textContent = '✓ Plan upgraded — your new limits are active.';
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 6000);
        history.replaceState(null, '', window.location.pathname);
    } else if (_params.get('upgrade') === 'cancelled') {
        const banner = document.createElement('div');
        banner.style.cssText = 'position:fixed;top:72px;left:50%;transform:translateX(-50%);background:#374151;color:#d1d5db;padding:12px 24px;border-radius:6px;font-family:JetBrains Mono,monospace;font-size:13px;z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.4)';
        banner.textContent = 'Checkout cancelled — your plan was not changed.';
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 4000);
        history.replaceState(null, '', window.location.pathname);
    }

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

                // Show user email under the dashboard title
                const subEmail = document.getElementById('dash-sub-email');
                if (subEmail && user.email) subEmail.textContent = user.email;

                if (!authChecked) {
                    authChecked = true;
                    await Promise.all([fetchAnalyses(user), fetchProfile(user)]);
                }

                // Refresh grid + plan usage after the embedded analyzer finishes
                window.addEventListener('analysis-complete', async () => {
                    loadingEl.classList.remove('hidden');
                    loadingEl.textContent = '$ Refreshing analyses...';
                    gridEl.innerHTML = '';
                    emptyStateEl.classList.add('hidden');
                    await Promise.all([fetchAnalyses(user), fetchProfile(user)]);
                });
            });

            btnLogout.onclick = () => {
                signOut(window.firebaseAuth).then(() => {
                    window.location.href = "index.html";
                });
            };

            // Account modal — use window.firebaseAuth.currentUser since `user`
            // from the onAuthStateChanged callback is out of scope here.
            const accountModal = document.getElementById('account-modal');
            const _u = () => window.firebaseAuth?.currentUser;

            document.getElementById('btn-account').onclick = () => {
                const u = _u();
                if (!u) return;
                document.getElementById('account-email').textContent = u.email || '';
                accountModal.style.display = 'block';
            };
            document.getElementById('account-modal-close').onclick = () => {
                accountModal.style.display = 'none';
            };
            accountModal.addEventListener('click', e => { if (e.target === accountModal) accountModal.style.display = 'none'; });

            document.getElementById('btn-change-password').onclick = async () => {
                const u = _u();
                if (!u) return;
                const pw = document.getElementById('new-password').value;
                const msg = document.getElementById('password-msg');
                msg.style.display = 'block';
                if (pw.length < 6) { msg.style.color = '#ef4444'; msg.textContent = 'Password must be at least 6 characters.'; return; }
                try {
                    await updatePassword(u, pw);
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
                const u = _u();
                if (!u) return;
                if (!confirm('Are you sure? This will permanently delete your account and all your analyses.')) return;
                try {
                    const token = await u.getIdToken();
                    // Delete all Firestore data first
                    const analyses = await fetch(`${API_URL}/api/analyses`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json());
                    await Promise.all(analyses.map(a => fetch(`${API_URL}/api/analyses/${a.id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } })));
                    await deleteUser(u);
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

    async function fetchProfile(user) {
        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_URL}/api/user/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) return;
            const profile = await res.json();
            renderPlanBanner(profile);
        } catch {
            // non-critical — silently ignore
        }
    }

    function renderPlanBanner({ tier, analyses_this_month, monthly_limit }) {
        const banner = document.getElementById('plan-banner');
        const badge = document.getElementById('plan-tier-badge');
        const usageText = document.getElementById('plan-usage-text');
        const bar = document.getElementById('plan-usage-bar');
        const upgradeLink = document.getElementById('plan-upgrade-link');

        const COLORS = { free: '#888', pro: '#fafafa', team: '#fafafa' };
        const BG = { free: 'rgba(255,255,255,0.04)', pro: 'rgba(255,255,255,0.1)', team: 'rgba(255,255,255,0.08)' };
        const color = COLORS[tier] || COLORS.free;

        badge.textContent = tier.toUpperCase();
        badge.style.color = color;
        badge.style.background = BG[tier] || BG.free;
        badge.style.border = `1px solid ${color}`;

        const pct = Math.min(analyses_this_month / monthly_limit, 1);
        usageText.textContent = `${analyses_this_month} / ${monthly_limit === 999 ? '∞' : monthly_limit} analyses this month`;
        bar.style.width = `${(pct * 100).toFixed(0)}%`;
        bar.style.background = pct >= 1 ? '#ef4444' : pct >= 0.8 ? '#eab308' : color;

        if (tier !== 'free') upgradeLink.style.display = 'none';

        banner.style.display = 'flex';
    }

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

            const card = document.createElement('article');
            card.className = 'analysis-card';

            const highCount = analysis.high_risk_count || 0;
            const medCount = analysis.medium_risk_count || 0;

            let statsHtml = '';
            if (highCount > 0) statsHtml += `<span class="stat-pill stat-high mono">${highCount} HIGH</span>`;
            if (medCount > 0) statsHtml += `<span class="stat-pill stat-med mono">${medCount} MED</span>`;
            if (highCount === 0 && medCount === 0) statsHtml += `<span class="stat-pill stat-low mono">ALL CLEAR</span>`;

            const safeName = (analysis.filename || 'Unknown Contract')
                .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

            card.innerHTML = `
                <div class="file-row">
                    <span class="file-icon mono">PDF</span>
                    <span class="filename analysis-title">${safeName}</span>
                    <div style="display:flex;gap:6px;align-self:flex-start;margin-left:auto;">
                        <button class="btn-share-analysis mono" title="Copy share link" style="background:none;border:none;color:var(--dim);cursor:pointer;font-size:11px;padding:0 4px;line-height:1;font-family:var(--font-mono);" data-id="${analysis.id}">Share</button>
                        <button class="btn-delete-analysis mono" title="Delete analysis" style="background:none;border:none;color:var(--dim);cursor:pointer;font-size:14px;padding:0 4px;line-height:1;" data-id="${analysis.id}">✕</button>
                    </div>
                </div>
                <div class="meta analysis-meta mono">
                    <span>${date}</span>
                </div>
                <div class="stats analysis-stats">${statsHtml}</div>
            `;

            card.querySelector('.btn-share-analysis').addEventListener('click', async (e) => {
                e.stopPropagation();
                const btn = e.currentTarget;
                btn.textContent = '...';
                try {
                    const token = await window.firebaseAuth.currentUser.getIdToken();
                    const res = await fetch(`${API_URL}/api/analyses/${analysis.id}/share`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (!res.ok) throw new Error();
                    const { url } = await res.json();
                    await navigator.clipboard.writeText(url);
                    btn.textContent = '✓ Copied';
                    setTimeout(() => { btn.textContent = 'Share'; }, 2000);
                } catch {
                    btn.textContent = 'Share';
                    alert('Failed to generate share link.');
                }
            });

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
                    // Reuse the embedded analyzer's refined ResultsView so
                    // saved analyses get the same verdict pill, score grid,
                    // action refboxes, diff blocks etc. as a fresh run.
                    if (typeof window.veritasShowAnalysis === 'function') {
                        window.veritasShowAnalysis(analysis.filename, analysis.report);
                        document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else {
                        showReportModal(analysis);
                    }
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
        // UTF-8 BOM + charset so editors that default to Latin-1 don't
        // mojibake German characters (ä → Ã¤, § → Â§, etc.).
        const blob = new Blob(['﻿' + briefContent], { type: 'text/plain;charset=utf-8' });
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
                        <button id="btn-download-modal" style="margin-top: 15px; padding: 10px 18px; background: var(--white); color: var(--black); border: 1px solid var(--white); border-radius: 6px; cursor: pointer; font-weight: 600; font-family: 'JetBrains Mono', monospace;">↓ Download Brief</button>
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
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 18px 18px 16px;
            background: rgba(255,255,255,0.015);
        `;

        const summary = document.createElement('div');
        summary.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 4px;
            user-select: none;
        `;

        const badge = document.createElement('span');
        badge.style.cssText = `
            padding: 3px 9px;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-family: 'JetBrains Mono', monospace;
        `;
        if (f.risk === 'high') {
            badge.style.cssText += `background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.3);`;
        } else if (f.risk === 'medium') {
            badge.style.cssText += `background: rgba(250,204,21,0.1); color: #facc15; border: 1px solid rgba(250,204,21,0.28);`;
        } else {
            badge.style.cssText += `background: rgba(74,222,128,0.08); color: #4ade80; border: 1px solid rgba(74,222,128,0.28);`;
        }
        badge.textContent = f.risk;

        const titleSpan = document.createElement('span');
        titleSpan.style.cssText = `color: #f5f5f5; font-weight: 600; font-size: 0.95rem; font-family: 'Inter', sans-serif;`;
        titleSpan.textContent = f.title;

        summary.appendChild(badge);
        summary.appendChild(titleSpan);

        const details = document.createElement('div');

        let detailsHtml = '';
        if (f.clause) {
            detailsHtml += `<div style="background: rgba(0,0,0,0.4); padding: 10px 14px; border-radius: 4px; margin: 14px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #999; border-left: 2px solid rgba(255,255,255,0.1); line-height: 1.6;">"${f.clause}"</div>`;
        }
        if (f.body) {
            detailsHtml += `<p style="margin: 14px 0; color: #ccc; font-family: 'Inter', sans-serif; font-size: 0.92rem; line-height: 1.7;">${f.body}</p>`;
        }
        if (f.redline) {
            detailsHtml += `<div style="background: rgba(74,222,128,0.04); padding: 10px 14px; border-radius: 4px; margin: 12px 0; border: 1px solid rgba(74,222,128,0.18); font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #4ade80; line-height: 1.6;">→ ${f.redline}</div>`;
        }
        if (f.statute) {
            detailsHtml += `<div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #888;">⚖ ${f.statute}</div>`;
        }

        details.innerHTML = detailsHtml;

        card.appendChild(summary);
        card.appendChild(details);
        findingsDiv.appendChild(card);
    });

    // Set brief
    briefDiv.textContent = report.brief || '';

    // Download handler
    btnDownload.onclick = () => {
        const blob = new Blob(['﻿' + (report.brief || '')], { type: 'text/plain;charset=utf-8' });
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
