// --- Configuration ---
// In production, change to your backend URL (e.g., https://your-backend-xyz.run.app)
const API_URL = 'https://contract-analyzer-3811281641.europe-west1.run.app';

/* ─ i18n — Translation Dictionary ────────────────────────────── */
const TRANSLATIONS = {
    en: {
        'nav.analyze':            'Analyze',
        'nav.how':                'How It Works',
        'nav.upload':             'Upload',
        'nav.submit':             'Submit',
        'nav.login':              'Log In',
        'hero.label':             '// German Freelance Contract Analyzer',
        'hero.title':             'Know every<br>risk before<br>you sign.',
        'hero.desc':              "We don't just flag issues. We show you what matters: Is it a Scheinselbstständigkeit risk? An illegal liability cap? An unenforceable non-compete? Know why it matters and what to do about it.",
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
        'loading.l1':             '$ Loading contract...',
        'loading.l2':             '$ Extracting clauses via GPT-4o...',
        'loading.l3':             '$ Running vector similarity search...',
        'loading.l4':             '$ Synthesizing risk report...',
        'results.heading':        'Analysis complete.',
        'results.download':       '↓ Download',
        'results.reset':          '← Analyze another',
        'footer.tagline':         'Intelligent German freelance contract risk analysis. Not legal advice.',
        'footer.poweredby':       'Powered by',
        'footer.legal':           '© 2025 contract.law — For educational purposes only.',
    },
    de: {
        'nav.analyze':            'Analysieren',
        'nav.how':                "So funktioniert's",
        'nav.upload':             'Hochladen',
        'nav.submit':             'Einreichen',
        'nav.login':              'Anmelden',
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
        'loading.l1':             '$ Vertrag wird geladen...',
        'loading.l2':             '$ Klauseln werden via GPT-4o extrahiert...',
        'loading.l3':             '$ Vektorähnlichkeitssuche läuft...',
        'loading.l4':             '$ Risikobericht wird erstellt...',
        'results.heading':        'Analyse abgeschlossen.',
        'results.download':       '↓ Herunterladen',
        'results.reset':          '← Weiteren Vertrag analysieren',
        'footer.tagline':         'Intelligente Risikoanalyse für deutsche Freelancer-Verträge. Keine Rechtsberatung.',
        'footer.poweredby':       'Unterstützt von',
        'footer.legal':           '© 2025 contract.law — Nur zu Bildungszwecken.',
    }
};

let currentLang = 'en';

function applyLang(lang) {
    currentLang = lang;
    const t = TRANSLATIONS[lang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key] !== undefined) el.innerHTML = t[key];
    });
    document.getElementById('lang-toggle').textContent = lang === 'en' ? 'DE' : 'EN';
    document.documentElement.lang = lang;
}

document.getElementById('lang-toggle').addEventListener('click', () => {
    applyLang(currentLang === 'en' ? 'de' : 'en');
});

/* ─ Scroll detection for pill-nav shadow ─ */
window.addEventListener('scroll', () => {
    document.getElementById('pill-nav').classList.toggle('scrolled', window.scrollY > 20);
});

/* ─ DOM refs ─ */
const dropZone     = document.getElementById('drop-zone');
const fileInput    = document.getElementById('file-input');
const loading      = document.getElementById('loading');
const resultsSection = document.getElementById('results-section');
const findingsContainer = document.getElementById('findings-container');
const briefText    = document.getElementById('negotiation-brief');
const btnDownload  = document.getElementById('btn-download');
const btnReset     = document.getElementById('btn-reset');
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

    uploadState.classList.add('hidden');
    loading.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/analyze`, { method: 'POST', body: formData });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || 'Analysis failed');
        }
        const data = await response.json();
        renderResults(data);
    } catch (error) {
        alert(`Error: ${error.message}`);
        uploadState.classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
    }
}

/* ─ Render results ─ */
function renderResults(data) {
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

    // Findings
    findingsContainer.innerHTML = '';
    (data.findings || []).forEach((f, idx) => {
        const card = document.createElement('div');
        card.className = `finding-card ${f.risk}`;

        const summary = document.createElement('div');
        summary.className = 'finding-summary';
        summary.innerHTML = `
            <span class="risk-badge ${f.risk}">${f.risk}</span>
            <span class="finding-title-text">${f.title}</span>
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
    const blob = new Blob([currentBrief], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'negotiation_brief.txt';
    a.click();
    URL.revokeObjectURL(url);
});

/* ─ Reset to upload ─ */
btnReset.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    uploadState.classList.remove('hidden');
    fileInput.value = '';
    currentBrief = '';
    findingsContainer.innerHTML = '';
    briefText.textContent = '';
    uploadState.scrollIntoView({ behavior: 'smooth' });
});
