// Variables globales para almacenar los datos y gráficos
let monthlyTrendChart, sessionsByFractionChart, attendanceByFractionChart;
let dashboardData = {};

async function fetchDashboardData() {
    console.log('Fetching dashboard data...');
    try {
        const endpoints = [
            'http://localhost:8000/kpi/asistencia',
            'http://localhost:8000/kpi/asistencia-mensual',
            'http://localhost:8000/kpi/ranking?top=10&orden=desc',
            'http://localhost:8000/kpi/sesiones-por-fraccion',
            'http://localhost:8000/time/asistencia',
            'http://localhost:8000/kpi/ranking?top=10&orden=asc'
        ];

        const promises = endpoints.map(url => 
            fetch(url).then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
        );

        const [
            globalData,
            monthlyData,
            rankingData,
            sessionsData,
            attendanceData,
            worstData
        ] = await Promise.all(promises);

        console.log('Data fetched successfully:', { globalData, monthlyData, rankingData, sessionsData, attendanceData, worstData });
        return {
            globalAttendance: globalData.pct_asistencia,
            monthlyAttendance: monthlyData,
            topDeputies: rankingData,
            worstDeputies: worstData,
            sessionsByFraction: sessionsData,
            attendanceByFraction: attendanceData
        };
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showAlert('Error al cargar datos. Verifique la conexión o intente de nuevo.', 'danger');
        return null;
    }
}

// Process data for charts
function processDashboardData(rawData) {
    if (!rawData) return null;

    const topDeputy = rawData.topDeputies.length > 0 ? rawData.topDeputies[0] : {Diputado: 'N/A', pct_asistencia: 0};
    const bottomDeputy = rawData.worstDeputies.length > 0 ? rawData.worstDeputies[0] : {Diputado: 'N/A', pct_asistencia: 0};

    // Procesar datos mensuales
    const monthlyLabels = rawData.monthlyAttendance.map(item => {
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        return `${months[item.Mes - 1]} ${item.Anio}`;
    });
    const monthlyValues = rawData.monthlyAttendance.map(item => item.kpi_pct);

    // Procesar datos por fracción
    const fractionLabels = rawData.sessionsByFraction.map(item => item.Fraccion);
    const fractionValues = rawData.sessionsByFraction.map(item => item.total_sesiones);

    // Procesar datos de asistencia por fracción
    const fractions = [...new Set(rawData.attendanceByFraction.map(item => item.Fraccion))];
    const timePeriods = [...new Set(rawData.attendanceByFraction.map(item => item.periodo))].sort();

    const fractionAttendance = {};
    fractions.forEach(fraction => {
        fractionAttendance[fraction] = timePeriods.map(period => {
            const record = rawData.attendanceByFraction.find(
                item => item.Fraccion === fraction && item.periodo === period
            );
            return record ? record.pct_asistencia : 0;
        });
    });

    return {
        globalAttendance: rawData.globalAttendance,
        monthlyAttendance: monthlyValues.length > 0 ? monthlyValues[monthlyValues.length - 1] : 0,
        topDeputy: { name: topDeputy.Diputado, attendance: topDeputy.pct_asistencia, fraction: topDeputy.Fraccion },
        bottomDeputy: { name: bottomDeputy.Diputado, attendance: bottomDeputy.pct_asistencia, fraction: bottomDeputy.Fraccion },
        monthlyTrend: { labels: monthlyLabels, data: monthlyValues },
        sessionsByFraction: { labels: fractionLabels, data: fractionValues, colors: ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c', '#d35400'] },
        topDeputies: rawData.topDeputies,
        worstDeputies: rawData.worstDeputies,
        attendanceByFraction: {
            labels: timePeriods,
            datasets: Object.keys(fractionAttendance).map((fraction, index) => {
                const colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'];
                return {
                    label: fraction,
                    data: fractionAttendance[fraction],
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length] + '20',
                    tension: 0.3,
                    fill: true
                };
            })
        }
    };
}

// Show alert function
function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    
    const alertContainer = document.querySelector('.container');
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    setTimeout(() => {
        alert.classList.add('hide');
        setTimeout(() => alert.remove(), 500);
    }, 5000);
}

