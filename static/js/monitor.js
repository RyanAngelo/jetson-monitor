// Chart configuration
const maxDataPoints = 60;
let updateIntervalMs = 5000;
let metricsChart, networkChart;
let intervalId;

// Chart data configuration
const metricsChartData = {
    labels: [],
    datasets: [{
        label: 'CPU Usage',
        data: [],
        borderColor: '#00bcd4',
        backgroundColor: 'rgba(0, 188, 212, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'Memory Usage',
        data: [],
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'Memory Pressure',
        data: [],
        borderColor: '#FF5722',
        backgroundColor: 'rgba(255, 87, 34, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'Swap Usage',
        data: [],
        borderColor: '#9C27B0',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'Disk Usage',
        data: [],
        borderColor: '#FFC107',
        backgroundColor: 'rgba(255, 193, 7, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'GPU Usage',
        data: [],
        borderColor: '#F44336',
        backgroundColor: 'rgba(244, 67, 54, 0.1)',
        tension: 0.1,
        fill: true
    }]
};

const networkChartData = {
    labels: [],
    datasets: [{
        label: 'Network Sent (KB/s)',
        data: [],
        borderColor: '#9C27B0',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        tension: 0.1,
        fill: true
    }, {
        label: 'Network Received (KB/s)',
        data: [],
        borderColor: '#FF9800',
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        tension: 0.1,
        fill: true
    }]
};

// Chart configuration
const metricsChartConfig = {
    type: 'line',
    options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
            padding: {
                left: 10,
                right: 10
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#b3b3b3'
                }
            },
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#b3b3b3',
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 6
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: '#b3b3b3',
                    boxWidth: 12,
                    padding: 10
                }
            }
        }
    }
};

const networkChartConfig = {
    type: 'line',
    options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
            padding: {
                left: 10,
                right: 10
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#b3b3b3',
                    callback: function(value) {
                        if (value >= 1024) {
                            return (value / 1024).toFixed(1) + ' MB/s';
                        } else {
                            return value.toFixed(0) + ' KB/s';
                        }
                    }
                }
            },
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#b3b3b3',
                    maxRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 6
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: '#b3b3b3',
                    boxWidth: 12,
                    padding: 10
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const value = context.raw;
                        if (value >= 1024) {
                            return context.dataset.label.replace('(KB/s)', '(MB/s)') + ': ' + (value / 1024).toFixed(2) + ' MB/s';
                        } else {
                            return context.dataset.label + ': ' + value.toFixed(1) + ' KB/s';
                        }
                    }
                }
            }
        }
    }
};

// Initialize charts
function initCharts() {
    const metricsCtx = document.getElementById('metricsChart').getContext('2d');
    metricsChart = new Chart(metricsCtx, {
        ...metricsChartConfig,
        data: metricsChartData
    });

    const networkCtx = document.getElementById('networkChart').getContext('2d');
    networkChart = new Chart(networkCtx, {
        ...networkChartConfig,
        data: networkChartData
    });

    // Force chart resize
    setTimeout(() => {
        metricsChart.resize();
        networkChart.resize();
    }, 100);
}

// Update metrics display
function updateMetricsDisplay(data) {
    // Update basic metrics
    document.getElementById('cpuValue').textContent = `${data.cpu_percent.toFixed(1)}%`;
    document.getElementById('memoryValue').textContent = `${data.memory_percent.toFixed(1)}%`;
    document.getElementById('diskValue').textContent = `${data.disk_percent.toFixed(1)}%`;
    
    // Update GPU metrics
    const gpuMetrics = data.gpu_metrics;
    if (gpuMetrics && !gpuMetrics.error) {
        document.getElementById('gpuValue').textContent = `${gpuMetrics.gpu_utilization.toFixed(1)}%`;
        document.getElementById('gpuTempValue').textContent = `${gpuMetrics.gpu_temperature?.toFixed(1) || 0}°C`;
        document.getElementById('cpuTempValue').textContent = `${gpuMetrics.cpu_temperature?.toFixed(1) || 0}°C`;
        document.getElementById('powerValue').textContent = `${gpuMetrics.total_power?.toFixed(0) || 0}mW`;
        document.getElementById('gpuPowerValue').textContent = `${gpuMetrics.gpu_power?.toFixed(0) || 0}mW`;
    }
    
    // Update memory pressure metrics
    const memoryPressure = data.memory_pressure;
    updateMemoryPressureDisplay(memoryPressure);
    
    // Update thermal status
    updateThermalStatusDisplay(data.thermal_status);
    
    // Update network metrics
    document.getElementById('networkSentValue').textContent = data.network.sent_speed_human;
    document.getElementById('networkRecvValue').textContent = data.network.recv_speed_human;
    
    // Update timestamp
    document.getElementById('timestamp').textContent = `Last updated: ${data.timestamp}`;
    
    // Update uptime
    document.getElementById('uptimeValue').textContent = data.uptime;
}

