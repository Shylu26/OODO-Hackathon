const Trips = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Trips</h2>
                    <p class="text-muted">Schedule and track fleet trips</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Trips.openCreate()">+ Create Trip</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="trips-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Trips.loadTable();
    },

    async loadTable() {
        try {
            const trips = await API.get('/trips');
            const area = document.getElementById('trips-table-area');
            if (!trips || trips.length === 0) { area.innerHTML = '<p class="empty-state">No trips found.</p>'; return; }
            const canManage = Auth.hasRole('fleet_manager');
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Trip #</th><th>Vehicle</th><th>Driver</th><th>Route</th><th>Cargo (kg)</th><th>Distance (km)</th><th>Revenue (₹)</th><th>Status</th>${canManage ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${trips.map(t => {
                    let actions = '';
                    if (canManage) {
                        if (t.state === 'draft') {
                            actions = `
                                <button class="btn btn-sm btn-primary" onclick="Trips.dispatch('${t.id}')">Dispatch</button>
                                <button class="btn btn-sm btn-outline" onclick="Trips.openEdit('${t.id}')">Edit</button>
                                <button class="btn btn-sm btn-danger" onclick="Trips.cancel('${t.id}')">Cancel</button>`;
                        } else if (t.state === 'dispatched') {
                            actions = `
                                <button class="btn btn-sm btn-success" onclick="Trips.complete('${t.id}')">Complete</button>
                                <button class="btn btn-sm btn-danger" onclick="Trips.cancel('${t.id}')">Cancel</button>`;
                        }
                    }
                    return `<tr>
                        <td><strong>${t.trip_number}</strong></td>
                        <td>${t.vehicle_name || '-'}</td>
                        <td>${t.driver_name || '-'}</td>
                        <td>${t.origin} → ${t.destination}</td>
                        <td>${t.cargo_weight || 0}</td>
                        <td>${t.distance_km || 0}</td>
                        <td>${t.revenue != null ? '₹' + Number(t.revenue).toLocaleString('en-IN') : '-'}</td>
                        <td>${App.badge(t.state)}</td>
                        ${canManage ? `<td class="actions-cell">${actions}</td>` : ''}
                    </tr>`;
                }).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('trips-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },

    async openCreate() {
        try {
            const [vehicles, drivers] = await Promise.all([
                API.get('/vehicles'),
                API.get('/drivers'),
            ]);
            const availableVehicles = (vehicles || []).filter(v => v.status === 'available');
            const availableDrivers = (drivers || []).filter(d => d.duty_status === 'available' && (!d.license_expiry || new Date(d.license_expiry) >= new Date()));
            App.openModal('Create Trip', Trips.formHtml({}, availableVehicles, availableDrivers), async () => {
                const data = Trips.getFormData();
                await API.post('/trips', data);
                App.closeModal();
                App.toast('Trip created successfully', 'success');
                await Trips.loadTable();
            });
        } catch (err) { App.toast('Failed to load form data: ' + err.message, 'error'); }
    },

    async openEdit(id) {
        try {
            const [trip, vehicles, drivers] = await Promise.all([
                API.get(`/trips/${id}`),
                API.get('/vehicles'),
                API.get('/drivers'),
            ]);
            const availableVehicles = (vehicles || []).filter(v => v.status === 'available' || v.id === trip.vehicle_id);
            const availableDrivers = (drivers || []).filter(d => (d.duty_status === 'available' && (!d.license_expiry || new Date(d.license_expiry) >= new Date())) || d.id === trip.driver_id);
            App.openModal('Edit Trip', Trips.formHtml(trip, availableVehicles, availableDrivers), async () => {
                const data = Trips.getFormData();
                await API.put(`/trips/${id}`, data);
                App.closeModal();
                App.toast('Trip updated', 'success');
                await Trips.loadTable();
            });
        } catch (err) { App.toast('Failed to load trip: ' + err.message, 'error'); }
    },

    async dispatch(id) {
        try {
            await API.post(`/trips/${id}/dispatch`);
            App.toast('Trip dispatched', 'success');
            await Trips.loadTable();
        } catch (err) { App.toast(err.message, 'error'); }
    },

    async complete(id) {
        try {
            await API.post(`/trips/${id}/complete`);
            App.toast('Trip completed', 'success');
            await Trips.loadTable();
        } catch (err) { App.toast(err.message, 'error'); }
    },

    async cancel(id) {
        if (!confirm('Cancel this trip?')) return;
        try {
            await API.post(`/trips/${id}/cancel`);
            App.toast('Trip cancelled', 'success');
            await Trips.loadTable();
        } catch (err) { App.toast(err.message, 'error'); }
    },

    formHtml(t = {}, vehicles = [], drivers = []) {
        return `
            <div class="grid-2">
                <div class="form-group"><label>Vehicle</label><select id="f-vehicle">
                    <option value="">-- Select Vehicle --</option>
                    ${vehicles.map(v => `<option value="${v.id}" ${t.vehicle_id === v.id ? 'selected' : ''}>${v.name} (${v.registration_number})</option>`).join('')}
                </select></div>
                <div class="form-group"><label>Driver</label><select id="f-driver">
                    <option value="">-- Select Driver --</option>
                    ${drivers.map(d => `<option value="${d.id}" ${t.driver_id === d.id ? 'selected' : ''}>${d.full_name} (${d.employee_id || 'N/A'})</option>`).join('')}
                </select></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Origin</label><input type="text" id="f-origin" value="${t.origin || ''}" placeholder="e.g. Mumbai"></div>
                <div class="form-group"><label>Destination</label><input type="text" id="f-destination" value="${t.destination || ''}" placeholder="e.g. Pune"></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Scheduled Date</label><input type="date" id="f-scheduled" value="${t.scheduled_date || ''}"></div>
                <div class="form-group"><label>Cargo Weight (kg)</label><input type="number" id="f-cargo" value="${t.cargo_weight || ''}" step="0.1" placeholder="0"></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Distance (km)</label><input type="number" id="f-distance" value="${t.distance_km || ''}" step="0.1" placeholder="0"></div>
                <div class="form-group"><label>Revenue (₹)</label><input type="number" id="f-revenue" value="${t.revenue || ''}" step="0.01" placeholder="0"></div>
            </div>`;
    },

    getFormData() {
        return {
            vehicle_id: document.getElementById('f-vehicle').value || null,
            driver_id: document.getElementById('f-driver').value || null,
            origin: document.getElementById('f-origin').value,
            destination: document.getElementById('f-destination').value,
            scheduled_date: document.getElementById('f-scheduled').value || null,
            cargo_weight: parseFloat(document.getElementById('f-cargo').value) || 0,
            distance_km: parseFloat(document.getElementById('f-distance').value) || 0,
            revenue: parseFloat(document.getElementById('f-revenue').value) || 0,
        };
    },
};
