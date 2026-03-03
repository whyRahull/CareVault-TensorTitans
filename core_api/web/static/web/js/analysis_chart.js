/*
 * analysis_chart.js
 * Renders the 7-day stacked bar chart showing low vs high severity incidents.
 * Expects window.CHART_DATA to be defined and populated by the backend.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Fallback if data is missing
    const defaultData = { labels: [], low_severity: [], high_severity: [] };
    const data = window.CHART_DATA || defaultData;

    const container = document.getElementById('chart-container');
    const labelsContainer = document.getElementById('chart-labels');

    if (!container || !labelsContainer) return;

    // Find max daily total to scale bars properly
    let maxTotal = 0;
    for (let i = 0; i < data.labels.length; i++) {
        const total = data.low_severity[i] + data.high_severity[i];
        if (total > maxTotal) maxTotal = total;
    }
    // Avoid div by zero, give it a floor
    maxTotal = Math.max(maxTotal, 10);

    // Render Bars
    for (let i = 0; i < data.labels.length; i++) {
        const low = data.low_severity[i];
        const high = data.high_severity[i];
        const total = low + high;

        const lowPct = (low / maxTotal) * 100;
        const highPct = (high / maxTotal) * 100;

        // Bar wrapper
        const col = document.createElement('div');
        col.className = 'flex-grow flex flex-col justify-end group relative transition-all rounded-t-lg overflow-hidden h-full';
        col.style.width = '10%';

        // Tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap pointer-events-none';
        tooltip.innerHTML = `<strong>${total}</strong> Total<br/><span class="text-red-400">${high} High</span> | <span class="text-gray-400">${low} Low</span>`;
        col.appendChild(tooltip);

        // High Severity Segment
        if (high > 0) {
            const highDiv = document.createElement('div');
            highDiv.className = 'bg-red-500 w-full transition-all group-hover:bg-red-400 rounded-t-sm';
            highDiv.style.height = `${highPct}%`;
            col.appendChild(highDiv);
        }

        // Low Severity Segment
        if (low > 0) {
            const lowDiv = document.createElement('div');
            lowDiv.className = `bg-gray-200 w-full transition-all group-hover:bg-gray-300 ${high === 0 ? 'rounded-t-sm' : ''}`;
            lowDiv.style.height = `${lowPct}%`;
            col.appendChild(lowDiv);
        }

        // Empty state filler if 0
        if (total === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'w-full h-1 bg-gray-50 rounded-t-sm';
            col.appendChild(emptyDiv);
        }

        container.appendChild(col);

        // Label
        const lbl = document.createElement('span');
        lbl.innerText = data.labels[i];
        labelsContainer.appendChild(lbl);
    }
});
