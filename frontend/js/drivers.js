const Drivers = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager', 'safety_officer');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Drivers</h2>
                    <p class="text-muted">Manage driver records and certifications</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Drivers.openCreate()">+ Add Driver</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="drivers-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Drivers.loadTable();
    },

    async loadTable() {
        try {
            const drivers = await API.get('/drivers');
            const area = document.getElementById('drivers-table-area');
            if (!drivers || drivers.length === 0) { area.innerHTML = '<p class="empty-state">No drivers found.</p>'; return; }
            const canEdit = Auth.hasRole('fleet_manager', 'safety_officer');
            const now = new Date();
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Name</th><th>Employee ID</th><th>License #</th><th>License Expiry</th><th>Safety Score</th><th>Duty Status</th>${canEdit ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${drivers.map(d => {
                    const expiry = d.license_expiry ? new Date(d.license_expiry) : null;
                    const isExpired = expiry && expiry < now;
                    const score = d.safety_score != null ? d.safety_score : 0;
                    const scoreColor = score >= 80 ? 'var(--clr-success)' : score >= 50 ? 'var(--clr-warning)' : 'var(--clr-danger)';
                    return `<tr>
                        <td><strong>${d.full_name}</strong></td>
                        <td><code>${d.employee_id || '-'}</code></td>
                        <td>${d.license_number || '-'}</td>
                        <td class="${isExpired ? 'text-danger' : ''}">${d.license_expiry || '-'}${isExpired ? ' ⚠️ Expired' : ''}</td>
                        <td>
                            <div class="score-cell">
                                <div class="progress-bar"><div class="progress-fill" style="width:${score}%;background:${scoreColor}"></div></div>
                                <span>${score}</span>
                            </div>
                        </td>
                        <td>${App.badge(d.duty_status)}</td>
                        ${canEdit ? `<td class="actions-cell">
                            <button class="btn btn-sm btn-outline" onclick="Drivers.openEdit('${d.id}')">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="Drivers.remove('${d.id}')">Delete</button>
                        </td>` : ''}
                    </tr>`;
                }).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('drivers-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },

    openCreate() {
        App.openModal('Add Driver', Drivers.formHtml(), async () => {
            const data = Drivers.getFormData();
            await API.post('/drivers', data);
            App.closeModal();
            App.toast('Driver created successfully', 'success');
            await Drivers.loadTable();
        });
    },

    async openEdit(id) {
        const d = await API.get(`/drivers/${id}`);
        App.openModal('Edit Driver', Drivers.formHtml(d), async () => {
            const data = Drivers.getFormData();
            await API.put(`/drivers/${id}`, data);
            App.closeModal();
            App.toast('Driver updated', 'success');
            await Drivers.loadTable();
        });
    },

    async remove(id) {
        if (!confirm('Delete this driver?')) return;
        await API.delete(`/drivers/${id}`);
        App.toast('Driver deleted', 'success');
        await Drivers.loadTable();
    },

    formHtml(d = {}) {
        const score = d.safety_score != null ? d.safety_score : 100;
        return `
            <div class="form-group"><label>Full Name</label><input type="text" id="f-fullname" value="${d.full_name || ''}" placeholder="e.g. Rajesh Kumar"></div>
            <div class="form-group"><label>Employee ID</label><input type="text" id="f-empid" value="${d.employee_id || ''}" placeholder="e.g. EMP-001"></div>
            <div class="grid-2">
                <div class="form-group"><label>License Number</label><input type="text" id="f-license" value="${d.license_number || ''}" placeholder="e.g. DL-1234567890"></div>
                <div class="form-group"><label>License Expiry</label><input type="date" id="f-expiry" value="${d.license_expiry || ''}"></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Phone</label><input type="text" id="f-phone" value="${d.phone || ''}" placeholder="+91 98765 43210"></div>
                <div class="form-group"><label>Duty Status</label><select id="f-duty">
                    <option value="available" ${d.duty_status==='available'?'selected':''}>Available</option>
                    <option value="on_duty" ${d.duty_status==='on_duty'?'selected':''}>On Duty</option>
                    <option value="off_duty" ${d.duty_status==='off_duty'?'selected':''}>Off Duty</option>
                    <option value="suspended" ${d.duty_status==='suspended'?'selected':''}>Suspended</option>
                </select></div>
            </div>
            <div class="form-group">
                <label>Safety Score: <strong id="f-score-display">${score}</strong></label>
                <input type="range" id="f-score" min="0" max="100" value="${score}" oninput="document.getElementById('f-score-display').textContent = this.value">
            </div>`;
    },

    getFormData() {
        return {
            name: document.getElementById('f-fullname').value,
            full_name: document.getElementById('f-fullname').value,
            employee_id: document.getElementById('f-empid').value,
            license_number: document.getElementById('f-license').value,
            license_expiry: document.getElementById('f-expiry').value || null,
            phone: document.getElementById('f-phone').value,
            duty_status: document.getElementById('f-duty').value,
            safety_score: parseInt(document.getElementById('f-score').value) || 0,
        };
    },
};
