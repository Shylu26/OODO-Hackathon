const Dashboard = {
    async render() {
        const content = document.getElementById('main-content');
        content.innerHTML = '<div class="spinner-container"><div class="spinner"></div></div>';
        try {
            const [kpis, recentTrips, chartData] = await Promise.all([
                API.get('/dashboard/kpis'),
                API.get('/dashboard/recent-trips'),
                API.get('/dashboard/chart-data'),
            ]);
            content.innerHTML = `
                <div class="kpi-grid">
                    ${Dashboard.kpiCard('🚛', 'Fleet Utilization', kpis.fleet_utilization + '%', 'blue', 'Active vehicles on trips')}
                    ${Dashboard.kpiCard('⛽', 'Fuel Efficiency', kpis.avg_fuel_efficiency + ' km/L', 'green', 'Average across fleet')}
                    ${Dashboard.kpiCard('💰', 'Operational Cost', '₹' + Dashboard.formatNum(kpis.operational_cost), 'amber', 'Fuel + Maintenance')}
                    ${Dashboard.kpiCard('📊', 'Total Revenue', '₹' + Dashboard.formatNum(kpis.total_revenue), 'violet', 'From completed trips')}
                </div>

                <!-- Charts + Tables two-column layout -->
                <div class="dashboard-split mt-4">
                    <!-- LEFT: Charts Panel -->
                    <div class="dashboard-charts-panel">
                        <div class="card chart-card">
                            <h3 class="card-title">📈 Monthly Fuel Costs</h3>
                            <div class="chart-container" id="chart-fuel-monthly"></div>
                        </div>
                        <div class="card chart-card">
                            <h3 class="card-title">🍩 Expense Breakdown</h3>
                            <div class="chart-container chart-donut-wrap" id="chart-expense-donut"></div>
                        </div>
                        <div class="card chart-card">
                            <h3 class="card-title">💹 Revenue vs Cost</h3>
                            <div class="chart-container" id="chart-revenue-cost"></div>
                        </div>
                        <div class="card chart-card">
                            <h3 class="card-title">🚦 Trip Status</h3>
                            <div class="chart-container" id="chart-trip-states"></div>
                        </div>
                    </div>

                    <!-- RIGHT: Tables Panel -->
                    <div class="dashboard-tables-panel">
                        <div class="card">
                            <h3 class="card-title">Fleet Status</h3>
                            <div class="fleet-status-bars">
                                ${Dashboard.statusBar('Available', kpis.available_vehicles, kpis.total_vehicles, 'var(--clr-success, var(--success))')}
                                ${Dashboard.statusBar('On Trip', kpis.on_trip_vehicles, kpis.total_vehicles, 'var(--clr-info, var(--info))')}
                                ${Dashboard.statusBar('In Shop', kpis.in_shop_vehicles, kpis.total_vehicles, 'var(--clr-warning, var(--warning))')}
                            </div>
                            <div class="fleet-summary mt-2">
                                <span class="text-muted">${kpis.total_vehicles} total vehicles · ${kpis.total_drivers} drivers (${kpis.available_drivers} available)</span>
                            </div>
                        </div>
                        <div class="card">
                            <h3 class="card-title">Top ROI Vehicles</h3>
                            ${kpis.top_roi_vehicles && kpis.top_roi_vehicles.length > 0 ? `
                            <table class="data-table">
                                <thead><tr><th>Vehicle</th><th>Reg #</th><th>ROI</th></tr></thead>
                                <tbody>
                                    ${kpis.top_roi_vehicles.map(v => `
                                        <tr>
                                            <td>${v.name}</td>
                                            <td><code>${v.registration}</code></td>
                                            <td><span class="${v.roi >= 0 ? 'text-success' : 'text-danger'}">${v.roi.toFixed(1)}%</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>` : '<p class="text-muted mt-2">No ROI data available yet.</p>'}
                        </div>
                        <div class="card">
                            <h3 class="card-title">Recent Trips</h3>
                            ${recentTrips && recentTrips.length > 0 ? `
                            <table class="data-table">
                                <thead><tr><th>Trip #</th><th>Vehicle</th><th>Driver</th><th>Route</th><th>Status</th></tr></thead>
                                <tbody>
                                    ${recentTrips.map(t => `
                                        <tr>
                                            <td><strong>${t.trip_number}</strong></td>
                                            <td>${t.vehicle_name || '-'}</td>
                                            <td>${t.driver_name || '-'}</td>
                                            <td>${t.origin} → ${t.destination}</td>
                                            <td>${App.badge(t.state)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>` : '<p class="text-muted mt-2">No trips yet.</p>'}
                        </div>
                    </div>
                </div>
            `;

            // Render charts after DOM is ready
            Dashboard.renderFuelChart(chartData.fuel_by_month);
            Dashboard.renderExpenseDonut(chartData.expense_breakdown);
            Dashboard.renderRevenueVsCost(chartData.revenue_vs_cost);
            Dashboard.renderTripStates(chartData.trips_by_state);
        } catch (err) {
            content.innerHTML = `<div class="error-state">Failed to load dashboard: ${err.message}</div>`;
        }
    },

    // ── KPI Card ─────────────────────────────────────────────────────
    kpiCard(icon, label, value, color, subtitle) {
        return `
            <div class="kpi-card accent-${color}">
                <div class="kpi-icon bg-${color}">${icon}</div>
                <div class="kpi-info">
                    <div class="kpi-value">${value}</div>
                    <div class="kpi-label">${label}</div>
                    <div class="kpi-subtitle">${subtitle}</div>
                </div>
            </div>`;
    },

    // ── Status Bar ───────────────────────────────────────────────────
    statusBar(label, count, total, color) {
        const pct = total > 0 ? (count / total * 100) : 0;
        return `
            <div class="status-bar-row">
                <span class="status-bar-label">${label}</span>
                <div class="status-bar-track">
                    <div class="status-bar-fill" style="width:${pct}%;background:${color}"></div>
                </div>
                <span class="status-bar-value">${count}</span>
            </div>`;
    },

    formatNum(n) {
        if (n == null) return '0';
        return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });
    },

    formatShort(n) {
        if (n >= 100000) return '₹' + (n / 100000).toFixed(1) + 'L';
        if (n >= 1000) return '₹' + (n / 1000).toFixed(1) + 'K';
        return '₹' + n;
    },

    // ── Bar Chart: Monthly Fuel Costs ────────────────────────────────
    renderFuelChart(data) {
        const container = document.getElementById('chart-fuel-monthly');
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<p class="text-muted chart-empty">No fuel data available</p>';
            return;
        }
        const maxVal = Math.max(...data.map(d => d.cost), 1);
        const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

        container.innerHTML = `
            <div class="bar-chart">
                <div class="bar-chart-y-axis">
                    <span>${Dashboard.formatShort(maxVal)}</span>
                    <span>${Dashboard.formatShort(maxVal * 0.5)}</span>
                    <span>₹0</span>
                </div>
                <div class="bar-chart-bars">
                    ${data.map(d => {
                        const pct = (d.cost / maxVal) * 100;
                        const monthIdx = parseInt(d.month.split('-')[1]) - 1;
                        const label = monthNames[monthIdx] || d.month;
                        return `
                            <div class="bar-col">
                                <div class="bar-tooltip">₹${Number(d.cost).toLocaleString('en-IN')}</div>
                                <div class="bar" style="height:${pct}%"></div>
                                <span class="bar-label">${label}</span>
                            </div>`;
                    }).join('')}
                </div>
            </div>`;
    },

    // ── Donut Chart: Expense Breakdown ───────────────────────────────
    renderExpenseDonut(data) {
        const container = document.getElementById('chart-expense-donut');
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<p class="text-muted chart-empty">No expense data available</p>';
            return;
        }
        const total = data.reduce((s, d) => s + d.amount, 0);
        const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6'];

        // Build conic-gradient segments
        let gradientParts = [];
        let cumPercent = 0;
        data.forEach((d, i) => {
            const pct = (d.amount / total) * 100;
            const color = colors[i % colors.length];
            gradientParts.push(`${color} ${cumPercent}% ${cumPercent + pct}%`);
            cumPercent += pct;
        });

        const legendItems = data.map((d, i) => {
            const pct = ((d.amount / total) * 100).toFixed(1);
            const color = colors[i % colors.length];
            const label = d.category.charAt(0).toUpperCase() + d.category.slice(1);
            return `<div class="donut-legend-item">
                <span class="donut-legend-dot" style="background:${color}"></span>
                <span class="donut-legend-label">${label}</span>
                <span class="donut-legend-val">₹${Number(d.amount).toLocaleString('en-IN')} (${pct}%)</span>
            </div>`;
        }).join('');

        container.innerHTML = `
            <div class="donut-chart-layout">
                <div class="donut-ring" style="background: conic-gradient(${gradientParts.join(', ')})">
                    <div class="donut-hole">
                        <span class="donut-total-label">Total</span>
                        <span class="donut-total-value">₹${Number(total).toLocaleString('en-IN')}</span>
                    </div>
                </div>
                <div class="donut-legend">${legendItems}</div>
            </div>`;
    },

    // ── Grouped Bar Chart: Revenue vs Cost ──────────────────────────
    renderRevenueVsCost(data) {
        const container = document.getElementById('chart-revenue-cost');
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<p class="text-muted chart-empty">No revenue/cost data available</p>';
            return;
        }
        const maxVal = Math.max(...data.map(d => Math.max(d.revenue, d.cost)), 1);
        const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

        container.innerHTML = `
            <div class="bar-chart grouped-bar-chart">
                <div class="bar-chart-y-axis">
                    <span>${Dashboard.formatShort(maxVal)}</span>
                    <span>${Dashboard.formatShort(maxVal * 0.5)}</span>
                    <span>₹0</span>
                </div>
                <div class="bar-chart-bars">
                    ${data.map(d => {
                        const revPct = (d.revenue / maxVal) * 100;
                        const costPct = (d.cost / maxVal) * 100;
                        const monthIdx = parseInt(d.month.split('-')[1]) - 1;
                        const label = monthNames[monthIdx] || d.month;
                        return `
                            <div class="bar-col grouped">
                                <div class="bar-group">
                                    <div class="bar-wrapper">
                                        <div class="bar-tooltip">₹${Number(d.revenue).toLocaleString('en-IN')}</div>
                                        <div class="bar bar-revenue" style="height:${revPct}%"></div>
                                    </div>
                                    <div class="bar-wrapper">
                                        <div class="bar-tooltip">₹${Number(d.cost).toLocaleString('en-IN')}</div>
                                        <div class="bar bar-cost" style="height:${costPct}%"></div>
                                    </div>
                                </div>
                                <span class="bar-label">${label}</span>
                            </div>`;
                    }).join('')}
                </div>
            </div>
            <div class="chart-legend-inline">
                <span class="legend-dot" style="background:var(--success)"></span> Revenue
                <span class="legend-dot" style="background:var(--danger);margin-left:12px"></span> Cost
            </div>`;
    },

    // ── Horizontal Bar Chart: Trip States ────────────────────────────
    renderTripStates(data) {
        const container = document.getElementById('chart-trip-states');
        if (!container || !data || data.length === 0) {
            if (container) container.innerHTML = '<p class="text-muted chart-empty">No trip data available</p>';
            return;
        }
        const maxVal = Math.max(...data.map(d => d.count), 1);
        const stateColors = {
            'draft': '#94a3b8',
            'dispatched': '#3b82f6',
            'completed': '#10b981',
            'cancelled': '#ef4444',
            'unknown': '#64748b',
        };

        container.innerHTML = `
            <div class="hbar-chart">
                ${data.map(d => {
                    const pct = (d.count / maxVal) * 100;
                    const color = stateColors[d.state] || '#6366f1';
                    const label = d.state.charAt(0).toUpperCase() + d.state.slice(1);
                    return `
                        <div class="hbar-row">
                            <span class="hbar-label">${label}</span>
                            <div class="hbar-track">
                                <div class="hbar-fill" style="width:${pct}%;background:${color}"></div>
                            </div>
                            <span class="hbar-value">${d.count}</span>
                        </div>`;
                }).join('')}
            </div>`;
    },
};
