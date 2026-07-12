const API = {
    baseUrl: '/api',
    token: localStorage.getItem('transit_token'),

    setToken(token) { this.token = token; localStorage.setItem('transit_token', token); },
    clearToken() { this.token = null; localStorage.removeItem('transit_token'); localStorage.removeItem('transit_user'); },
    getUser() { const u = localStorage.getItem('transit_user'); return u ? JSON.parse(u) : null; },
    setUser(user) { localStorage.setItem('transit_user', JSON.stringify(user)); },

    async request(endpoint, options = {}) {
        // Ensure trailing slash to avoid FastAPI 307 redirect which drops POST body
        let normalizedEndpoint = endpoint;
        if (!normalizedEndpoint.endsWith('/')) {
            normalizedEndpoint += '/';
        }
        const url = this.baseUrl + normalizedEndpoint;
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
        try {
            const res = await fetch(url, { ...options, headers, redirect: 'follow' });
            if (res.status === 401 && endpoint !== '/auth/login') {
                Auth.logout();
                return null;
            }
            const data = await res.json();
            if (!res.ok) {
                let msg = 'Request failed';
                if (data && data.detail) {
                    if (Array.isArray(data.detail)) {
                        msg = data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                    } else if (typeof data.detail === 'object') {
                        msg = JSON.stringify(data.detail);
                    } else {
                        msg = data.detail;
                    }
                }
                throw new Error(msg);
            }
            return data;
        } catch (err) { throw err; }
    },
    get(endpoint) { return this.request(endpoint); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) }); },
    put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(body) }); },
    delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },
};
