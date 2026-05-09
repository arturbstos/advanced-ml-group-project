import { API_URL } from './config.js?v=4';

/* ─ i18n — Translation Dictionary ────────────────────────────── */
const TRANSLATIONS = {
    en: {
        'nav.how':                'How It Works',
        'nav.pricing':            'Pricing',
        'nav.upload':             'Upload',
        'nav.login':              'Log In',
        'pricing.label':          '// Pricing',
        'pricing.title':          'Simple, transparent pricing.',
        'hero.label':             '// German Freelance Contract Analyzer',
        'hero.title':             'Know every<br>risk before<br>you sign.',
        'hero.desc':              "We don't just flag issues. We show you what matters: Is it a false self-employment risk? An illegal liability cap? An unenforceable non-compete? Know why it matters and what to do about it.",
        'hero.cta1':              'Analyze Contract →',
        'hero.cta2':              'See How It Works',
        'hero.window.status':     'STATUS: LIVE ANALYSIS',
        'hero.window.action':     '→ Redline provided',
        'hero.window.scroll':     'Keep scrolling ↓',
        'how.label':              '// How It Works',
        'how.title':              'Powered by AI.<br>Grounded in German law.',
        'how.step1.title':        'Upload',
        'how.step1.desc':         'Drag and drop your PDF contract. We accept any German freelance agreement.',
        'how.step2.title':        'Extract',
        'how.step2.desc':         'GPT-4o reads and structures every clause — rates, IP, liability, payment terms.',
        'how.step3.title':        'Vector Match',
        'how.step3.desc':         'Each clause is embedded and matched against our legal playbook via Firestore Vector Search.',
        'how.step4.title':        'Report',
        'how.step4.desc':         'Receive a risk-ranked report with statutory citations, redlines, and a negotiation brief.',
        'analyzer.label':         '// Analyzer',
        'analyzer.heading':       'Analyze your<br>contract.',
        'analyzer.drop':          'Drop your PDF contract here',
        'analyzer.browse':        'Browse files',
        'analyzer.privacy':       'Your contract is sent to OpenAI for analysis and is not stored by veritas. See our Privacy Policy.',
        'analyzer.lang_label':    'Report language:',
        'loading.l1':             '$ Loading contract...',
        'loading.l2':             '$ Extracting clauses via GPT-4o...',
        'loading.l3':             '$ Running vector similarity search...',
        'loading.l4':             '$ Synthesizing risk report...',
        'results.heading':        'Analysis complete.',
        'results.download':       '↓ Download',
        'results.reset':          '← Analyze another',
        'footer.tagline':         'Intelligent German freelance contract risk analysis. Not legal advice.',
        'footer.poweredby':       'Powered by',
        'footer.legal':           '© 2026 Nova School of Business and Economics — For educational purposes only.',
        'nav.account':            'Account',
        'nav.logout':             'Log Out',
        'dashboard.title':        'Dashboard',
        'dashboard.your_analyses':'Your Analyses',
        'dashboard.upgrade':      'Upgrade plan →',
        'dashboard.loading':      '$ Loading past analyses...',
        'dashboard.empty.title':  'No analyses yet.',
        'dashboard.empty.desc':   'Upload a contract above to see it here.',
        'dashboard.new_analysis': 'New analysis.',
        'dashboard.search':       'Search by filename...',
    },
    de: {
        'nav.how':                "So funktioniert's",
        'nav.pricing':            'Preise',
        'nav.upload':             'Hochladen',
        'nav.login':              'Anmelden',
        'pricing.label':          '// Preise',
        'pricing.title':          'Einfache, transparente Preise.',
        'hero.label':             '// KI-Vertragsanalyse für Freelancer',
        'hero.title':             'Jeden Risiko<br>kennen, bevor<br>du unterschreibst.',
        'hero.desc':              'Wir zeigen dir, was wirklich wichtig ist: Droht Scheinselbstständigkeit? Ist die Haftungsklausel unwirksam? Ist das Wettbewerbsverbot durchsetzbar? Versteh das Risiko – und was du dagegen tun kannst.',
        'hero.cta1':              'Vertrag analysieren →',
        'hero.cta2':              "So funktioniert's",
        'hero.window.status':     'STATUS: LIVE-ANALYSE',
        'hero.window.action':     '→ Redline vorhanden',
        'hero.window.scroll':     'Weiterscrollen ↓',
        'how.label':              "// So funktioniert's",
        'how.title':              'KI-gestützt.<br>Im deutschen Recht verankert.',
        'how.step1.title':        'Hochladen',
        'how.step1.desc':         'PDF-Vertrag per Drag & Drop hochladen. Wir akzeptieren jeden deutschen Freelancer-Vertrag.',
        'how.step2.title':        'Extrahieren',
        'how.step2.desc':         'GPT-4o liest und strukturiert jede Klausel – Honorar, IP, Haftung, Zahlungsbedingungen.',
        'how.step3.title':        'Vektorabgleich',
        'how.step3.desc':         'Jede Klausel wird eingebettet und über Firestore Vector Search mit unserem Rechts-Playbook abgeglichen.',
        'how.step4.title':        'Bericht',
        'how.step4.desc':         'Du erhältst einen risikogestuften Bericht mit Gesetzesangaben, Redlines und einem Verhandlungsleitfaden.',
        'analyzer.label':         '// Analysator',
        'analyzer.heading':       'Deinen Vertrag<br>analysieren.',
        'analyzer.drop':          'PDF-Vertrag hier ablegen',
        'analyzer.browse':        'Dateien durchsuchen',
        'analyzer.privacy':       'Dein Vertrag wird zur Analyse an OpenAI gesendet und nicht von veritas gespeichert. Siehe unsere Datenschutzerklärung.',
        'analyzer.lang_label':    'Berichtssprache:',
        'loading.l1':             '$ Vertrag wird geladen...',
        'loading.l2':             '$ Klauseln werden via GPT-4o extrahiert...',
        'loading.l3':             '$ Vektorähnlichkeitssuche läuft...',
        'loading.l4':             '$ Risikobericht wird erstellt...',
        'results.heading':        'Analyse abgeschlossen.',
        'results.download':       '↓ Herunterladen',
        'results.reset':          '← Weiteren Vertrag analysieren',
        'footer.tagline':         'Intelligente Risikoanalyse für deutsche Freelancer-Verträge. Keine Rechtsberatung.',
        'footer.poweredby':       'Unterstützt von',
        'footer.legal':           '© 2026 Nova School of Business and Economics — Nur zu Bildungszwecken.',
        'nav.account':            'Konto',
        'nav.logout':             'Abmelden',
        'dashboard.title':        'Dashboard',
        'dashboard.your_analyses':'Deine Analysen',
        'dashboard.upgrade':      'Plan upgraden →',
        'dashboard.loading':      '$ Frühere Analysen werden geladen...',
        'dashboard.empty.title':  'Noch keine Analysen.',
        'dashboard.empty.desc':   'Lade oben einen Vertrag hoch, um ihn hier zu sehen.',
        'dashboard.new_analysis': 'Neue Analyse.',
        'dashboard.search':       'Nach Dateiname suchen...',
    }
};

