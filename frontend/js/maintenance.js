const Maintenance = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager', 'safety_officer');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Maintenance</h2>
                    <p class="text-muted">Track vehicle maintenance and repairs</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Maintenance.openCreate()">+ Log Maintenance</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="maintenance-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Maintenance.loadTable();
    },

    async loadTable() {
        try {
            const records = await API.get('/maintenance');
            const area = document.getElementById('maintenance-table-area');
            if (!records || records.length === 0) { area.innerHTML = '<p class="empty-state">No maintenance records found.</p>'; return; }
            const canEdit = Auth.hasRole('fleet_manager', 'safety_officer');
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Vehicle</th><th>Date</th><th>Description</th><th>Cost (₹)</th><th>Mechanic</th><th>Status</th>${canEdit ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${records.map(m => {
                    let actions = '';
                    if (canEdit) {
                        if (m.state === 'scheduled') {
                            actions = `
                                <button class="btn btn-sm btn-primary" onclick="Maintenance.start('${m.id}')">Start</button>
                                <button class="btn btn-sm btn-outline" onclick="Maintenance.openEdit('${m.id}')">Edit</button>
                                <button class="btn btn-sm btn-danger" onclick="Maintenance.remove('${m.id}')">Delete</button>`;
                        } else if (m.state === 'in_progress') {
                            actions = `
                                <button class="btn btn-sm btn-success" onclick="Maintenance.completeJob('${m.id}')">Complete</button>
                                <button class="btn btn-sm btn-outline" onclick="Maintenance.openEdit('${m.id}')">Edit</button>`;
                        } else {
                            actions = `<button class="btn btn-sm btn-outline" onclick="Maintenance.openEdit('${m.id}')">Edit</button>`;
                        }
                    }
                    return `<tr>
                        <td><strong>${m.vehicle_name || '-'}</strong></td>
                        <td>${m.date || '-'}</td>
                        <td>${m.description || '-'}</td>
                        <td>${m.cost != null ? '₹' + Number(m.cost).toLocaleString('en-IN') : '-'}</td>
                        <td>${m.mechanic || '-'}</td>
                        <td>${App.badge(m.state)}</td>
                        ${canEdit ? `<td class="actions-cell">${actions}</td>` : ''}
                    </tr>`;
                }).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('maintenance-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },

    async openCreate() {
        try {
            const vehicles = await API.get('/vehicles');
            App.openModal('Log Maintenance', Maintenance.formHtml({}, vehicles || []), async () => {
                const data = Maintenance.getCreateFormData();
                await API.post('/maintenance', data);
                App.closeModal();
                App.toast('Maintenance record created', 'success');
                await Maintenance.loadTable();
            });
        } catch (err) { App.toast('Failed to load vehicles: ' + err.message, 'error'); }
    },

    async openEdit(id) {
        try {
            const [record, vehicles] = await Promise.all([
                API.get(`/maintenance/${id}`),
                API.get('/vehicles'),
            ]);
            App.openModal('Edit Maintenance', Maintenance.formHtml(record, vehicles || []), async () => {
                const data = Maintenance.getFormData();
                await API.put(`/maintenance/${id}`, data);
                App.closeModal();
                App.toast('Maintenance record updated', 'success');
                await Maintenance.loadTable();
            });
        } catch (err) { App.toast('Failed to load record: ' + err.message, 'error'); }
    },

    async remove(id) {
        if (!confirm('Delete this maintenance record?')) return;
        await API.delete(`/maintenance/${id}`);
        App.toast('Maintenance record deleted', 'success');
        await Maintenance.loadTable();
    },

    async start(id) {
        try {
            await API.post(`/maintenance/${id}/start`);
            App.toast('Maintenance started', 'success');
            await Maintenance.loadTable();
        } catch (err) { App.toast(err.message, 'error'); }
    },

    async completeJob(id) {
        try {
            await API.post(`/maintenance/${id}/complete`);
            App.toast('Maintenance completed', 'success');
            await Maintenance.loadTable();
        } catch (err) { App.toast(err.message, 'error'); }
    },

    formHtml(m = {}, vehicles = []) {
        return `
            <div class="form-group"><label>Vehicle</label><select id="f-vehicle">
                <option value="">-- Select Vehicle --</option>
                ${vehicles.map(v => `<option value="${v.id}" ${m.vehicle_id === v.id ? 'selected' : ''}>${v.name} (${v.registration_number})</option>`).join('')}
            </select></div>
            <div class="grid-2">
                <div class="form-group"><label>Date</label><input type="date" id="f-date" value="${m.date || ''}"></div>
                <div class="form-group"><label>Cost (₹)</label><input type="number" id="f-cost" value="${m.cost || ''}" step="0.01" placeholder="0"></div>
            </div>
            <div class="form-group"><label>Description</label><textarea id="f-description" rows="3" placeholder="Describe the maintenance work...">${m.description || ''}</textarea></div>
            <div class="grid-2">
                <div class="form-group"><label>Mechanic</label><input type="text" id="f-mechanic" value="${m.mechanic || ''}" placeholder="e.g. Suresh Auto Works"></div>
                <div class="form-group"><label>Status</label><select id="f-state">
                    <option value="scheduled" ${m.state==='scheduled'?'selected':''}>Scheduled</option>
                    <option value="in_progress" ${m.state==='in_progress'?'selected':''}>In Progress</option>
                    <option value="completed" ${m.state==='completed'?'selected':''}>Completed</option>
                </select></div>
            </div>`;
    },

    getFormData() {
        return {
            description: document.getElementById('f-description').value,
            cost: parseFloat(document.getElementById('f-cost').value) || 0,
            mechanic: document.getElementById('f-mechanic').value,
            state: document.getElementById('f-state').value,
        };
    },

    getCreateFormData() {
        return {
            vehicle_id: document.getElementById('f-vehicle').value || "",
            date: document.getElementById('f-date').value || "",
            description: document.getElementById('f-description').value,
            cost: parseFloat(document.getElementById('f-cost').value) || 0,
            mechanic: document.getElementById('f-mechanic').value,
            state: document.getElementById('f-state').value,
        };
    },
};
