document.addEventListener('DOMContentLoaded', () => {
    const loadSelect = document.getElementById('load-select');
    const generationSelect = document.getElementById('generation-select');
    const chartCanvas = document.getElementById('energy-chart');
    let chart;

    function updateChart() {
        const meterId = loadSelect.value;
        const generationIds = Array.from(generationSelect.querySelectorAll('input:checked')).map(input => input.value);

        if (!meterId) {
            if (chart) {
                chart.destroy();
            }
            return;
        }

        fetch(`/api/data?meter_id=${meterId}&generation_ids[]=${generationIds.join('&generation_ids[]=')}`)
            .then(response => response.json())
            .then(data => {
                const timestamps = Object.keys(data.load).sort();
                const loadData = timestamps.map(ts => data.load[ts]);
                const generationData = timestamps.map(ts => data.generation[ts] || 0);

                const chartData = {
                    labels: timestamps.map(ts => new Date(ts).toLocaleString()),
                    datasets: [
                        {
                            label: 'Load',
                            data: loadData,
                            borderColor: 'blue',
                            backgroundColor: 'rgba(0, 0, 255, 0.1)',
                            type: 'line',
                            yAxisID: 'y-axis-1'
                        },
                        {
                            label: 'Generation',
                            data: generationData,
                            backgroundColor: 'rgba(255, 99, 132, 0.5)',
                            type: 'bar',
                            yAxisID: 'y-axis-1'
                        }
                    ]
                };

                if (chart) {
                    chart.data = chartData;
                    chart.update();
                } else {
                    chart = new Chart(chartCanvas, {
                        type: 'bar',
                        data: chartData,
                        options: {
                            scales: {
                                'y-axis-1': {
                                    type: 'linear',
                                    position: 'left',
                                    stacked: true
                                }
                            }
                        }
                    });
                }
            });
    }

    loadSelect.addEventListener('change', updateChart);
    generationSelect.addEventListener('change', updateChart);
});