// Initialize charts with real data
async function initializeDashboard() {
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('dashboard-content').style.display = 'none';

    const rawData = await fetchDashboardData();
    if (!rawData) {
        document.getElementById('loading').style.display = 'none';
        return;
    }

    dashboardData = processDashboardData(rawData);
    if (!dashboardData) {
        document.getElementById('loading').style.display = 'none';
        return;
    }

    // Set KPI values
    document.getElementById('global-attendance').textContent = dashboardData.globalAttendance.toFixed(1) + '%';
    document.getElementById('monthly-attendance').textContent = dashboardData.monthlyAttendance.toFixed(1) + '%';
    document.getElementById('top-deputy-attendance').textContent = dashboardData.topDeputy.attendance.toFixed(1) + '%';
    document.getElementById('bottom-deputy-attendance').textContent = dashboardData.bottomDeputy.attendance.toFixed(1) + '%';
    document.getElementById('top-deputy-name').textContent = dashboardData.topDeputy.name;
    document.getElementById('bottom-deputy-name').textContent = dashboardData.bottomDeputy.name;

    // Destroy existing charts to avoid memory leaks
    if (monthlyTrendChart) monthlyTrendChart.destroy();
    if (sessionsByFractionChart) sessionsByFractionChart.destroy();
    if (attendanceByFractionChart) attendanceByFractionChart.destroy();

    // Initialize monthly trend chart
    const monthlyTrendCtx = document.getElementById('monthly-trend-chart').getContext('2d');
    monthlyTrendChart = new Chart(monthlyTrendCtx, {
        type: 'line',
        data: {
            labels: dashboardData.monthlyTrend.labels,
            datasets: [{
                label: 'Asistencia Mensual (%)',
                data: dashboardData.monthlyTrend.data,
                borderColor: '#3498db',
                backgroundColor: '#3498db20',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { 
                    beginAtZero: false, 
                    min: 70, 
                    max: 100, 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }, 
                    ticks: { callback: value => value + '%' } 
                },
                x: { 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' } 
                }
            },
            plugins: { 
                legend: { position: 'top' }, 
                tooltip: { 
                    callbacks: { 
                        label: context => context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%' 
                    } 
                } 
            }
        }
    });

    // Initialize sessions by fraction chart
    const sessionsCtx = document.getElementById('sessions-by-fraction-chart').getContext('2d');
    sessionsByFractionChart = new Chart(sessionsCtx, {
        type: 'bar',
        data: {
            labels: dashboardData.sessionsByFraction.labels,
            datasets: [{
                label: 'Sesiones',
                data: dashboardData.sessionsByFraction.data,
                backgroundColor: dashboardData.sessionsByFraction.colors
            }]
        },
        options: {
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true, 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' } 
                }, 
                x: { 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' } 
                } 
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });

    // Initialize attendance by fraction chart
    const attendanceCtx = document.getElementById('attendance-by-fraction-chart').getContext('2d');
    attendanceByFractionChart = new Chart(attendanceCtx, {
        type: 'line',
        data: { 
            labels: dashboardData.attendanceByFraction.labels, 
            datasets: dashboardData.attendanceByFraction.datasets 
        },
        options: {
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: false, 
                    min: 70, 
                    max: 100, 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }, 
                    ticks: { callback: value => value + '%' } 
                }, 
                x: { 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' } 
                } 
            },
            plugins: { 
                legend: { position: 'top' }, 
                tooltip: { 
                    callbacks: { 
                        label: context => context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%' 
                    } 
                } 
            }
        }
    });

    // Populate top deputies list
    const topList = document.getElementById('top-deputies-list');
    topList.innerHTML = '';
    dashboardData.topDeputies.forEach((deputy, index) => {
        const attendance = deputy.pct_asistencia;
        const badgeClass = attendance > 95 ? 'excellent' : attendance > 90 ? 'good' : attendance > 85 ? 'warning' : 'critical';
        const progressClass = attendance > 95 ? 'bg-success' : attendance > 90 ? 'bg-primary' : attendance > 85 ? 'bg-warning' : 'bg-danger';
        const progressWidth = attendance;
        
        topList.innerHTML += `
            <div class="ranking-row">
                <div class="ranking-position">${index + 1}</div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${deputy.Diputado}</strong>
                            <small class="text-muted d-block">${deputy.Fraccion}</small>
                        </div>
                        <span class="kpi-badge ${badgeClass}">${attendance.toFixed(1)}%</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar ${progressClass}" style="width: ${progressWidth}%" aria-valuenow="${attendance}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
        `;
    });

    // Populate bottom deputies list
    const bottomList = document.getElementById('bottom-deputies-list');
    bottomList.innerHTML = '';
    dashboardData.worstDeputies.forEach((deputy, index) => {
        const attendance = deputy.pct_asistencia;
        const badgeClass = attendance > 85 ? 'excellent' : attendance > 80 ? 'good' : attendance > 75 ? 'warning' : 'critical';
        const progressClass = attendance > 85 ? 'bg-success' : attendance > 80 ? 'bg-primary' : attendance > 75 ? 'bg-warning' : 'bg-danger';
        const progressWidth = attendance;
        
        bottomList.innerHTML += `
            <div class="ranking-row">
                <div class="ranking-position">${index + 1}</div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${deputy.Diputado}</strong>
                            <small class="text-muted d-block">${deputy.Fraccion}</small>
                        </div>
                        <span class="kpi-badge ${badgeClass}">${attendance.toFixed(1)}%</span>
                    </div>
                    <div class="progress mt-2">
                        <div class="progress-bar ${progressClass}" style="width: ${progressWidth}%" aria-valuenow="${attendance}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
        `;
    });

    // Update last updated time
    const now = new Date();
    const timeString = now.toLocaleTimeString('es-ES');
    document.getElementById('last-updated').textContent = `Última actualización: ${timeString}`;

    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboard-content').style.display = 'block';
}

// Initialize the dashboard when page loads
document.addEventListener('DOMContentLoaded', async function() {
    await initializeDashboard();

    document.querySelectorAll('.time-filter-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.time-filter-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            showAlert('Filtro de tiempo actualizado', 'info');
        });
    });

    document.getElementById('refresh-btn').addEventListener('click', async function() {
        const btn = this;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Actualizando...';
        btn.disabled = true;

        await initializeDashboard();

        btn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar Datos';
        btn.disabled = false;
        showAlert('Datos actualizados correctamente', 'success');
    });
});