let currentLang = (localStorage.getItem('lang') === 'de') ? 'de' : 'en';

function applyLang(lang) {
    currentLang = lang;
    try { localStorage.setItem('lang', lang); } catch {}
    const t = TRANSLATIONS[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key] === undefined) return;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = t[key];
        } else {
            el.innerHTML = t[key];
        }
    });
    const toggle = document.getElementById('lang-toggle');
    if (toggle) toggle.textContent = lang === 'en' ? 'DE' : 'EN';
    const langSelect = document.getElementById('languageSelect');
    if (langSelect && langSelect.value !== lang) langSelect.value = lang;
    document.documentElement.lang = lang;
}

document.getElementById('lang-toggle')?.addEventListener('click', () => {
    applyLang(currentLang === 'en' ? 'de' : 'en');
});

document.getElementById('languageSelect')?.addEventListener('change', (e) => {
    applyLang(e.target.value);
});

// Apply persisted language to all data-i18n elements on every page load.
applyLang(currentLang);

/* ─ Scroll detection for pill-nav shadow ─ */
window.addEventListener('scroll', () => {
    document.getElementById('pill-nav')?.classList.toggle('scrolled', window.scrollY > 20);
});

/* ─ DOM refs ─ */
const dropZone     = document.getElementById('drop-zone');
const fileInput    = document.getElementById('file-input');
const loading      = document.getElementById('loading');
const resultsSection = document.getElementById('results-section');
const findingsContainer = document.getElementById('findings-container');
const briefText    = document.getElementById('negotiation-brief');
const btnDownload    = document.getElementById('btn-download');
const btnDownloadPdf = document.getElementById('btn-download-pdf');
const btnReset       = document.getElementById('btn-reset');
const summaryPills = document.getElementById('summary-pills');
const uploadState  = document.getElementById('upload-state');

let currentBrief = '';

/* ─ Drag & drop ─ */
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

