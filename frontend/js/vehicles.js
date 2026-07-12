const Vehicles = {
    async render() {
        const content = document.getElementById('main-content');
        const canCreate = Auth.hasRole('fleet_manager');
        content.innerHTML = `
            <div class="page-header">
                <div>
                    <h2>Vehicles</h2>
                    <p class="text-muted">Manage your fleet inventory</p>
                </div>
                ${canCreate ? '<button class="btn btn-primary" onclick="Vehicles.openCreate()">+ Add Vehicle</button>' : ''}
            </div>
            <div class="card"><div class="table-wrapper" id="vehicles-table-area"><div class="spinner-container"><div class="spinner"></div></div></div></div>`;
        await Vehicles.loadTable();
    },
    async loadTable() {
        try {
            const vehicles = await API.get('/vehicles');
            const area = document.getElementById('vehicles-table-area');
            if (!vehicles || vehicles.length === 0) { area.innerHTML = '<p class="empty-state">No vehicles found.</p>'; return; }
            const canEdit = Auth.hasRole('fleet_manager');
            area.innerHTML = `<table class="data-table"><thead><tr>
                <th>Name</th><th>Registration</th><th>Type</th><th>Seats</th><th>Max Load</th><th>Status</th>${canEdit ? '<th>Actions</th>' : ''}
            </tr></thead><tbody>
                ${vehicles.map(v => `<tr>
                    <td><strong>${v.name}</strong></td>
                    <td><code>${v.registration_number}</code></td>
                    <td>${v.vehicle_type}</td>
                    <td>${v.capacity_seats}</td>
                    <td>${v.max_load_kg} kg</td>
                    <td>${App.badge(v.status)}</td>
                    ${canEdit ? `<td class="actions-cell">
                        <button class="btn btn-sm btn-outline" onclick="Vehicles.openEdit('${v.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="Vehicles.remove('${v.id}')">Delete</button>
                    </td>` : ''}
                </tr>`).join('')}
            </tbody></table>`;
        } catch (err) { document.getElementById('vehicles-table-area').innerHTML = `<p class="error-state">${err.message}</p>`; }
    },
    openCreate() {
        App.openModal('Add Vehicle', Vehicles.formHtml(), async () => {
            const data = Vehicles.getFormData();
            await API.post('/vehicles', data);
            App.closeModal();
            App.toast('Vehicle created successfully', 'success');
            await Vehicles.loadTable();
        });
    },
    async openEdit(id) {
        const v = await API.get(`/vehicles/${id}`);
        App.openModal('Edit Vehicle', Vehicles.formHtml(v), async () => {
            const data = Vehicles.getFormData();
            await API.put(`/vehicles/${id}`, data);
            App.closeModal();
            App.toast('Vehicle updated', 'success');
            await Vehicles.loadTable();
        });
    },
    async remove(id) {
        if (!confirm('Delete this vehicle?')) return;
        await API.delete(`/vehicles/${id}`);
        App.toast('Vehicle deleted', 'success');
        await Vehicles.loadTable();
    },
    formHtml(v = {}) {
        return `
            <div class="form-group"><label>Vehicle Name</label><input type="text" id="f-name" value="${v.name || ''}" placeholder="e.g. City Express 1"></div>
            <div class="form-group"><label>Registration Number</label><input type="text" id="f-reg" value="${v.registration_number || ''}" placeholder="e.g. MH-01-AB-1234"></div>
            <div class="grid-2">
                <div class="form-group"><label>Type</label><select id="f-type">
                    <option value="bus" ${v.vehicle_type==='bus'?'selected':''}>Bus</option>
                    <option value="truck" ${v.vehicle_type==='truck'?'selected':''}>Truck</option>
                    <option value="van" ${v.vehicle_type==='van'?'selected':''}>Van</option>
                    <option value="car" ${v.vehicle_type==='car'?'selected':''}>Car</option>
                </select></div>
                <div class="form-group"><label>Seats</label><input type="number" id="f-seats" value="${v.capacity_seats || 0}"></div>
            </div>
            <div class="grid-2">
                <div class="form-group"><label>Max Load (kg)</label><input type="number" id="f-load" value="${v.max_load_kg || ''}" step="0.1"></div>
                <div class="form-group"><label>Acquisition Cost (₹)</label><input type="number" id="f-cost" value="${v.acquisition_cost || 0}" step="0.01"></div>
            </div>
            <div class="form-group"><label>Status</label><select id="f-status">
                <option value="available" ${v.status==='available'?'selected':''}>Available</option>
                <option value="on_trip" ${v.status==='on_trip'?'selected':''}>On Trip</option>
                <option value="in_shop" ${v.status==='in_shop'?'selected':''}>In Shop</option>
                <option value="retired" ${v.status==='retired'?'selected':''}>Retired</option>
            </select></div>`;
    },
    getFormData() {
        return {
            name: document.getElementById('f-name').value,
            registration_number: document.getElementById('f-reg').value,
            vehicle_type: document.getElementById('f-type').value,
            capacity_seats: parseInt(document.getElementById('f-seats').value) || 0,
            max_load_kg: parseFloat(document.getElementById('f-load').value) || 0,
            acquisition_cost: parseFloat(document.getElementById('f-cost').value) || 0,
            status: document.getElementById('f-status').value,
        };
    },
};
