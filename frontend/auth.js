import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import {
    getAuth,
    signInWithPopup,
    GoogleAuthProvider,
    onAuthStateChanged,
    signOut,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { firebaseConfig } from './firebase-config.js';

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Expose auth to window so other scripts can use it to get the token
window.firebaseAuth = auth;

document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.querySelector('.btn-login');
    const modal = document.getElementById('auth-modal');
    
    // If no login button (e.g., on dashboard), just handle state
    if (!loginBtn) return;

    // Modal elements
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const authForm = document.getElementById('auth-form');
    const emailInput = document.getElementById('auth-email');
    const passwordInput = document.getElementById('auth-password');
    const authSubmit = document.getElementById('auth-submit');
    const authError = document.getElementById('auth-error');
    const linkToggleMode = document.getElementById('link-toggle-mode');
    const linkForgotPassword = document.getElementById('link-forgot-password');
    const btnGoogleLogin = document.getElementById('btn-google-login');

    let isSignUpMode = false;

    // --- State Listener ---
    onAuthStateChanged(auth, (user) => {
        if (user) {
            // Logged in
            loginBtn.textContent = "Dashboard";
            loginBtn.removeAttribute('data-i18n');
            loginBtn.onclick = () => { window.location.href = "dashboard.html"; };
            if (modal) modal.classList.add('hidden');
        } else {
            // Logged out
            loginBtn.textContent = "Log In";
            loginBtn.setAttribute('data-i18n', 'nav.login');
            loginBtn.onclick = () => {
                if (modal) openModal();
            };
        }
    });

    // --- Modal Logic ---
    function openModal() {
        modal.classList.remove('hidden');
        resetModalState();
    }

    // Expose so other modules can trigger the login modal
    window.openAuthModal = openModal;

    function closeModal() {
        modal.classList.add('hidden');
    }

    function showError(message) {
        authError.textContent = message;
        authError.classList.remove('hidden');
    }

    function hideError() {
        authError.textContent = '';
        authError.classList.add('hidden');
    }

    function resetModalState() {
        isSignUpMode = false;
        modalTitle.textContent = "Log In";
        authSubmit.textContent = "Log In";
        linkToggleMode.textContent = "Create an account";
        passwordInput.style.display = "block";
        passwordInput.required = true;
        linkForgotPassword.style.display = "inline";
        hideError();
        authForm.reset();
    }

    if (modalClose) modalClose.onclick = closeModal;

    // Close on overlay click
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }

    // Toggle Sign Up / Log In
    if (linkToggleMode) {
        linkToggleMode.onclick = (e) => {
            e.preventDefault();
            isSignUpMode = !isSignUpMode;
            hideError();
            if (isSignUpMode) {
                modalTitle.textContent = "Create Account";
                authSubmit.textContent = "Sign Up";
                linkToggleMode.textContent = "Already have an account? Log In";
                passwordInput.style.display = "block";
                passwordInput.required = true;
                linkForgotPassword.style.display = "none";
            } else {
                resetModalState();
            }
        };
    }

    // Forgot Password
    if (linkForgotPassword) {
        linkForgotPassword.onclick = (e) => {
            e.preventDefault();
            const email = emailInput.value.trim();
            if (!email) {
                showError("Please enter your email address first.");
                return;
            }
            sendPasswordResetEmail(auth, email)
                .then(() => {
                    showError("Password reset email sent! Check your inbox.");
                    authError.style.color = "var(--green)";
                    authError.style.background = "rgba(74,222,128,0.1)";
                    setTimeout(() => {
                        authError.style.color = "";
                        authError.style.background = "";
                    }, 5000);
                })
                .catch((error) => {
                    showError(error.message);
                });
        };
    }

    // Form Submit (Email/Password)
    if (authForm) {
        authForm.onsubmit = (e) => {
            e.preventDefault();
            hideError();
            
            const email = emailInput.value.trim();
            const password = passwordInput.value;

            authSubmit.disabled = true;
            authSubmit.textContent = "Please wait...";

            if (isSignUpMode) {
                createUserWithEmailAndPassword(auth, email, password)
                    .catch((error) => {
                        showError(getFriendlyErrorMessage(error.code, error.message));
                        authSubmit.disabled = false;
                        authSubmit.textContent = "Sign Up";
                    });
            } else {
                signInWithEmailAndPassword(auth, email, password)
                    .catch((error) => {
                        showError(getFriendlyErrorMessage(error.code, error.message));
                        authSubmit.disabled = false;
                        authSubmit.textContent = "Log In";
                    });
            }
        };
    }

    // Google Sign In
    if (btnGoogleLogin) {
        btnGoogleLogin.onclick = () => {
            hideError();
            signInWithPopup(auth, googleProvider).catch((error) => {
                showError(getFriendlyErrorMessage(error.code, error.message));
            });
        };
    }

    // Helper for friendly error messages
    function getFriendlyErrorMessage(code, defaultMessage) {
        switch (code) {
            case 'auth/invalid-email': return 'Invalid email address format.';
            case 'auth/user-disabled': return 'This account has been disabled.';
            case 'auth/user-not-found': return 'No account found with this email.';
            case 'auth/wrong-password': return 'Incorrect password.';
            case 'auth/email-already-in-use': return 'An account already exists with this email.';
            case 'auth/weak-password': return 'Password is too weak (minimum 6 characters).';
            case 'auth/invalid-credential': return 'Invalid login credentials.';
            default: return defaultMessage;
        }
    }
});