/* ─ Core upload & analysis flow ─ */
async function handleFile(file) {
    if (file.type !== 'application/pdf') { alert('Please upload a PDF file.'); return; }
    if (file.size > 10 * 1024 * 1024) { alert('File too large. Maximum size is 10 MB.'); return; }
    if (!window.firebaseAuth?.currentUser) {
        if (window.openAuthModal) window.openAuthModal();
        return;
    }

    uploadState.classList.add('hidden');
    loading.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);
    // Tell the backend which language to render the report in. Falls back
    // to the active UI language (set via lang-toggle) if the dashboard's
    // languageSelect dropdown isn't on this page.
    const langSelect = document.getElementById('languageSelect');
    formData.append('target_language', langSelect ? langSelect.value : currentLang);

    const headers = {};
    if (window.firebaseAuth && window.firebaseAuth.currentUser) {
        const token = await window.firebaseAuth.currentUser.getIdToken();
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_URL}/analyze`, { method: 'POST', body: formData, headers: headers });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            const e = new Error(err.detail || 'Analysis failed');
            e.status = response.status;
            throw e;
        }
        const data = await response.json();
        renderResults(data);
        window.dispatchEvent(new CustomEvent('analysis-complete'));
    } catch (error) {
        if (error.status === 429) {
            const go = confirm(`${error.message}\n\nView pricing plans?`);
            if (go) document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
        } else if (error.message.toLowerCase().includes('scanned')) {
            alert('Scanned PDFs are not supported. Please upload a text-based PDF (not a scan or image).');
        } else {
            alert(`Error: ${error.message}`);
        }
        uploadState.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

/* ─ Rate benchmark bar ─ */
function renderRateBenchmark(bench) {
    const section = document.getElementById('rate-benchmark-section');
    if (!bench || bench.offered === 0) { section.classList.add('hidden'); return; }

    const { offered, p25, median, p75, skill_category, experience, source } = bench;
    const min = Math.min(offered, p25) * 0.85;
    const max = Math.max(offered, p75) * 1.1;
    const range = max - min;
    const pct = v => `${((v - min) / range * 100).toFixed(1)}%`;

    document.getElementById('rate-bar-p25').style.left   = '0';
    document.getElementById('rate-bar-p25').style.width  = pct(p25);
    document.getElementById('rate-bar-mid').style.left   = pct(p25);
    document.getElementById('rate-bar-mid').style.width  = `${((median - p25) / range * 100).toFixed(1)}%`;
    document.getElementById('rate-bar-p75').style.left   = pct(median);
    document.getElementById('rate-bar-p75').style.right  = '0';
    document.getElementById('rate-bar-offer').style.left = `calc(${pct(offered)} - 1.5px)`;

    const status = offered < p25 ? '⚠ Below p25' : offered < median ? 'Below median' : offered < p75 ? 'Above median' : '✓ Above p75';
    document.getElementById('rate-benchmark-label').innerHTML =
        `${experience} ${skill_category} · Offered: <strong style="color:${offered < p25 ? '#ef4444' : offered < median ? '#eab308' : '#22c55e'}">€${offered}/h</strong> &nbsp;|&nbsp; ${status} &nbsp;(${source})`;
    const ticks = document.getElementById('rate-benchmark-ticks');
    ticks.innerHTML =
        `<span>€${p25} p25</span><span>€${median} median</span><span>€${p75} p75</span>`;

    let footnote = document.getElementById('rate-benchmark-footnote');
    if (!footnote) {
        footnote = document.createElement('div');
        footnote.id = 'rate-benchmark-footnote';
        footnote.className = 'mono dim';
        footnote.style.cssText = 'font-size:0.65rem;margin-top:0.4rem;line-height:1.5;';
        footnote.textContent = 'p25/p75 modeled ±15% around experience-adjusted median (Freelancer-Kompass 2025). Not observed percentiles.';
        ticks.after(footnote);
    }

    section.classList.remove('hidden');
}

/* ─ Render results ─ */
function renderResults(data) {
    currentReport = data;
    // Summary pills
    summaryPills.innerHTML = '';
    const counts = data.summary || {};
    [['high', 'HIGH'], ['medium', 'MED'], ['low', 'LOW']].forEach(([key, label]) => {
        if (counts[key]) {
            const pill = document.createElement('span');
            pill.className = `summary-pill ${key} mono`;
            pill.textContent = `${counts[key]} ${label}`;
            summaryPills.appendChild(pill);
        }
    });

    // Rate benchmark
    renderRateBenchmark(data.rate_benchmark);

    // Findings
    findingsContainer.innerHTML = '';
    (data.findings || []).forEach((f, idx) => {
        const card = document.createElement('div');
        card.className = `finding-card ${f.risk}`;

        const isUncurated = f.source === 'System' || f.title === 'Analysis error';

        const summary = document.createElement('div');
        summary.className = 'finding-summary';
        summary.innerHTML = `
            <span class="risk-badge ${f.risk}">${f.risk}</span>
            <span class="finding-title-text">${f.title}</span>
            ${isUncurated ? '<span class="mono dim" style="font-size:0.7rem;flex-shrink:0;">⚠ No curated match — AI-generated</span>' : ''}
            <span class="finding-toggle mono">▶</span>
        `;

        const details = document.createElement('div');
        details.className = 'finding-details';
        details.innerHTML = `
            ${f.clause ? `<div class="clause-block">"${f.clause}"</div>` : ''}
            <p class="finding-body">${f.body || ''}</p>
            ${f.redline ? `<div class="redline-block">→ ${f.redline}</div>` : ''}
            <div class="meta-row">
                ${f.statute ? `<span>⚖ ${f.statute}</span>` : ''}
                ${f.source  ? `<span>📚 ${f.source}</span>`  : ''}
            </div>
        `;

        summary.addEventListener('click', () => {
            const toggle = summary.querySelector('.finding-toggle');
            const isOpen = details.classList.toggle('open');
            toggle.classList.toggle('open', isOpen);
        });

        card.appendChild(summary);
        card.appendChild(details);
        findingsContainer.appendChild(card);
    });

    // Brief
    currentBrief = data.brief || '';
    briefText.textContent = currentBrief;

    resultsSection.classList.remove('hidden');

    // Smooth scroll into results
    setTimeout(() => resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

/* ─ Download brief ─ */
btnDownload.addEventListener('click', () => {
    if (!currentBrief) return;
    // Lead with a UTF-8 BOM and declare the charset on the MIME type so
    // editors that default to Windows-1252 / Latin-1 (Notepad, Excel,
    // older TextEdit) don't corrupt German umlauts / § into mojibake.
    const blob = new Blob(['﻿' + currentBrief], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'negotiation_brief.txt';
    a.click();
    URL.revokeObjectURL(url);
});

/* ─ PDF export ─ */
let currentReport = null;

btnDownloadPdf.addEventListener('click', () => {
    if (!currentReport) return;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });
    const marginL = 15, marginR = 15, pageW = 210;
    const usableW = pageW - marginL - marginR;
    let y = 20;

    const addLine = (text, opts = {}) => {
        const { size = 10, bold = false, color = [200, 200, 200], indent = 0 } = opts;
        doc.setFontSize(size);
        doc.setFont('helvetica', bold ? 'bold' : 'normal');
        doc.setTextColor(...color);
        const lines = doc.splitTextToSize(text, usableW - indent);
        lines.forEach(line => {
            if (y > 275) { doc.addPage(); y = 20; }
            doc.text(line, marginL + indent, y);
            y += size * 0.45;
        });
        y += 2;
    };

    // Header
    doc.setFillColor(15, 15, 15);
    doc.rect(0, 0, 210, 297, 'F');
    addLine('veritas', { size: 18, bold: true, color: [245, 245, 245] });
    addLine(`German Freelance Contract Analysis  ·  ${currentReport.date}`, { size: 9, color: [100, 100, 100] });
    addLine(currentReport.profile, { size: 9, color: [120, 120, 120] });
    y += 4;

    // Summary
    const s = currentReport.summary || {};
    addLine(`Findings: ${s.total || 0} total  ·  ${s.high || 0} HIGH  ·  ${s.medium || 0} MED  ·  ${s.low || 0} LOW`, { size: 10, bold: true, color: [245, 245, 245] });
    y += 4;

    // Rate benchmark
    if (currentReport.rate_benchmark && currentReport.rate_benchmark.offered > 0) {
        const b = currentReport.rate_benchmark;
        addLine(`Rate: €${b.offered}/h  ·  p25 €${b.p25}  ·  median €${b.median}  ·  p75 €${b.p75}  (${b.source})`, { size: 9, color: [160, 160, 160] });
        y += 2;
    }

    // Findings
    addLine('FINDINGS', { size: 11, bold: true, color: [180, 180, 180] });
    y += 2;
    (currentReport.findings || []).forEach((f, i) => {
        const riskColor = f.risk === 'high' ? [239, 68, 68] : f.risk === 'medium' ? [234, 179, 8] : [34, 197, 94];
        addLine(`${i + 1}. [${f.risk.toUpperCase()}] ${f.title}`, { size: 10, bold: true, color: riskColor });
        if (f.body) addLine(f.body, { size: 9, color: [180, 180, 180], indent: 4 });
        if (f.redline) addLine(`→ ${f.redline}`, { size: 9, color: [100, 180, 100], indent: 4 });
        if (f.statute) addLine(`⚖ ${f.statute}`, { size: 8, color: [120, 120, 120], indent: 4 });
        y += 2;
    });

    doc.save(`contract_analysis_${currentReport.date}.pdf`);
});

/* ─ Reset to upload ─ */
btnReset.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    uploadState.classList.remove('hidden');
    fileInput.value = '';
    currentBrief = '';
    currentReport = null;
    findingsContainer.innerHTML = '';
    briefText.textContent = '';
    document.getElementById('rate-benchmark-section').classList.add('hidden');
    uploadState.scrollIntoView({ behavior: 'smooth' });
});
