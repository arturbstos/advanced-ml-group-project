import { API_URL } from './config.js?v=4';

/* ─ i18n — Translation Dictionary ────────────────────────────── */
const TRANSLATIONS = {
    en: {
        'nav.how':                'How',
        'nav.pricing':            'Pricing',
        'nav.upload':             'Analyzer',
        'nav.login':              'Log In',
        'pricing.label':          '// pricing',
        'pricing.title':          'Simple, transparent pricing.',
        'pricing.sub':            'No seat-based bait-and-switch. No "Contact Sales" wall. Pay for what you analyze.',
        'pricing.free.f1':        '1 contract analysis / mo',
        'pricing.free.f2':        'Risk summary only',
        'pricing.free.f3':        'No download brief',
        'pricing.free.f4':        'Veritas badge on output',
        'pricing.free.role':      'Curious freelancer',
        'pricing.pro.f1':         '10 contract analyses / mo',
        'pricing.pro.f2':         'Full negotiation brief',
        'pricing.pro.f3':         'Statute + benchmark sources',
        'pricing.pro.f4':         'Priority support',
        'pricing.pro.role':       'Active solo freelancer',
        'pricing.team.f1':        'Up to 5 seats',
        'pricing.team.f2':        'API access',
        'pricing.team.f3':        'Custom playbook entries',
        'pricing.team.f4':        'Co-branded brief PDFs',
        'pricing.team.role':      'Steuerberater & agencies',
        'hero.label':             'German freelance contract analyzer',
        'hero.title':             'Know every<br>risk before<br>you sign.',
        'hero.desc':              "We don't just flag issues. We tell you what each clause actually means under German law — false self-employment, illegal liability caps, unenforceable non-competes — and draft the redline you should send back.",
        'hero.cta1':               'Analyze a contract →',
        'hero.cta2':              'See how it works',
        'hero.window.status':     'STATUS · LIVE',
        'hero.window.action':     '→ Redline drafted',
        'hero.window.scroll':     'Keep scrolling ↓',
        'how.label':              '// how it works',
        'how.title':              'Powered by AI.<br>Grounded in German law.',
        'how.sub':                'Every flag we raise is anchored to a real statute or BGH ruling — and to a concrete redline you can paste into your reply.',
        'how.step1.title':        'Upload',
        'how.step1.desc':         'Drag and drop your German freelance contract. PDF, signed or unsigned.',
        'how.step2.title':        'Extract',
        'how.step2.desc':         'GPT-4o reads every clause — rates, IP, liability, hours, payment terms.',
        'how.step3.title':        'Vector match',
        'how.step3.desc':         '66 risky-clause patterns. Firestore vector search finds yours in milliseconds.',
        'how.step4.title':        'Brief',
        'how.step4.desc':         'Risk-ranked report with statute citations, redlines, and a negotiation plan.',
        'analyzer.label':         '// analyzer',
        'analyzer.heading':       'Drop a contract.<br>Get a brief in seconds.',
        'analyzer.subhead':       'Analyze your contract.',
        'analyzer.timing':        'Average analysis takes 7–9 seconds.',
        'analyzer.drop':          'Drop your PDF contract here',
        'analyzer.subnote':       'or browse from your machine — max 10 MB · German or English',
        'analyzer.browse':        'Browse files →',
        'analyzer.privacy.lead':  'Your contract is sent to OpenAI for analysis and is not stored by veritas. See our ',
        'analyzer.privacy.link':  'Privacy Policy',
        'analyzer.demo':          'Or try the demo contract →',
        'analyzer.lang_label':    'report:',
        'loading.l1':             '$ Loading contract...',
        'loading.l2':             '$ Extracting clauses via GPT-4o...',
        'loading.l3':             '$ Running vector similarity search...',
        'loading.l4':             '$ Synthesizing risk report...',
        'results.heading':        "Here's what to push back on.",
        'results.findings_label': '// findings · click to expand',
        'results.download':       '↓ TXT',
        'results.copy':           'Copy',
        'results.send_client':    'Send to client →',
        'results.reset':          '← Analyze another',
        'footer.tagline':         'Intelligent German freelance contract risk analysis. Not legal advice — get a Fachanwalt for that.',
        'footer.poweredby':       '// powered by',
        'footer.legal':           '© 2026 Nova School of Business and Economics — For educational purposes only · Not legal advice',
        'nav.account':            'Account',
        'nav.logout':             'Log Out',
        'dashboard.eyebrow':      '// your workspace',
        'dashboard.title':        'Dashboard',
        'dashboard.your_analyses':'Past analyses',
        'dashboard.upgrade':      'Manage plan →',
        'dashboard.loading':      '$ Loading past analyses...',
        'dashboard.empty.title':  'No analyses yet.',
        'dashboard.empty.desc':   'Upload a contract above to see it here.',
        'dashboard.new_analysis': 'New analysis.',
        'dashboard.search':       'Search by filename...',
    },
    de: {
        'nav.how':                "So funktioniert's",
        'nav.pricing':            'Preise',
        'nav.upload':             'Analysator',
        'nav.login':              'Anmelden',
        'pricing.label':          '// preise',
        'pricing.title':          'Einfache, transparente Preise.',
        'pricing.sub':            'Keine sitzbasierte Falle. Keine "Kontaktieren Sie den Vertrieb"-Hürde. Zahle nur für tatsächliche Analysen.',
        'pricing.free.f1':        '1 Vertragsanalyse / Monat',
        'pricing.free.f2':        'Nur Risiko-Übersicht',
        'pricing.free.f3':        'Kein Download-Brief',
        'pricing.free.f4':        'Veritas-Badge im Output',
        'pricing.free.role':      'Neugierige Freelancer',
        'pricing.pro.f1':         '10 Vertragsanalysen / Monat',
        'pricing.pro.f2':         'Vollständiger Verhandlungsbrief',
        'pricing.pro.f3':         'Gesetz + Benchmark-Quellen',
        'pricing.pro.f4':         'Prioritäts-Support',
        'pricing.pro.role':       'Aktive Solo-Freelancer',
        'pricing.team.f1':        'Bis zu 5 Plätze',
        'pricing.team.f2':        'API-Zugang',
        'pricing.team.f3':        'Eigene Playbook-Einträge',
        'pricing.team.f4':        'Co-gebrandete Brief-PDFs',
        'pricing.team.role':      'Steuerberater & Agenturen',
        'hero.label':             'KI-Vertragsanalyse für Freelancer',
        'hero.title':             'Jedes Risiko<br>kennen, bevor<br>du unterschreibst.',
        'hero.desc':              'Wir markieren nicht nur Risiken. Wir erklären, was jede Klausel im deutschen Recht wirklich bedeutet – Scheinselbstständigkeit, unwirksame Haftungsklauseln, undurchsetzbare Wettbewerbsverbote – und entwerfen die Redline, die du zurücksenden solltest.',
        'hero.cta1':              'Vertrag analysieren →',
        'hero.cta2':              "So funktioniert's",
        'hero.window.status':     'STATUS · LIVE',
        'hero.window.action':     '→ Redline erstellt',
        'hero.window.scroll':     'Weiterscrollen ↓',
        'how.label':              "// so funktioniert's",
        'how.title':              'KI-gestützt.<br>Im deutschen Recht verankert.',
        'how.sub':                'Jede Markierung ist an ein konkretes Gesetz oder eine BGH-Entscheidung gebunden – und an eine konkrete Redline, die du in deine Antwort einfügen kannst.',
        'how.step1.title':        'Hochladen',
        'how.step1.desc':         'Ziehe deinen deutschen Freelancer-Vertrag per Drag & Drop. PDF, unterzeichnet oder nicht.',
        'how.step2.title':        'Extrahieren',
        'how.step2.desc':         'GPT-4o liest jede Klausel – Honorar, IP, Haftung, Stunden, Zahlungsbedingungen.',
        'how.step3.title':        'Vektorabgleich',
        'how.step3.desc':         '66 Muster riskanter Klauseln. Firestore Vector Search findet deine in Millisekunden.',
        'how.step4.title':        'Brief',
        'how.step4.desc':         'Risiko-eingestufter Bericht mit Gesetzesangaben, Redlines und einem Verhandlungsplan.',
        'analyzer.label':         '// analysator',
        'analyzer.heading':       'Vertrag ablegen.<br>Brief in Sekunden.',
        'analyzer.subhead':       'Vertrag analysieren.',
        'analyzer.timing':        'Durchschnittliche Analyse dauert 7–9 Sekunden.',
        'analyzer.drop':          'PDF-Vertrag hier ablegen',
        'analyzer.subnote':       'oder vom Computer durchsuchen – max. 10 MB · Deutsch oder Englisch',
        'analyzer.browse':        'Dateien durchsuchen →',
        'analyzer.privacy.lead':  'Dein Vertrag wird zur Analyse an OpenAI gesendet und nicht von veritas gespeichert. Siehe unsere ',
        'analyzer.privacy.link':  'Datenschutzerklärung',
        'analyzer.demo':          'Oder probiere den Beispielvertrag →',
        'analyzer.lang_label':    'Bericht:',
        'loading.l1':             '$ Vertrag wird geladen...',
        'loading.l2':             '$ Klauseln werden via GPT-4o extrahiert...',
        'loading.l3':             '$ Vektorähnlichkeitssuche läuft...',
        'loading.l4':             '$ Risikobericht wird erstellt...',
        'results.heading':        'Hier sind die Punkte, die du verhandeln solltest.',
        'results.findings_label': '// findings · zum aufklappen klicken',
        'results.download':       '↓ TXT',
        'results.copy':           'Kopieren',
        'results.send_client':    'An Auftraggeber senden →',
        'results.reset':          '← Weiteren Vertrag analysieren',
        'footer.tagline':         'Intelligente Risikoanalyse für deutsche Freelancer-Verträge. Keine Rechtsberatung – dafür brauchst du einen Fachanwalt.',
        'footer.poweredby':       '// unterstützt von',
        'footer.legal':           '© 2026 Nova School of Business and Economics — Nur zu Bildungszwecken · Keine Rechtsberatung',
        'nav.account':            'Konto',
        'nav.logout':             'Abmelden',
        'dashboard.eyebrow':      '// dein arbeitsbereich',
        'dashboard.title':        'Dashboard',
        'dashboard.your_analyses':'Frühere Analysen',
        'dashboard.upgrade':      'Plan verwalten →',
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
let currentFilename = '';

/* ─ Drag & drop ─ */
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

/* ─ Demo contract: fetch bundled sample PDF and run analysis on it ─ */
document.getElementById('btn-demo-contract')?.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
        const resp = await fetch('sample-contract.pdf');
        if (!resp.ok) throw new Error('Could not load demo contract.');
        const blob = await resp.blob();
        const file = new File([blob], 'demo-contract.pdf', { type: 'application/pdf' });
        await handleFile(file);
    } catch (err) {
        alert('Failed to load demo contract: ' + err.message);
    }
});

