function createMemoryPressureChart() {
    const ctx = document.getElementById('memoryPressureChart').getContext('2d');
    memoryPressureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Pressure',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 10
                }
            },
            animation: {
                duration: 0
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: '#ffffff',
                        callback: function(value) {
                            if (value <= 30) return 'Low';
                            if (value <= 70) return 'Moderate';
                            return 'High';
                        }
                    },
                    grid: {
                        color: function(context) {
                            const value = context.tick.value;
                            if (value === 30) return 'rgba(0, 255, 0, 0.2)';
                            if (value === 70) return 'rgba(255, 0, 0, 0.2)';
                            return 'rgba(255, 255, 255, 0.1)';
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 6,
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            let status = 'Low';
                            if (value > 70) status = 'High';
                            else if (value > 30) status = 'Moderate';
                            return `Pressure: ${value.toFixed(1)}% (${status})`;
                        }
                    }
                }
            }
        }
    });
}

// Update the chart container style in the HTML
document.addEventListener('DOMContentLoaded', function() {
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
        // Set a minimum height for mobile
        const isMobile = window.innerWidth < 768;
        chartContainer.style.height = isMobile ? '300px' : '200px';
        chartContainer.style.width = '100%';
        
        // Update height on window resize
        window.addEventListener('resize', function() {
            const isMobile = window.innerWidth < 768;
            chartContainer.style.height = isMobile ? '300px' : '200px';
            chartContainer.style.width = '100%';
        });
    }
}); 