const Auth = {
    init() {
        const form = document.getElementById('login-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                Auth.login();
            });
        }
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => Auth.logout());
        }

        // Forgot password view handlers
        const forgotTrigger = document.getElementById('forgot-pwd-trigger');
        if (forgotTrigger) {
            forgotTrigger.addEventListener('click', (e) => {
                e.preventDefault();
                Auth.showForgotPassword();
            });
        }

        document.querySelectorAll('.back-to-login-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                Auth.showLoginView();
            });
        });

        const forgotForm = document.getElementById('forgot-form');
        if (forgotForm) {
            forgotForm.addEventListener('submit', (e) => {
                e.preventDefault();
                Auth.forgotPassword();
            });
        }

        const errorClose = document.getElementById('login-error-close');
        if (errorClose) {
            errorClose.addEventListener('click', () => {
                const errorEl = document.getElementById('login-error');
                if (errorEl) errorEl.classList.add('hidden');
                if (Auth._errorTimeout) clearTimeout(Auth._errorTimeout);
            });
        }
    },

    showForgotPassword() {
        const loginContainer = document.getElementById('login-form-container');
        const forgotContainer = document.getElementById('forgot-password-container');
        const successContainer = document.getElementById('forgot-success-container');
        const errorEl = document.getElementById('login-error');

        if (loginContainer) loginContainer.classList.add('hidden');
        if (successContainer) successContainer.classList.add('hidden');
        if (forgotContainer) forgotContainer.classList.remove('hidden');
        if (errorEl) errorEl.classList.add('hidden');
        if (Auth._errorTimeout) clearTimeout(Auth._errorTimeout);
    },

    showLoginView() {
        const loginContainer = document.getElementById('login-form-container');
        const forgotContainer = document.getElementById('forgot-password-container');
        const successContainer = document.getElementById('forgot-success-container');
        const errorEl = document.getElementById('login-error');

        if (forgotContainer) forgotContainer.classList.add('hidden');
        if (successContainer) successContainer.classList.add('hidden');
        if (loginContainer) loginContainer.classList.remove('hidden');
        if (errorEl) errorEl.classList.add('hidden');
        if (Auth._errorTimeout) clearTimeout(Auth._errorTimeout);
    },

    showError(message) {
        const errorEl = document.getElementById('login-error');
        const errorTextEl = document.getElementById('login-error-text');
        if (errorEl) {
            if (errorTextEl) errorTextEl.textContent = message;
            errorEl.classList.remove('hidden');

            if (Auth._errorTimeout) {
                clearTimeout(Auth._errorTimeout);
            }
            Auth._errorTimeout = setTimeout(() => {
                errorEl.classList.add('hidden');
            }, 4000);
        }
    },

    async login() {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.classList.add('hidden');
        if (Auth._errorTimeout) clearTimeout(Auth._errorTimeout);

        if (!username || !password) {
            Auth.showError('Please enter both fields');
            return;
        }
        try {
            const data = await API.request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
            if (data && data.token) {
                API.setToken(data.token);
                API.setUser(data.user);
                App.showApp();
            }
        } catch (err) {
            Auth.showError(err.message || 'Login failed');
        }
    },

    async forgotPassword() {
        const email = document.getElementById('forgot-email').value.trim();
        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.classList.add('hidden');
        if (Auth._errorTimeout) clearTimeout(Auth._errorTimeout);

        // Simple client-side validation for email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email || !emailRegex.test(email)) {
            Auth.showError('Please enter a valid email address');
            return;
        }

        try {
            const data = await API.post('/auth/forgot-password', { email });
            if (data) {
                const forgotContainer = document.getElementById('forgot-password-container');
                const successContainer = document.getElementById('forgot-success-container');
                if (forgotContainer) forgotContainer.classList.add('hidden');
                if (successContainer) successContainer.classList.remove('hidden');
                if (errorEl) errorEl.classList.add('hidden');
            }
        } catch (err) {
            Auth.showError(err.message || 'Email verification failed');
        }
    },

    logout() {
        API.clearToken();
        App.showLogin();
    },
    isLoggedIn() { return !!API.token; },
    getRole() { const u = API.getUser(); return u ? u.role : null; },
    hasRole(...roles) { return roles.includes(Auth.getRole()); },
};
