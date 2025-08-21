// Variables globales para almacenar los datos y gráficos
let monthlyTrendChart, sessionsByFractionChart, attendanceByFractionChart;
let fractionsComparisonChart, topDeputiesChart, bottomDeputiesChart;
let fractionsDistributionChart, attendanceByFractionBarChart;
let annualTrendChart, sessionTypesChart, sessionTypesBarChart;
let dashboardData = {};

// Colores predefinidos para gráficos
const CHART_COLORS = {
    primary: '#3498db',
    success: '#27ae60',
    warning: '#f39c12',
    danger: '#e74c3c',
    info: '#9b59b6',
    secondary: '#34495e',
    light: '#ecf0f1'
};

const CHART_COLOR_PALETTE = [
    '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', 
    '#1abc9c', '#d35400', '#c0392b', '#8e44ad', '#16a085'
];

async function fetchDashboardData() {
    console.log('Fetching dashboard data...');
    try {
        const endpoints = [
            'http://localhost:8000/kpi/asistencia',
            'http://localhost:8000/kpi/asistencia-mensual',
            'http://localhost:8000/kpi/ranking?top=10&orden=desc',
            'http://localhost:8000/kpi/sesiones-por-fraccion',
            'http://localhost:8000/time/asistencia',
            'http://localhost:8000/kpi/ranking?top=10&orden=asc',
            'http://localhost:8000/kpi/comparacion-fracciones',
            'http://localhost:8000/time/asistencia-anual',
            'http://localhost:8000/kpi/asistencia-por-tipo-sesion',
            'http://localhost:8000/fracciones',
            'http://localhost:8000/stats/resumen'
        ];

        const promises = endpoints.map(url => 
            fetch(url).then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
        );

        const results = await Promise.allSettled(promises);
        
        // Verificar que todas las peticiones se completaron correctamente
        const successfulResults = results.filter(result => result.status === 'fulfilled');
        if (successfulResults.length !== endpoints.length) {
            console.error('Algunas peticiones fallaron:', results.filter(r => r.status === 'rejected'));
            showAlert('Algunos datos no se pudieron cargar completamente', 'warning');
        }

        const [
            globalData,
            monthlyData,
            rankingData,
            sessionsData,
            attendanceData,
            worstData,
            fractionsComparisonData,
            annualData,
            sessionTypesData,
            fractionsData,
            statsData
        ] = successfulResults.map(result => result.value);

        console.log('Data fetched successfully');
        return {
            globalAttendance: globalData?.pct_asistencia || 0,
            monthlyAttendance: monthlyData || [],
            topDeputies: rankingData || [],
            worstDeputies: worstData || [],
            sessionsByFraction: sessionsData || [],
            attendanceByFraction: attendanceData || [],
            fractionsComparison: fractionsComparisonData || [],
            annualTrend: annualData || [],
            sessionTypes: sessionTypesData || [],
            fractions: fractionsData || [],
            stats: statsData || {}
        };
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showAlert('Error al cargar datos. Verifique que la API esté ejecutándose en localhost:8000', 'danger');
        return null;
    }
}

