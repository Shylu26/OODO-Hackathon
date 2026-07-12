const Fuel = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager', 'financial_analyst');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Fuel Logs</h2>
                    <p class="text-muted">Track fuel consumption and costs</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Fuel.openCreate()">+ Add Fuel Log</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="fuel-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Fuel.loadTable();
    },

    async loadTable() {
        try {
            const logs = await API.get('/fuel');
            const area = document.getElementById('fuel-table-area');
            if (!logs || logs.length === 0) { area.innerHTML = '<p class="empty-state">No fuel logs found.</p>'; return; }
            const canEdit = Auth.hasRole('fleet_manager', 'financial_analyst');
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Vehicle</th><th>Date</th><th>Liters</th><th>Cost (₹)</th><th>Cost/L</th><th>Odometer (km)</th><th>Station</th>${canEdit ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${logs.map(f => {
                    const costPerLiter = f.liters > 0 ? (f.cost / f.liters).toFixed(2) : '-';
                    return `<tr>
                        <td><strong>${f.vehicle_name || '-'}</strong></td>
                        <td>${f.date || '-'}</td>
                        <td>${f.liters != null ? f.liters.toFixed(1) : '-'}</td>
                        <td>${f.cost != null ? '₹' + Number(f.cost).toLocaleString('en-IN') : '-'}</td>
                        <td>${costPerLiter !== '-' ? '₹' + costPerLiter : '-'}</td>
                        <td>${f.odometer != null ? Number(f.odometer).toLocaleString('en-IN') : '-'}</td>
                        <td>${f.station || '-'}</td>
                        ${canEdit ? `<td class="actions-cell">
                            <button class="btn btn-sm btn-outline" onclick="Fuel.openEdit('${f.id}')">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="Fuel.remove('${f.id}')">Delete</button>
                        </td>` : ''}
                    </tr>`;
                }).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('fuel-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },

    async openCreate() {
        try {
            const vehicles = await API.get('/vehicles');
            App.openModal('Add Fuel Log', Fuel.formHtml({}, vehicles || []), async () => {
                const data = Fuel.getFormData();
                await API.post('/fuel', data);
                App.closeModal();
                App.toast('Fuel log created', 'success');
                await Fuel.loadTable();
            });
        } catch (err) { App.toast('Failed to load vehicles: ' + err.message, 'error'); }
    },

    async openEdit(id) {
        try {
            const [log, vehicles] = await Promise.all([
                API.get(`/fuel/${id}`),
                API.get('/vehicles'),
            ]);
            App.openModal('Edit Fuel Log', Fuel.formHtml(log, vehicles || []), async () => {
                const data = Fuel.getFormData();
                await API.put(`/fuel/${id}`, data);
                App.closeModal();
                App.toast('Fuel log updated', 'success');
                await Fuel.loadTable();
            });
        } catch (err) { App.toast('Failed to load fuel log: ' + err.message, 'error'); }
    },

    async remove(id) {
        if (!confirm('Delete this fuel log?')) return;
        await API.delete(`/fuel/${id}`);
        App.toast('Fuel log deleted', 'success');
        await Fuel.loadTable();
    },

    formHtml(f = {}, vehicles = []) {
        return `
            <div class="form-group"><label>Vehicle</label><select id="f-vehicle">
                <option value="">-- Select Vehicle --</option>
                ${vehicles.map(v => `<option value="${v.id}" ${f.vehicle_id === v.id ? 'selected' : ''}>${v.name} (${v.registration_number})</option>`).join('')}
            </select></div>
            <div class="grid-2">
                <div class="form-group"><label>Date</label><input type="date" id="f-date" value="${f.date || ''}"></div>
                <div class="form-group"><label>Liters</label><input type="number" id="f-liters" value="${f.liters || ''}" step="0.1" placeholder="0"></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Cost (₹)</label><input type="number" id="f-cost" value="${f.cost || ''}" step="0.01" placeholder="0"></div>
                <div class="form-group"><label>Odometer (km)</label><input type="number" id="f-odometer" value="${f.odometer || ''}" step="0.1" placeholder="0"></div>
            </div>
            <div class="form-group"><label>Station</label><input type="text" id="f-station" value="${f.station || ''}" placeholder="e.g. Indian Oil, Andheri"></div>`;
    },

    getFormData() {
        return {
            vehicle_id: document.getElementById('f-vehicle').value || "",
            date: document.getElementById('f-date').value || "",
            liters: parseFloat(document.getElementById('f-liters').value) || 0,
            cost: parseFloat(document.getElementById('f-cost').value) || 0,
            odometer: parseFloat(document.getElementById('f-odometer').value) || 0,
            station: document.getElementById('f-station').value,
        };
    },
};
