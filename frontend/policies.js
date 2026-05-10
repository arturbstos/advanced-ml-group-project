/* Cookie banner + Privacy modal — vanilla JS port of design/components/policies.jsx
 *
 * - Cookie banner: shows on first visit; persists choice in localStorage
 *   under 'veritas-cookies'. Clicking either action dismisses it.
 * - Privacy modal: opens from any element with id="link-privacy" (analyzer
 *   privacy notice), id="cookie-policy-link" (banner), or via a custom
 *   'open-privacy' event. Closes on overlay click, close button, or Escape.
 */

const COOKIE_KEY = 'veritas-cookies';

const cookieBanner = document.getElementById('cookie-banner');
const cookieAccept = document.getElementById('cookie-accept');
const cookieReject = document.getElementById('cookie-reject');
const cookiePolicyLink = document.getElementById('cookie-policy-link');

const privacyModal = document.getElementById('privacy-modal');
const privacyClose = document.getElementById('privacy-modal-close');
const privacyTrigger = document.getElementById('link-privacy');

function showCookieBanner() {
    if (!cookieBanner) return;
    let stored = null;
    try { stored = localStorage.getItem(COOKIE_KEY); } catch {}
    if (!stored) cookieBanner.classList.remove('hidden');
}

function dismissCookieBanner(choice) {
    try { localStorage.setItem(COOKIE_KEY, choice); } catch {}
    cookieBanner?.classList.add('hidden');
}

function openPrivacyModal() {
    privacyModal?.classList.remove('hidden');
}

function closePrivacyModal() {
    privacyModal?.classList.add('hidden');
}

cookieAccept?.addEventListener('click', () => dismissCookieBanner('all'));
cookieReject?.addEventListener('click', () => dismissCookieBanner('necessary'));
cookiePolicyLink?.addEventListener('click', (e) => { e.preventDefault(); openPrivacyModal(); });

privacyTrigger?.addEventListener('click', (e) => { e.preventDefault(); openPrivacyModal(); });
privacyClose?.addEventListener('click', closePrivacyModal);
privacyModal?.addEventListener('click', (e) => {
    if (e.target === privacyModal) closePrivacyModal();
});

// Allow other modules to dispatch 'open-privacy'
window.addEventListener('open-privacy', openPrivacyModal);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePrivacyModal();
});

showCookieBanner();