/* ─ Core upload & analysis flow ─ */
async function handleFile(file) {
    if (file.type !== 'application/pdf') { alert('Please upload a PDF file.'); return; }
    if (file.size > 10 * 1024 * 1024) { alert('File too large. Maximum size is 10 MB.'); return; }
    if (!window.firebaseAuth?.currentUser) {
        if (window.openAuthModal) window.openAuthModal();
        return;
    }

    currentFilename = file.name;
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
            const go = confirm(`${error.message}\n\nUpgrade to Pro for 10 analyses/month?`);
            if (go) window.location.href = 'mailto:arturdbastos@gmail.com?subject=Veritas%20Plan%20Upgrade&body=Hi%2C%20I%27d%20like%20to%20upgrade%20my%20Veritas%20plan.';
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
    const range = max - min || 1;
    const pctNum = v => ((v - min) / range * 100);
    const pct = v => `${pctNum(v).toFixed(1)}%`;

    // Bar segments
    document.getElementById('rate-bar-p25').style.left   = '0';
    document.getElementById('rate-bar-p25').style.width  = pct(p25);
    document.getElementById('rate-bar-mid').style.left   = pct(p25);
    document.getElementById('rate-bar-mid').style.width  = `${(pctNum(p75) - pctNum(p25)).toFixed(1)}%`;
    document.getElementById('rate-bar-p75').style.left   = pct(p75);
    document.getElementById('rate-bar-p75').style.right  = '0';
    document.getElementById('rate-bar-offer').style.left = `calc(${pct(offered)} - 1.5px)`;
    document.getElementById('rate-bar-offer').setAttribute('data-label', `YOU · €${offered}`);

    // Header label — short and clean: "rate benchmark · {profile}" + summary on right
    const profileLine = `${experience} ${skill_category}`;
    const deltaPct = median ? ((offered / median - 1) * 100) : 0;
    const offerColor = offered < p25 ? 'var(--red)' : offered < median ? 'var(--amber)' : 'var(--green)';
    const summaryLine =
        `Your offer <strong style="color:${offerColor};">€${offered}/h</strong> · ${deltaPct.toFixed(0)}% vs median €${median}/h`;
    document.getElementById('rate-benchmark-label').innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap;">
        <span class="rate-label mono">// ${profileLine}</span>
        <span class="rate-summary mono">${summaryLine}</span>
      </div>
      <div style="margin-top:8px;padding:6px 10px;border-left:2px solid var(--amber);font-size:12px;font-family:var(--font-mono);color:var(--amber);line-height:1.5;">
        ⚠ p25/p75 are modeled estimates (±15% around the experience-adjusted median), not observed survey percentiles.
      </div>`;

    // 5 ticks: min · p25 · median · p75 · max
    const ticks = document.getElementById('rate-benchmark-ticks');
    ticks.innerHTML = `
      <span>€${Math.round(min)}</span>
      <span>p25 · €${p25}</span>
      <span>median · €${median}</span>
      <span>p75 · €${p75}</span>
      <span>€${Math.round(max)}</span>`;

    // Source line below ticks
    let sourceLine = document.getElementById('rate-benchmark-source');
    if (!sourceLine) {
        sourceLine = document.createElement('div');
        sourceLine.id = 'rate-benchmark-source';
        sourceLine.className = 'mono dim';
        sourceLine.style.cssText = 'font-size:11px;margin-top:12px;letter-spacing:0.02em;';
        ticks.after(sourceLine);
    }
    sourceLine.textContent = `source · ${source}`;

    section.classList.remove('hidden');
}

/* ─ Render results ─ */
const _RISK_LABELS = {
    high:   { en: 'HIGH', de: 'HOCH' },
    medium: { en: 'MED',  de: 'MITTEL' },
    low:    { en: 'LOW',  de: 'NIEDRIG' },
};
function _riskLabel(risk) {
    const l = _RISK_LABELS[risk];
    if (!l) return (risk || '').toUpperCase();
    return l[currentLang] || l.en;
}

function _escape(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

/* Severity score mapped from the LLM-assigned risk tier.
 * high=9.0, medium=5.5, low=2.0. Displayed as X / 10 to convey relative
 * severity — not independently computed. Uses the backend `score` field
 * if one is ever added to the Finding schema. */
function _findingScore(f) {
    if (typeof f.score === 'number') return f.score;
    if (f.risk === 'high')   return 9.0;
    if (f.risk === 'medium') return 5.5;
    return 2.0;
}

function _findingTag(f) {
    if (f.risk === 'high')   return 'CRITICAL';
    if (f.risk === 'medium') return 'NEGOTIATE';
    return 'OK';
}

const _VERDICT_COPY = {
    en: {
        high: { label: 'MATERIAL RISKS FOUND', cls: 'high' },
        med:  { label: 'NEGOTIATE BEFORE SIGNING', cls: 'med' },
        low:  { label: 'SAFE TO SIGN', cls: 'low' },
    },
    de: {
        high: { label: 'WESENTLICHE RISIKEN GEFUNDEN', cls: 'high' },
        med:  { label: 'VOR DER UNTERSCHRIFT VERHANDELN', cls: 'med' },
        low:  { label: 'UNTERSCHRIFTSREIF', cls: 'low' },
    },
};
function _verdict(counts) {
    const lang = currentLang === 'de' ? 'de' : 'en';
    const v = _VERDICT_COPY[lang];
    if ((counts.high || 0) > 0) return v.high;
    if ((counts.medium || 0) > 0) return v.med;
    return v.low;
}

const _SCORE_GRID_COPY = {
    en: {
        risk_label: '// risk score',
        rate_label: '// rate vs market',
        liab_label: '// liability exposure',
        critical: 'critical',
        to_negotiate: 'to negotiate',
        all_clear: 'no flags',
        rate_na: 'No rate stated',
        rate_sub: (offered, median) => `€${offered}/h · median €${median}/h`,
        liab_unlimited: 'Unlimited',
        liab_unlimited_sub: 'Cap at fees recommended',
        liab_capped: 'Capped',
        liab_capped_sub: 'Review the proposed redline',
        liab_standard: 'Standard',
        liab_standard_sub: 'No liability flags raised',
        liab_na: '—',
        liab_na_sub: 'Not detected in this contract',
    },
    de: {
        risk_label: '// risiko-score',
        rate_label: '// honorar vs markt',
        liab_label: '// haftungsrisiko',
        critical: 'kritisch',
        to_negotiate: 'verhandeln',
        all_clear: 'keine Flags',
        rate_na: 'Kein Honorar angegeben',
        rate_sub: (offered, median) => `€${offered}/h · Median €${median}/h`,
        liab_unlimited: 'Unbeschränkt',
        liab_unlimited_sub: 'Deckelung auf Honorarsumme empfohlen',
        liab_capped: 'Begrenzt',
        liab_capped_sub: 'Prüfe die vorgeschlagene Redline',
        liab_standard: 'Standard',
        liab_standard_sub: 'Keine Haftungs-Flags',
        liab_na: '—',
        liab_na_sub: 'In diesem Vertrag nicht erkannt',
    },
};

/* Aggregate 0–10 risk score from per-finding scores: weighted blend of max + avg. */
function _overallRiskScore(findings) {
    const flagged = findings.filter(f => f.risk !== 'low');
    if (!flagged.length) return null;
    const scores = flagged.map(_findingScore);
    const max = Math.max(...scores);
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    return ((max * 0.7) + (avg * 0.3)).toFixed(1);
}

function _rateDelta(bench) {
    if (!bench || !bench.median || !bench.offered) return null;
    return Math.round(((bench.offered - bench.median) / bench.median) * 100);
}

/* Heuristic: scan findings for liability/Haftung mentions and use the worst
 * matching risk level. Falls back to a neutral state if not detected. */
function _liabilityExposure(findings, copy) {
    const re = /haftung|liabilit/i;
    const hits = (findings || []).filter(f => re.test(f.title || '') || re.test(f.body || ''));
    if (!hits.length) return { val: copy.liab_na, sub: copy.liab_na_sub, color: 'var(--dim)' };
    const high = hits.find(f => f.risk === 'high');
    if (high) return { val: copy.liab_unlimited, sub: copy.liab_unlimited_sub, color: 'var(--red)' };
    const med = hits.find(f => f.risk === 'medium');
    if (med) return { val: copy.liab_capped, sub: copy.liab_capped_sub, color: 'var(--amber)' };
    return { val: copy.liab_standard, sub: copy.liab_standard_sub, color: 'var(--green)' };
}

function _renderScoreGrid(data) {
    const grid = document.getElementById('score-grid');
    if (!grid) return;
    const lang = currentLang === 'de' ? 'de' : 'en';
    const copy = _SCORE_GRID_COPY[lang];
    const findings = data.findings || [];
    const counts = data.summary || {};

    // Cell 1: risk score
    const riskScore = _overallRiskScore(findings);
    const critical = counts.high || 0;
    const negotiate = counts.medium || 0;
    const riskValHtml = riskScore != null
        ? `<span class="num" style="color:var(--text);">${riskScore}</span> <span style="font-size:14px;color:var(--dim);font-family:var(--font-mono);">/ 10</span>`
        : `<span class="num" style="color:var(--text);">—</span>`;
    const riskSub = critical || negotiate
        ? `${critical} ${copy.critical} · ${negotiate} ${copy.to_negotiate}`
        : copy.all_clear;

    // Cell 2: rate vs market
    const delta = _rateDelta(data.rate_benchmark);
    const rateColor = delta == null ? 'var(--dim)'
        : delta < -10 ? 'var(--red)'
        : delta < 0   ? 'var(--amber)'
        : 'var(--green)';
    const rateValHtml = delta != null
        ? `<span class="num" style="color:${rateColor};">${delta > 0 ? '+' : ''}${delta}%</span>`
        : `<span class="num" style="color:var(--dim);">—</span>`;
    const rateSub = delta != null
        ? copy.rate_sub(data.rate_benchmark.offered, data.rate_benchmark.median)
        : copy.rate_na;

    // Cell 3: liability exposure
    const liab = _liabilityExposure(findings, copy);

    grid.innerHTML = `
      <div class="score-cell">
        <span class="lbl">${copy.risk_label}</span>
        <span class="val">${riskValHtml}</span>
        <span class="sub">${riskSub}</span>
      </div>
      <div class="score-cell">
        <span class="lbl">${copy.rate_label}</span>
        <span class="val">${rateValHtml}</span>
        <span class="sub">${_escape(rateSub)}</span>
      </div>
      <div class="score-cell">
        <span class="lbl">${copy.liab_label}</span>
        <span class="val" style="color:${liab.color};">${_escape(liab.val)}</span>
        <span class="sub">${_escape(liab.sub)}</span>
      </div>`;
    grid.classList.remove('hidden');
}

function _renderVerdictPill(counts) {
    const v = _verdict(counts);
    const pill = document.createElement('span');
    pill.className = `pill ${v.cls} mono`;
    pill.innerHTML = `<span class="pdot"></span>${v.label}`;
    return pill;
}

function renderResults(data) {
    currentReport = data;
    const counts = data.summary || {};
    const findings = data.findings || [];

    // Eyebrow with filename
    const eyebrow = document.getElementById('results-eyebrow');
    if (eyebrow) {
        eyebrow.textContent = currentFilename
            ? `// analysis_complete · ${currentFilename}`
            : '// analysis_complete';
    }

    // Summary pills: verdict pill first, then severity counts
    summaryPills.innerHTML = '';
    summaryPills.appendChild(_renderVerdictPill(counts));
    [['high', 'HIGH'], ['medium', 'MED'], ['low', 'OK']].forEach(([key, fallback]) => {
        if (counts[key]) {
            const pill = document.createElement('span');
            pill.className = `pill ${key} mono`;
            const label = key === 'low' ? fallback : _riskLabel(key);
            pill.innerHTML = `<span class="pdot"></span>${counts[key]} ${label}`;
            summaryPills.appendChild(pill);
        }
    });

    // "X of Y clauses flagged" — flagged = high + medium; total = all findings
    const flagged = (counts.high || 0) + (counts.medium || 0);
    const total = counts.total || findings.length;
    const flaggedEl = document.getElementById('clauses-flagged');
    if (flaggedEl) {
        const lang = currentLang === 'de' ? 'de' : 'en';
        flaggedEl.textContent = lang === 'de'
            ? `· ${flagged} von ${total} Klauseln markiert`
            : `· ${flagged} of ${total} clauses flagged`;
    }

    // 3-cell score grid
    _renderScoreGrid(data);

    // Rate benchmark
    renderRateBenchmark(data.rate_benchmark);

    // Findings — refined .finding / .finding-head / .finding-body-collapsible / .diff-wrap / .refbox
    findingsContainer.innerHTML = '';
    (data.findings || []).forEach((f, idx) => {
        const isUncurated = f.source === 'System' || f.title === 'Analysis error';
        const card = document.createElement('div');
        card.className = `finding ${f.risk}`;

        const num = String(idx + 1).padStart(2, '0');
        const statuteLine = f.statute
            ? `<span class="finding-statute">${_escape(f.statute)}</span>`
            : (isUncurated ? `<span class="finding-statute mono dim">⚠ No curated match — AI-generated</span>` : '');

        const sevColor = f.risk === 'high' ? 'var(--red)' : f.risk === 'medium' ? 'var(--amber)' : 'var(--green)';
        const sevScore = _findingScore(f).toFixed(1);
        const sevTag = _findingTag(f);

        const head = document.createElement('div');
        head.className = 'finding-head';
        head.innerHTML = `
            <span class="finding-num mono">${num}</span>
            <div>
              <div class="finding-title">${_escape(f.title)}</div>
              ${statuteLine}
            </div>
            <div class="finding-sev" style="color:${sevColor};">
              <span class="num">${sevScore}</span><span style="color:var(--dim);" title="Derived from risk tier (high=9.0 · medium=5.5 · low=2.0)"> / 10</span>
              <div class="mono" style="font-size:9.5px;letter-spacing:0.12em;font-weight:600;margin-top:2px;">${sevTag}</div>
            </div>
            <button class="finding-toggle" aria-label="Toggle details">▾</button>
        `;

        const body = document.createElement('div');
        body.className = 'finding-body-collapsible';
        const inner = document.createElement('div');
        inner.className = 'inner';
        const innerInner = document.createElement('div');
        innerInner.className = 'finding-body-inner';
        const panel = document.createElement('div');
        panel.className = 'panel-row';

        // Body text
        const bodyHtml = f.body
            ? `<p class="what">${_escape(f.body)}</p>`
            : '';

        // Side-by-side diff (only when we have BOTH the clause AND a redline)
        let diffHtml = '';
        if (f.clause && f.redline) {
            diffHtml = `
            <div class="diff-wrap">
              <div class="diff-col">
                <div class="diff-head">
                  <span class="left mono">// original</span>
                  <span class="diff-tag mono">as-drafted</span>
                </div>
                <div class="diff-body"><span class="del">${_escape(f.clause)}</span></div>
              </div>
              <div class="diff-col">
                <div class="diff-head">
                  <span class="right mono">// recommended redline</span>
                  <span class="diff-tag mono">veritas</span>
                </div>
                <div class="diff-body"><span class="ins">${_escape(f.redline)}</span></div>
              </div>
            </div>`;
        } else if (f.clause) {
            diffHtml = `
            <div class="diff-wrap" style="grid-template-columns:1fr;">
              <div class="diff-col">
                <div class="diff-head">
                  <span class="left mono">// clause</span>
                  <span class="diff-tag mono">as-drafted</span>
                </div>
                <div class="diff-body">${_escape(f.clause)}</div>
              </div>
            </div>`;
        } else if (f.redline) {
            diffHtml = `
            <div class="diff-wrap" style="grid-template-columns:1fr;">
              <div class="diff-col">
                <div class="diff-head">
                  <span class="right mono">// recommended redline</span>
                  <span class="diff-tag mono">veritas</span>
                </div>
                <div class="diff-body"><span class="ins">${_escape(f.redline)}</span></div>
              </div>
            </div>`;
        }

        // Refboxes for statute and action
        let refHtml = '';
        if (f.statute) {
            refHtml += `
            <div class="refbox">
              <span class="lbl">statute</span>
              <span class="val">${_escape(f.statute)}</span>
            </div>`;
        }
        if (f.action) {
            refHtml += `
            <div class="refbox" style="margin-bottom:0;">
              <span class="lbl">action</span>
              <span class="val">${_escape(f.action)}</span>
            </div>`;
        }

        // Per-finding action buttons (Copy redline / Export PDF / Dismiss)
        const hasRedline = f.redline && f.redline.trim();
        const buttonsHtml = `
            <div class="action-row" style="margin-top:14px;">
              ${hasRedline ? `<button class="btn btn-ghost mono finding-btn-copy" style="padding:8px 14px;font-size:12px;">Copy redline</button>` : ''}
              <button class="btn btn-ghost mono finding-btn-pdf" style="padding:8px 14px;font-size:12px;">↓ Export PDF</button>
              <button class="btn btn-ghost mono finding-btn-dismiss" style="padding:8px 14px;font-size:12px;">✕ Dismiss</button>
            </div>`;

        panel.innerHTML = bodyHtml + diffHtml + refHtml + buttonsHtml;
        innerInner.appendChild(panel);
        inner.appendChild(innerInner);
        body.appendChild(inner);

        head.addEventListener('click', (e) => {
            // Don't toggle when clicking inside the body (e.g., copy button)
            if (e.target.closest('.action-row')) return;
            card.classList.toggle('open');
        });

        card.appendChild(head);
        card.appendChild(body);

        // Wire per-finding buttons
        const btnCopy = panel.querySelector('.finding-btn-copy');
        if (btnCopy) {
            btnCopy.addEventListener('click', (e) => {
                e.stopPropagation();
                if (!f.redline) return;
                navigator.clipboard?.writeText(f.redline).then(() => {
                    const original = btnCopy.textContent;
                    btnCopy.textContent = '✓ Copied';
                    setTimeout(() => { btnCopy.textContent = original; }, 1500);
                }).catch(() => {/* clipboard blocked */});
            });
        }
        const btnPdf = panel.querySelector('.finding-btn-pdf');
        if (btnPdf) {
            btnPdf.addEventListener('click', (e) => {
                e.stopPropagation();
                btnDownloadPdf?.click();
            });
        }
        const btnDismiss = panel.querySelector('.finding-btn-dismiss');
        if (btnDismiss) {
            btnDismiss.addEventListener('click', (e) => {
                e.stopPropagation();
                card.style.opacity = '0';
                card.style.transition = 'opacity 0.18s';
                setTimeout(() => card.remove(), 200);
            });
        }

        findingsContainer.appendChild(card);

        // Open the first finding by default
        if (idx === 0) card.classList.add('open');
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

/* ─ PDF export (server-side via /api/export/pdf) ─ */
let currentReport = null;

btnDownloadPdf.addEventListener('click', async () => {
    if (!currentReport) return;

    const user = window.firebaseAuth?.currentUser;
    if (!user) { alert('Please log in to export PDF.'); return; }

    btnDownloadPdf.disabled = true;
    btnDownloadPdf.textContent = '⏳ Generating…';

    try {
        const token = await user.getIdToken();
        const resp  = await fetch(`${API_URL}/api/export/pdf`, {
            method:  'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body:    JSON.stringify(currentReport),
        });
        if (!resp.ok) throw new Error(`Server error ${resp.status}`);
        const blob = await resp.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `veritas-analysis-${currentReport.date}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error('PDF export failed:', err);
        alert('PDF export failed. Please try again.');
    } finally {
        btnDownloadPdf.disabled = false;
        btnDownloadPdf.textContent = '↓ PDF';
    }
});

/* Expose a stable entry point so dashboard.js can render a stored
 * analysis through the same refined ResultsView used after live uploads. */
window.veritasShowAnalysis = function (filename, report) {
    if (!report) return;
    currentFilename = filename || '';
    uploadState.classList.add('hidden');
    loading.classList.add('hidden');
    renderResults(report);
};

/* ─ Reset to upload ─ */
btnReset.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    uploadState.classList.remove('hidden');
    fileInput.value = '';
    currentBrief = '';
    currentFilename = '';
    currentReport = null;
    findingsContainer.innerHTML = '';
    briefText.textContent = '';
    document.getElementById('rate-benchmark-section').classList.add('hidden');
    document.getElementById('score-grid')?.classList.add('hidden');
    uploadState.scrollIntoView({ behavior: 'smooth' });
});

/* ─ Re-run: same as reset (returns to upload state) ─ */
document.getElementById('btn-rerun')?.addEventListener('click', () => btnReset.click());

/* ─ Share: Web Share API → fallback to copying brief ─ */
document.getElementById('btn-share')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-share');
    const flash = (txt) => {
        const orig = btn.textContent;
        btn.textContent = txt;
        setTimeout(() => { btn.textContent = orig; }, 1500);
    };
    try {
        if (navigator.share) {
            await navigator.share({
                title: 'veritas — Contract Analysis',
                text: currentBrief || 'Contract analysis report',
            });
        } else if (currentBrief && navigator.clipboard) {
            await navigator.clipboard.writeText(currentBrief);
            flash('✓');
        }
    } catch { /* user cancelled */ }
});

/* ─ Brief Copy ─ */
document.getElementById('btn-brief-copy')?.addEventListener('click', () => {
    if (!currentBrief || !navigator.clipboard) return;
    const btn = document.getElementById('btn-brief-copy');
    navigator.clipboard.writeText(currentBrief).then(() => {
        const orig = btn.textContent;
        btn.textContent = '✓ Copied';
        setTimeout(() => { btn.textContent = orig; }, 1500);
    });
});

/* ─ Send to client: open mailto with brief in body ─ */
document.getElementById('btn-send-client')?.addEventListener('click', () => {
    if (!currentBrief) return;
    const subject = encodeURIComponent('Contract review — proposed redlines');
    const body = encodeURIComponent(currentBrief);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
});

/* ─ Hero walkthrough animation ─
 * Cycles through 3 reels of clause-analysis lines (extract → match → flag),
 * revealing one line every 480 ms, holding the full reel for 1.8 s, then
 * advancing to the next tab. Only runs if the hero markup is on the page. */
const _HERO_REELS = [
    [
        { key: 'file:',     v: 'tk-staffing-mar2026.pdf',                cls: 'dim' },
        { key: 'parsing:',  v: '14 clauses · 2,431 tokens',              cls: 'cite' },
        { key: 'ok',        v: '✓ Structured by GPT-4o',                 cls: 'low' },
    ],
    [
        { key: 'embed:',    v: 'text-embedding-3-small',                 cls: 'cite' },
        { key: 'matched:',  v: '7 / 14 clauses against playbook',        cls: 'cite' },
        { key: 'top hit:',  v: '"§7 SGB IV · False Self-Employment"',    cls: 'med' },
        { key: 'distance:', v: 'cosine 0.87',                            cls: 'dim' },
    ],
    [
        { key: 'risk:',     v: 'HIGH',                                   cls: 'high' },
        { key: 'clause:',   v: '§3.2 fixed hours + named superior',      cls: 'cite' },
        { key: 'statute:',  v: '§7 Abs. 1 SGB IV',                       cls: 'low' },
        { key: 'severity:', v: '9.4 / 10',                               cls: 'med' },
        { key: 'action:',   v: '→ Redline drafted',                      cls: 'dim' },
    ],
];

(function startHeroWalk() {
    const tabsEl    = document.getElementById('hero-walk-tabs');
    const contentEl = document.getElementById('hero-walk-content');
    const passEl    = document.getElementById('hero-walk-pass');
    if (!tabsEl || !contentEl) return;

    let tab = 0, step = 0;

    function updateTabs() {
        const tabSpans = tabsEl.children;
        for (let i = 0; i < tabSpans.length; i++) {
            tabSpans[i].classList.toggle('on', i === tab);
        }
        if (passEl) passEl.textContent = `PASS ${tab + 1}/${_HERO_REELS.length}`;
    }

    function clearWalk() {
        contentEl.innerHTML = '';
    }

    function appendLine(row, index) {
        const div = document.createElement('div');
        div.className = `walk-row clause-line ${row.cls || ''}`;
        div.innerHTML =
            `<span class="lineno mono dim">${String(index + 1).padStart(2, '0')}</span>` +
            `<span class="key mono text-purple">${_escape(row.key)}</span>` +
            `<span class="v mono">${_escape(row.v)}</span>`;
        contentEl.appendChild(div);
    }

    function appendCursor() {
        const cur = document.createElement('div');
        cur.className = 'walk-cursor cursor-blink';
        contentEl.appendChild(cur);
    }

    function tick() {
        const reel = _HERO_REELS[tab];
        if (step < reel.length) {
            appendLine(reel[step], step);
            step++;
            setTimeout(tick, 480);
        } else {
            appendCursor();
            setTimeout(() => {
                step = 0;
                tab = (tab + 1) % _HERO_REELS.length;
                clearWalk();
                updateTabs();
                setTimeout(tick, 480);
            }, 1800);
        }
    }

    updateTabs();
    setTimeout(tick, 480);
})();
