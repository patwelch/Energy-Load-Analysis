document.addEventListener('DOMContentLoaded', () => {
    const loadSelect = document.getElementById('load-select');
    const generationSelect = document.getElementById('generation-select');
    const selectAllLoad = document.getElementById('select-all-load');
    const selectAllGeneration = document.getElementById('select-all-generation');
    const ctx = document.getElementById('energyChart');
    let chart;

    if (!ctx) {
        console.log("Chart canvas not found on this page.");
        return;
    }

    function updateChart() {
        const meterIds = Array.from(loadSelect.querySelectorAll('input[name="load"]:checked')).map(input => input.value);
        const generationIds = Array.from(generationSelect.querySelectorAll('input[name="generation"]:checked')).map(input => input.value);

        if (meterIds.length === 0) {
            if (chart) {
                chart.destroy();
                chart = null;
            }
            return;
        }

        const params = new URLSearchParams();
        meterIds.forEach(id => params.append('meter_ids[]', id));
        generationIds.forEach(id => params.append('generation_ids[]', id));

        const apiUrl = `/api/data?${params.toString()}`;
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error("API Error:", data.error);
                    return;
                }

                const timestamps = Object.keys(data.load).sort();
                if (timestamps.length === 0) {
                     if (chart) {
                        chart.destroy();
                        chart = null;
                    }
                    return;
                }

                const loadData = timestamps.map(ts => data.load[ts]);

                // Get all unique generation source names across all timestamps
                const generationSources = [...new Set(Object.values(data.generation).flatMap(gen => Object.keys(gen)))];

                const generationDatasets = generationSources.map(source => {
                    return {
                        type: 'bar',
                        label: `${source} (MW)`,
                        data: timestamps.map(ts => data.generation[ts] ? data.generation[ts][source] || 0 : 0),
                        backgroundColor: getRandomColor(),
                        yAxisID: 'y1'
                    };
                });

                // --- Axis Synchronization Logic ---
                // Calculate the maximum value across all datasets to synchronize the Y-axes.
                const maxLoad = loadData.length > 0 ? Math.max(...loadData) : 0;

                let maxGeneration = 0;
                if (generationDatasets.length > 0 && timestamps.length > 0) {
                    // For stacked bars, the max is the highest sum at any single point.
                    const summedGeneration = timestamps.map((_, i) =>
                        generationDatasets.reduce((sum, dataset) => sum + (dataset.data[i] || 0), 0)
                    );
                    maxGeneration = Math.max(...summedGeneration);
                }

                // Determine the overall maximum and add a small buffer (e.g., 10%) for better visualization.
                const overallMax = Math.max(maxLoad, maxGeneration);
                const suggestedMax = overallMax * 1.1;
                // --- End of Axis Synchronization Logic ---


                const chartData = {
                    labels: timestamps.map(key => formatMonthHourLabel(key)),
                    datasets: [
                        {
                            type: 'line',
                            label: 'Total Load (MW)',
                            data: loadData,
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            yAxisID: 'y',
                            tension: 0.4,
                            fill: true
                        },
                        ...generationDatasets
                    ]
                };

                if (chart) {
                    chart.data = chartData;
                    chart.options.scales.y.max = suggestedMax;
                    chart.options.scales.y1.stacked = generationIds.length > 0;
                    chart.options.scales.y1.max = suggestedMax;
                    chart.update();
                } else {
                    chart = new Chart(ctx, {
                        type: 'bar', // This is a default, individual datasets override it
                        data: chartData,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    type: 'linear',
                                    position: 'left',
                                    title: {
                                        display: true,
                                        text: 'Load (MW)'
                                    },
                                    min: 0,
                                    max: suggestedMax
                                },
                                y1: {
                                    type: 'linear',
                                    position: 'right',
                                    stacked: generationIds.length > 0, // Only stack if there's generation data
                                    title: {
                                        display: true,
                                        text: 'Generation (MW)'
                                    },
                                    grid: { drawOnChartArea: false },
                                    min: 0,
                                    max: suggestedMax
                                },
                                x: {
                                    stacked: true,
                                    title: { display: true, text: 'Time' }
                                }
                            }
                        }
                    });
                }
            });
    }

    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    function formatMonthHourLabel(key) {
        const [month, hour] = key.split('-');
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const monthIndex = parseInt(month, 10) - 1;
        if (monthIndex >= 0 && monthIndex < 12) {
            return `${monthNames[monthIndex]}-${hour}`;
        }
        return key; // Fallback
    }

    if (selectAllLoad && loadSelect) {
        selectAllLoad.addEventListener('change', () => {
            const checkboxes = loadSelect.querySelectorAll('input[name="load"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllLoad.checked;
            });
            updateChart();
        });
        loadSelect.addEventListener('change', updateChart);
    }

    if (selectAllGeneration && generationSelect) {
        selectAllGeneration.addEventListener('change', () => {
            const checkboxes = generationSelect.querySelectorAll('input[name="generation"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllGeneration.checked;
            });
            updateChart();
        });
        generationSelect.addEventListener('change', updateChart);
    }

    // Initial chart load (optional, if you want to pre-select items)
    updateChart(); // Call on load to render an empty state or initial data if any are pre-selected.
});