// Update memory pressure display
function updateMemoryPressureDisplay(memoryPressure) {
    const pressureValue = memoryPressure.memory_pressure;
    const pressureElement = document.getElementById('memoryPressureValue');
    const swapElement = document.getElementById('swapValue');
    
    // Update memory pressure
    pressureElement.textContent = `${pressureValue.toFixed(1)}`;
    pressureElement.className = 'metric-value';
    updatePressureClass(pressureElement, pressureValue);
    
    // Update swap usage
    const swapPercent = memoryPressure.swap.percent;
    swapElement.textContent = `${swapPercent.toFixed(1)}%`;
    swapElement.className = 'metric-value';
    updatePressureClass(swapElement, swapPercent);
    
    document.getElementById('swapDetails').textContent = 
        `${memoryPressure.swap.used.toFixed(0)} MB / ${memoryPressure.swap.total.toFixed(0)} MB`;
}

// Update thermal status display
function updateThermalStatusDisplay(thermalStatus) {
    const thermalStatusElement = document.getElementById('thermalStatusValue');
    const thermalDetailsElement = document.getElementById('thermalDetails');
    
    thermalStatusElement.textContent = thermalStatus.status;
    thermalStatusElement.className = 'metric-value';
    
    // Set the appropriate class based on status
    if (thermalStatus.status === 'Normal') {
        thermalStatusElement.classList.add('thermal-normal');
    } else if (thermalStatus.status === 'Throttled') {
        thermalStatusElement.classList.add('thermal-throttled');
    } else if (thermalStatus.status === 'Unknown') {
        thermalStatusElement.classList.add('thermal-unknown');
    } else {
        thermalStatusElement.classList.add('thermal-error');
    }
    
    // Update details
    let details = [];
    if (thermalStatus.cpu_throttled) details.push('CPU Throttled');
    if (thermalStatus.gpu_throttled) details.push('GPU Throttled');
    thermalDetailsElement.textContent = details.length > 0 ? details.join(', ') : 'All Normal';
}

// Update pressure class based on value
function updatePressureClass(element, value) {
    if (value <= 30) {
        element.classList.add('pressure-low');
    } else if (value <= 70) {
        element.classList.add('pressure-moderate');
    } else {
        element.classList.add('pressure-high');
    }
}

// Update charts
function updateCharts(data) {
    const timestamp = new Date().toLocaleTimeString();
    
    // Update metrics chart
    if (metricsChartData.labels.length >= maxDataPoints) {
        metricsChartData.labels.shift();
        metricsChartData.datasets.forEach(dataset => dataset.data.shift());
    }
    
    metricsChartData.labels.push(timestamp);
    metricsChartData.datasets[0].data.push(data.cpu_percent);
    metricsChartData.datasets[1].data.push(data.memory_percent);
    metricsChartData.datasets[2].data.push(data.memory_pressure.memory_pressure);
    metricsChartData.datasets[3].data.push(data.memory_pressure.swap.percent);
    metricsChartData.datasets[4].data.push(data.disk_percent);
    metricsChartData.datasets[5].data.push(data.gpu_metrics?.gpu_utilization || 0);
    metricsChart.update('none');
    
    // Update network chart
    if (networkChartData.labels.length >= maxDataPoints) {
        networkChartData.labels.shift();
        networkChartData.datasets.forEach(dataset => dataset.data.shift());
    }
    
    networkChartData.labels.push(timestamp);
    networkChartData.datasets[0].data.push(data.network.sent_speed / 1024);
    networkChartData.datasets[1].data.push(data.network.recv_speed / 1024);
    networkChart.update('none');
}

// Fetch and update metrics
function updateMetrics() {
    fetch('/metrics')
        .then(response => response.json())
        .then(data => {
            updateMetricsDisplay(data);
            updateCharts(data);
        })
        .catch(error => console.error('Error fetching metrics:', error));
}

// Update interval handler
function updateInterval() {
    const newInterval = document.getElementById('updateInterval').value;
    updateIntervalMs = newInterval * 1000;
    clearInterval(intervalId);
    intervalId = setInterval(updateMetrics, updateIntervalMs);
}

// Initialize the monitoring
function init() {
    initCharts();
    intervalId = setInterval(updateMetrics, updateIntervalMs);
    updateMetrics(); // Initial update
}

// Start monitoring when the page loads
document.addEventListener('DOMContentLoaded', init); 