function processDashboardData(rawData) {
    if (!rawData) return null;

    const topDeputy = rawData.topDeputies.length > 0 ? rawData.topDeputies[0] : {Diputado: 'N/A', pct_asistencia: 0, Fraccion: 'N/A'};
    const bottomDeputy = rawData.worstDeputies.length > 0 ? rawData.worstDeputies[0] : {Diputado: 'N/A', pct_asistencia: 0, Fraccion: 'N/A'};

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

    // Procesar datos de comparación de fracciones
    const fractionsComparisonLabels = Array.isArray(rawData.fractionsComparison) ? 
        rawData.fractionsComparison.map(item => item.Fraccion) : [];
    const fractionsComparisonValues = Array.isArray(rawData.fractionsComparison) ? 
        rawData.fractionsComparison.map(item => item.pct_asistencia) : [];

    // Procesar datos anuales
    const annualLabels = rawData.annualTrend.map(item => item.Anio);
    const annualValues = rawData.annualTrend.map(item => item.pct_asistencia);

    // Procesar datos de tipos de sesión
    const sessionTypesLabels = rawData.sessionTypes.map(item => item.tipo_sesion);
    const sessionTypesValues = rawData.sessionTypes.map(item => item.promedio_asistencia);
    const sessionTypesTotal = rawData.sessionTypes.map(item => item.total_sesiones);

    return {
        globalAttendance: rawData.globalAttendance,
        monthlyAttendance: monthlyValues.length > 0 ? monthlyValues[monthlyValues.length - 1] : 0,
        topDeputy: { name: topDeputy.Diputado, attendance: topDeputy.pct_asistencia, fraction: topDeputy.Fraccion },
        bottomDeputy: { name: bottomDeputy.Diputado, attendance: bottomDeputy.pct_asistencia, fraction: bottomDeputy.Fraccion },
        monthlyTrend: { labels: monthlyLabels, data: monthlyValues },
        sessionsByFraction: { labels: fractionLabels, data: fractionValues, colors: CHART_COLOR_PALETTE },
        topDeputies: rawData.topDeputies,
        worstDeputies: rawData.worstDeputies,
        fractionsComparison: { labels: fractionsComparisonLabels, data: fractionsComparisonValues },
        annualTrend: { labels: annualLabels, data: annualValues },
        sessionTypes: { 
            labels: sessionTypesLabels, 
            data: sessionTypesValues, 
            total: sessionTypesTotal,
            details: rawData.sessionTypes 
        },
        fractions: rawData.fractions,
        stats: rawData.stats,
        attendanceByFraction: {
            labels: timePeriods,
            datasets: Object.keys(fractionAttendance).map((fraction, index) => {
                return {
                    label: fraction,
                    data: fractionAttendance[fraction],
                    borderColor: CHART_COLOR_PALETTE[index % CHART_COLOR_PALETTE.length],
                    backgroundColor: CHART_COLOR_PALETTE[index % CHART_COLOR_PALETTE.length] + '20',
                    tension: 0.3,
                    fill: true
                };
            })
        }
    };
}

