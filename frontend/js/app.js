const App = {
    currentPage: 'dashboard',

    init() {
        Auth.init();
        if (Auth.isLoggedIn()) {
            App.showApp();
        } else {
            App.showLogin();
        }
        // Nav link clicks
        document.querySelectorAll('.nav-item').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                App.navigate(page);
            });
        });
        // Modal close handlers
        document.getElementById('modal-close-btn').addEventListener('click', App.closeModal);
        document.getElementById('modal-cancel-btn').addEventListener('click', App.closeModal);
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') App.closeModal();
        });
    },

    showLogin() {
        document.getElementById('login-page').classList.remove('hidden');
        document.getElementById('app-layout').classList.add('hidden');
        document.getElementById('login-username').value = '';
        document.getElementById('login-password').value = '';
        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.classList.add('hidden');
    },

    showApp() {
        document.getElementById('login-page').classList.add('hidden');
        document.getElementById('app-layout').classList.remove('hidden');
        const user = API.getUser();
        if (user) {
            const sidebarName = document.getElementById('sidebar-user-name');
            if (sidebarName) sidebarName.textContent = user.full_name;
            
            const sidebarRole = document.getElementById('sidebar-user-role');
            if (sidebarRole) sidebarRole.textContent = user.role.replace('_', ' ');
            
            const initials = user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
            const userAvatar = document.getElementById('user-avatar');
            if (userAvatar) userAvatar.textContent = initials;
            
            const headerAvatar = document.getElementById('header-avatar');
            if (headerAvatar) headerAvatar.textContent = initials;
            
            const headerRole = document.getElementById('header-user-role');
            if (headerRole) headerRole.textContent = user.role.replace('_', ' ');
            
            // RBAC: hide nav items based on role
            App.applyRBAC(user.role);
        }
        App.navigate('dashboard');
    },

    applyRBAC(role) {
        // Show all nav links first
        document.querySelectorAll('.nav-item').forEach(l => l.style.display = 'flex');
        // Drivers can only see dashboard, trips (read)
        if (role === 'driver') {
            ['maintenance', 'fuel', 'expenses'].forEach(page => {
                const link = document.querySelector(`.nav-item[data-page='${page}']`);
                if (link) link.style.display = 'none';
            });
        }
    },

    navigate(page) {
        App.currentPage = page;
        // Update active nav
        document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
        const activeLink = document.querySelector(`.nav-item[data-page='${page}']`);
        if (activeLink) activeLink.classList.add('active');
        // Update page title
        const titles = { dashboard:'Dashboard', vehicles:'Vehicles', drivers:'Drivers', trips:'Trips', maintenance:'Maintenance', fuel:'Fuel Logs', expenses:'Expenses' };
        document.getElementById('page-title').textContent = titles[page] || page;
        // Render page
        const pages = { dashboard: Dashboard, vehicles: Vehicles, drivers: Drivers, trips: Trips, maintenance: Maintenance, fuel: Fuel, expenses: Expenses };
        if (pages[page]) pages[page].render();
    },

    // ── Modal helpers ──
    openModal(title, bodyHtml, onSave) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHtml;
        document.getElementById('modal-overlay').classList.remove('hidden');
        const saveBtn = document.getElementById('modal-save-btn');
        // Clone to remove old listeners
        const newBtn = saveBtn.cloneNode(true);
        saveBtn.parentNode.replaceChild(newBtn, saveBtn);
        newBtn.id = 'modal-save-btn';
        newBtn.addEventListener('click', async () => {
            try {
                newBtn.disabled = true;
                newBtn.textContent = 'Saving...';
                await onSave();
            } catch (err) {
                App.toast(err.message, 'error');
            } finally {
                newBtn.disabled = false;
                newBtn.textContent = 'Save';
            }
        });
    },
    closeModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    },

    // ── Toast notifications ──
    toast(message, type = 'info') {
        const container = document.getElementById('toast-container') || App.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">&times;</button>`;
        container.appendChild(toast);
        setTimeout(() => { if (toast.parentElement) toast.remove(); }, 4000);
    },
    createToastContainer() {
        const c = document.createElement('div');
        c.id = 'toast-container';
        document.body.appendChild(c);
        return c;
    },

    // ── Status badge helper ──
    badge(status) {
        const classes = {
            available: 'badge-available', on_trip: 'badge-on-trip', in_shop: 'badge-in-shop', retired: 'badge-retired',
            on_duty: 'badge-on-duty', off_duty: 'badge-off-duty', suspended: 'badge-suspended',
            draft: 'badge-draft', dispatched: 'badge-dispatched', completed: 'badge-completed', cancelled: 'badge-cancelled',
            scheduled: 'badge-scheduled', in_progress: 'badge-in-progress',
            fuel: 'badge-fuel', maintenance: 'badge-maintenance', salary: 'badge-salary',
            insurance: 'badge-insurance', toll: 'badge-toll', other: 'badge-other',
        };
        const label = (status || '').replace(/_/g, ' ');
        return `<span class="badge ${classes[status] || ''}">${label}</span>`;
    },
};

// ── Boot ──
document.addEventListener('DOMContentLoaded', () => App.init());
