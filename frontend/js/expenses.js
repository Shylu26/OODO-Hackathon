const Expenses = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager', 'financial_analyst');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Expenses</h2>
                    <p class="text-muted">Track and manage operational expenses</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Expenses.openCreate()">+ Add Expense</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="expenses-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Expenses.loadTable();
    },

    async loadTable() {
        try {
            const expenses = await API.get('/expenses');
            const area = document.getElementById('expenses-table-area');
            if (!expenses || expenses.length === 0) { area.innerHTML = '<p class="empty-state">No expenses found.</p>'; return; }
            const canEdit = Auth.hasRole('fleet_manager', 'financial_analyst');
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Description</th><th>Category</th><th>Amount (₹)</th><th>Date</th><th>Vehicle</th><th>Driver</th>${canEdit ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${expenses.map(e => `<tr>
                    <td><strong>${e.name || e.description || '-'}</strong></td>
                    <td>${App.badge(e.category)}</td>
                    <td>${e.amount != null ? '₹' + Number(e.amount).toLocaleString('en-IN') : '-'}</td>
                    <td>${e.date || '-'}</td>
                    <td>${e.vehicle_name || '-'}</td>
                    <td>${e.driver_name || '-'}</td>
                    ${canEdit ? `<td class="actions-cell">
                        <button class="btn btn-sm btn-outline" onclick="Expenses.openEdit('${e.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="Expenses.remove('${e.id}')">Delete</button>
                    </td>` : ''}
                </tr>`).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('expenses-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },

    async openCreate() {
        try {
            const [vehicles, drivers] = await Promise.all([
                API.get('/vehicles'),
                API.get('/drivers'),
            ]);
            App.openModal('Add Expense', Expenses.formHtml({}, vehicles || [], drivers || []), async () => {
                const data = Expenses.getFormData();
                await API.post('/expenses', data);
                App.closeModal();
                App.toast('Expense created', 'success');
                await Expenses.loadTable();
            });
        } catch (err) { App.toast('Failed to load form data: ' + err.message, 'error'); }
    },

    async openEdit(id) {
        try {
            const [expense, vehicles, drivers] = await Promise.all([
                API.get(`/expenses/${id}`),
                API.get('/vehicles'),
                API.get('/drivers'),
            ]);
            App.openModal('Edit Expense', Expenses.formHtml(expense, vehicles || [], drivers || []), async () => {
                const data = Expenses.getFormData();
                await API.put(`/expenses/${id}`, data);
                App.closeModal();
                App.toast('Expense updated', 'success');
                await Expenses.loadTable();
            });
        } catch (err) { App.toast('Failed to load expense: ' + err.message, 'error'); }
    },

    async remove(id) {
        if (!confirm('Delete this expense?')) return;
        await API.delete(`/expenses/${id}`);
        App.toast('Expense deleted', 'success');
        await Expenses.loadTable();
    },

    formHtml(e = {}, vehicles = [], drivers = []) {
        return `
            <div class="form-group"><label>Description</label><input type="text" id="f-description" value="${e.name || e.description || ''}" placeholder="e.g. Quarterly insurance premium"></div>
            <div class="grid-2">
                <div class="form-group"><label>Category</label><select id="f-category">
                    <option value="fuel" ${e.category==='fuel'?'selected':''}>Fuel</option>
                    <option value="maintenance" ${e.category==='maintenance'?'selected':''}>Maintenance</option>
                    <option value="salary" ${e.category==='salary'?'selected':''}>Salary</option>
                    <option value="insurance" ${e.category==='insurance'?'selected':''}>Insurance</option>
                    <option value="toll" ${e.category==='toll'?'selected':''}>Toll</option>
                    <option value="other" ${e.category==='other'?'selected':''}>Other</option>
                </select></div>
                <div class="form-group"><label>Amount (₹)</label><input type="number" id="f-amount" value="${e.amount || ''}" step="0.01" placeholder="0"></div>
            </div>
            <div class="form-group"><label>Date</label><input type="date" id="f-date" value="${e.date || ''}"></div>
            <div class="grid-2">
                <div class="form-group"><label>Vehicle (optional)</label><select id="f-vehicle">
                    <option value="">-- None --</option>
                    ${vehicles.map(v => `<option value="${v.id}" ${e.vehicle_id === v.id ? 'selected' : ''}>${v.name} (${v.registration_number})</option>`).join('')}
                </select></div>
                <div class="form-group"><label>Driver (optional)</label><select id="f-driver">
                    <option value="">-- None --</option>
                    ${drivers.map(d => `<option value="${d.id}" ${e.driver_id === d.id ? 'selected' : ''}>${d.full_name}</option>`).join('')}
                </select></div>
            </div>`;
    },

    getFormData() {
        return {
            name: document.getElementById('f-description').value,
            category: document.getElementById('f-category').value,
            amount: parseFloat(document.getElementById('f-amount').value) || 0,
            date: document.getElementById('f-date').value || "",
            vehicle_id: document.getElementById('f-vehicle').value || null,
            driver_id: document.getElementById('f-driver').value || null,
        };
    },
};