function showAlert(message, type) {
    // Eliminar alertas existentes
    document.querySelectorAll('.alert').forEach(alert => alert.remove());
    
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

async function initializeDashboard() {
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('dashboard-content').style.display = 'none';

    try {
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

        // Inicializar gráficos
        initializeCharts();
        
        // Poblar listas y tablas
        populateListsAndTables();

        // Update last updated time
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES');
        document.getElementById('last-updated').textContent = `Última actualización: ${timeString}`;

    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showAlert('Error al inicializar el dashboard: ' + error.message, 'danger');
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('dashboard-content').style.display = 'block';
    }
}

function initializeCharts() {
    // Destruir gráficos existentes si existen
    const destroyChart = (chart) => {
        if (chart) {
            try {
                chart.destroy();
            } catch (e) {
                console.error('Error destroying chart:', e);
            }
        }
    };

    destroyChart(monthlyTrendChart);
    destroyChart(sessionsByFractionChart);
    destroyChart(attendanceByFractionChart);
    destroyChart(fractionsComparisonChart);
    destroyChart(topDeputiesChart);
    destroyChart(bottomDeputiesChart);
    destroyChart(fractionsDistributionChart);
    destroyChart(attendanceByFractionBarChart);
    destroyChart(annualTrendChart);
    destroyChart(sessionTypesChart);
    destroyChart(sessionTypesBarChart);

    // Inicializar gráficos solo si los elementos canvas existen
    if (document.getElementById('monthly-trend-chart')) {
        const monthlyTrendCtx = document.getElementById('monthly-trend-chart').getContext('2d');
        monthlyTrendChart = createMonthlyTrendChart(monthlyTrendCtx);
    }
    
    if (document.getElementById('sessions-by-fraction-chart')) {
        const sessionsCtx = document.getElementById('sessions-by-fraction-chart').getContext('2d');
        sessionsByFractionChart = createSessionsByFractionChart(sessionsCtx);
    }
    
    if (document.getElementById('attendance-by-fraction-chart')) {
        const attendanceCtx = document.getElementById('attendance-by-fraction-chart').getContext('2d');
        attendanceByFractionChart = createAttendanceByFractionChart(attendanceCtx);
    }
    
    if (document.getElementById('fractions-comparison-chart')) {
        const fractionsComparisonCtx = document.getElementById('fractions-comparison-chart').getContext('2d');
        fractionsComparisonChart = createFractionsComparisonChart(fractionsComparisonCtx);
    }
    
    if (document.getElementById('top-deputies-chart')) {
        const topDeputiesCtx = document.getElementById('top-deputies-chart').getContext('2d');
        topDeputiesChart = createTopDeputiesChart(topDeputiesCtx);
    }
    
    if (document.getElementById('bottom-deputies-chart')) {
        const bottomDeputiesCtx = document.getElementById('bottom-deputies-chart').getContext('2d');
        bottomDeputiesChart = createBottomDeputiesChart(bottomDeputiesCtx);
    }
    
    if (document.getElementById('fractions-distribution-chart')) {
        const fractionsDistributionCtx = document.getElementById('fractions-distribution-chart').getContext('2d');
        fractionsDistributionChart = createFractionsDistributionChart(fractionsDistributionCtx);
    }
    
    if (document.getElementById('attendance-by-fraction-bar-chart')) {
        const attendanceByFractionBarCtx = document.getElementById('attendance-by-fraction-bar-chart').getContext('2d');
        attendanceByFractionBarChart = createAttendanceByFractionBarChart(attendanceByFractionBarCtx);
    }
    
    if (document.getElementById('annual-trend-chart')) {
        const annualTrendCtx = document.getElementById('annual-trend-chart').getContext('2d');
        annualTrendChart = createAnnualTrendChart(annualTrendCtx);
    }
    
    if (document.getElementById('session-types-chart')) {
        const sessionTypesCtx = document.getElementById('session-types-chart').getContext('2d');
        sessionTypesChart = createSessionTypesChart(sessionTypesCtx);
    }
    
    if (document.getElementById('session-types-bar-chart')) {
        const sessionTypesBarCtx = document.getElementById('session-types-bar-chart').getContext('2d');
        sessionTypesBarChart = createSessionTypesBarChart(sessionTypesBarCtx);
    }
}

// Funciones para crear gráficos individuales
function createMonthlyTrendChart(ctx) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dashboardData.monthlyTrend.labels,
            datasets: [{
                label: 'Asistencia Mensual (%)',
                data: dashboardData.monthlyTrend.data,
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.primary + '20',
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
}

function createSessionsByFractionChart(ctx) {
    return new Chart(ctx, {
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
}

function createAttendanceByFractionChart(ctx) {
    return new Chart(ctx, {
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
}

function createFractionsComparisonChart(ctx) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.fractionsComparison.labels,
            datasets: [{
                label: 'Asistencia (%)',
                data: dashboardData.fractionsComparison.data,
                backgroundColor: CHART_COLOR_PALETTE
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: { 
                x: { 
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => value + '%' } 
                }, 
                y: { 
                    grid: { color: 'rgba(0, 0, 0, 0.05)' } 
                } 
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function createTopDeputiesChart(ctx) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.topDeputies.map(d => d.Diputado),
            datasets: [{
                label: 'Asistencia (%)',
                data: dashboardData.topDeputies.map(d => d.pct_asistencia),
                backgroundColor: CHART_COLORS.success
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: { 
                x: { 
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => value + '%' } 
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function createBottomDeputiesChart(ctx) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.worstDeputies.map(d => d.Diputado),
            datasets: [{
                label: 'Asistencia (%)',
                data: dashboardData.worstDeputies.map(d => d.pct_asistencia),
                backgroundColor: CHART_COLORS.danger
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: { 
                x: { 
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => value + '%' } 
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function createFractionsDistributionChart(ctx) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dashboardData.fractions.map(f => f.Fraccion),
            datasets: [{
                data: dashboardData.fractions.map(f => f.total_diputados),
                backgroundColor: CHART_COLOR_PALETTE
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function createAttendanceByFractionBarChart(ctx) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.fractionsComparison.labels,
            datasets: [{
                label: 'Asistencia (%)',
                data: dashboardData.fractionsComparison.data,
                backgroundColor: CHART_COLOR_PALETTE
            }]
        },
        options: {
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => value + '%' } 
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function createAnnualTrendChart(ctx) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dashboardData.annualTrend.labels,
            datasets: [{
                label: 'Asistencia Anual (%)',
                data: dashboardData.annualTrend.data,
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.primary + '20',
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
}

function createSessionTypesChart(ctx) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dashboardData.sessionTypes.labels,
            datasets: [{
                data: dashboardData.sessionTypes.data,
                backgroundColor: CHART_COLOR_PALETTE
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function createSessionTypesBarChart(ctx) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.sessionTypes.labels,
            datasets: [{
                label: 'Asistencia (%)',
                data: dashboardData.sessionTypes.data,
                backgroundColor: CHART_COLOR_PALETTE
            }]
        },
        options: {
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => value + '%' } 
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function populateListsAndTables() {
    // Populate top deputies list
    const topList = document.getElementById('top-deputies-list');
    if (topList) {
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
    }

    // Populate bottom deputies list
    const bottomList = document.getElementById('bottom-deputies-list');
    if (bottomList) {
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
    }

    // Populate fractions table
    const fractionsTable = document.getElementById('fractions-table');
    if (fractionsTable) {
        const tbody = fractionsTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        // Crear un mapa de asistencia por fracción para búsqueda rápida
        const attendanceMap = {};
        if (Array.isArray(dashboardData.fractionsComparison)) {
            dashboardData.fractionsComparison.forEach(item => {
                attendanceMap[item.Fraccion] = item.pct_asistencia;
            });
        }
        
        dashboardData.fractions.forEach(fraction => {
            const attendance = attendanceMap[fraction.Fraccion] || 0;
            
            tbody.innerHTML += `
                <tr>
                    <td>${fraction.Fraccion}</td>
                    <td>${fraction.total_diputados}</td>
                    <td>${fraction.total_registros}</td>
                    <td>${attendance.toFixed(1)}%</td>
                </tr>
            `;
        });
    }

    // Populate annual summary table
    const annualSummaryTable = document.getElementById('annual-summary-table');
    if (annualSummaryTable) {
        const tbody = annualSummaryTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        dashboardData.annualTrend.data.forEach((attendance, index) => {
            const year = dashboardData.annualTrend.labels[index];
            const prevYear = dashboardData.annualTrend.data[index - 1];
            let trend = 'stable';
            let trendIcon = 'fa-minus';
            
            if (prevYear) {
                if (attendance > prevYear + 2) {
                    trend = 'up';
                    trendIcon = 'fa-arrow-up';
                } else if (attendance < prevYear - 2) {
                    trend = 'down';
                    trendIcon = 'fa-arrow-down';
                }
            }
            
            tbody.innerHTML += `
                <tr>
                    <td>${year}</td>
                    <td>${attendance.toFixed(1)}%</td>
                    <td><i class="fas ${trendIcon} text-${trend}"></i></td>
                </tr>
            `;
        });
    }

    // Populate session types table
    const sessionTypesTable = document.getElementById('session-types-table');
    if (sessionTypesTable) {
        const tbody = sessionTypesTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        dashboardData.sessionTypes.details.forEach(session => {
            tbody.innerHTML += `
                <tr>
                    <td>${session.tipo_sesion}</td>
                    <td>${session.total_asistencias}</td>
                    <td>${session.total_ausencias}</td>
                    <td>${session.total_sesiones}</td>
                    <td>${session.promedio_asistencia.toFixed(1)}%</td>
                </tr>
            `;
        });
    }
}

async function searchDeputy() {
    const searchTerm = document.getElementById('deputy-search').value.trim();
    if (!searchTerm) {
        showAlert('Por favor ingrese un nombre para buscar', 'warning');
        return;
    }

    try {
        const response = await fetch(`http://localhost:8000/kpi/diputado/${encodeURIComponent(searchTerm)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const deputyData = await response.json();
        
        const container = document.getElementById('deputy-details-container');
        const content = document.getElementById('deputy-details-content');
        
        content.innerHTML = `
            <div class="deputy-header mb-4">
                <h3>${deputyData.Diputado}</h3>
                <p class="text-muted">${deputyData.Fraccion}</p>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header">Estadísticas Generales</div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-2">
                                <span>Asistencia Total:</span>
                                <strong>${deputyData.pct_asistencia_total}%</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-2">
                                <span>Total Sesiones:</span>
                                <strong>${deputyData.total_sesiones}</strong>
                            </div>
                            <div class="d-flex justify-content-between mb-2">
                                <span>Asistencias:</span>
                                <strong>${deputyData.total_asistencias}</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span>Ausencias:</span>
                                <strong>${deputyData.total_ausencias}</strong>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Desglose por Tipo de Sesión</div>
                        <div class="card-body">
                            ${Object.entries(deputyData.desglose_por_tipo || {}).map(([key, value]) => `
                                <div class="mb-2">
                                    <div class="d-flex justify-content-between">
                                        <span>${key.replace('_', ' ').toUpperCase()}:</span>
                                        <strong>${value.porcentaje}%</strong>
                                    </div>
                                    <div class="progress" style="height: 5px;">
                                        <div class="progress-bar" style="width: ${value.porcentaje}%"></div>
                                    </div>
                                    <small class="text-muted">${value.asistencias} asistencias / ${value.ausencias} ausencias</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.style.display = 'block';
    } catch (error) {
        console.error('Error searching deputy:', error);
        showAlert('Error al buscar diputado. Verifique el nombre e intente de nuevo.', 'danger');
    }
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

    const searchBtn = document.getElementById('search-deputy-btn');
    const searchInput = document.getElementById('deputy-search');
    
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', searchDeputy);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchDeputy();
            }
        });
    }
});