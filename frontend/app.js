// Theme Dark/Light toggle logic
const themeToggleBtn = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('theme') || 'light';

if (currentTheme === 'dark') {
    document.body.setAttribute('data-theme', 'dark');
} else {
    document.body.setAttribute('data-theme', 'light');
}

document.addEventListener('DOMContentLoaded', () => {
    if (currentTheme === 'dark') {
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    } else {
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }
});

themeToggleBtn.addEventListener('click', () => {
    const activeTheme = document.body.getAttribute('data-theme');
    if (activeTheme === 'dark') {
        document.body.setAttribute('data-theme', 'light');
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        localStorage.setItem('theme', 'light');
        updateChartsTheme('light');
    } else {
        document.body.setAttribute('data-theme', 'dark');
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
        updateChartsTheme('dark');
    }
});

function updateChartsTheme(theme) {
    const textColor = theme === 'dark' ? '#f5f6fa' : '#323338';
    const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
    const tickColor = theme === 'dark' ? '#a4b0be' : '#676879';

    [sectorChartInstance, pipelineChartInstance, ownerChartInstance, woChartInstance].forEach(chart => {
        if (chart) {
            if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            if (chart.options.scales) {
                for (const scaleKey in chart.options.scales) {
                    const scale = chart.options.scales[scaleKey];
                    if (scale.ticks) scale.ticks.color = tickColor;
                    if (scale.grid) scale.grid.color = gridColor;
                }
            }
            chart.update();
        }
    });
}

// Navigation tab switching
const navButtons = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.workspace-section');
const mainHeading = document.getElementById('main-heading');

navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // Toggle Nav Items Active State
        navButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show corresponding workspace section
        const targetSection = btn.id.replace('nav-', '').replace('-btn', '') + '-section';
        sections.forEach(sec => {
            if (sec.id === targetSection) {
                sec.classList.add('active');
            } else {
                sec.classList.remove('active');
            }
        });

        // Update header heading
        if (btn.id === 'nav-overview-btn') {
            mainHeading.textContent = 'Executive System Overview';
        } else if (btn.id === 'nav-chat-btn') {
            mainHeading.textContent = 'Monday.com BI Insights';
        } else if (btn.id === 'nav-dashboard-btn') {
            mainHeading.textContent = 'Executive Leadership Dashboard';
            loadDashboardData();
        } else if (btn.id === 'nav-explorer-btn') {
            mainHeading.textContent = 'Interactive Data Explorer';
            initExplorer();
        } else if (btn.id === 'nav-reports-btn') {
            mainHeading.textContent = 'Leadership Reports Export';
            loadLeadershipReport();
        }
    });
});

// Chat Integration Logic
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatFeed = document.getElementById('chat-feed');
const sqlPanel = document.getElementById('sql-panel');
const sqlCode = document.getElementById('sql-code');
const closeSqlBtn = document.getElementById('close-sql-btn');

closeSqlBtn.addEventListener('click', () => {
    sqlPanel.classList.add('hidden');
});

// Suggested query click handler
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.suggest-btn');
    if (btn) {
        const query = btn.getAttribute('data-query');
        chatInput.value = query;
        chatForm.dispatchEvent(new Event('submit'));
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Clear input and disable
    chatInput.value = '';
    chatInput.disabled = true;
    const submitBtn = document.getElementById('chat-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    // Append User Message bubble
    appendMessage(query, 'user-message');

    // Append Bot Message placeholder with typing indicator
    const botMsgId = 'bot-' + Date.now();
    const botBubble = appendMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', 'bot-message', botMsgId);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: query })
        });
        const data = await res.json();

        // Re-enable input
        chatInput.disabled = false;
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
        chatInput.focus();

        // Remove typing indicator and render response
        const bubbleContent = botBubble.querySelector('.message-bubble');
        bubbleContent.innerHTML = ''; // clear

        if (data.error) {
            bubbleContent.textContent = 'Apologies, I encountered an error: ' + data.error;
            return;
        }

        // Render response content
        const rawText = data.response;
        const sqlQuery = data.sql;

        // Parse markdown formatting
        const { cleanText, chartConfig } = extractAndParseContent(rawText);
        
        // Insert clean response text
        const textPara = document.createElement('div');
        textPara.innerHTML = cleanText;
        bubbleContent.appendChild(textPara);

        // Render inline chart if config is present
        if (chartConfig) {
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chat-chart-container';
            const canvas = document.createElement('canvas');
            const canvasId = 'chart-' + Date.now();
            canvas.id = canvasId;
            chartDiv.appendChild(canvas);
            bubbleContent.appendChild(chartDiv);
            
            // Build the chart
            setTimeout(() => {
                const activeTheme = document.body.getAttribute('data-theme') || 'light';
                const textColor = activeTheme === 'dark' ? '#f5f6fa' : '#323338';
                const tickColor = activeTheme === 'dark' ? '#a4b0be' : '#676879';
                const gridColor = activeTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

                new Chart(canvas, {
                    type: chartConfig.type,
                    data: chartConfig.data || {
                        labels: chartConfig.labels,
                        datasets: chartConfig.datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                labels: { color: textColor }
                            }
                        },
                        scales: chartConfig.type !== 'pie' && chartConfig.type !== 'doughnut' ? {
                            x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                            y: { grid: { color: gridColor }, ticks: { color: tickColor } }
                        } : {}
                    }
                });
            }, 100);
        }

        // Add view SQL actions if available
        if (sqlQuery) {
            const sqlBtn = document.createElement('button');
            sqlBtn.className = 'suggest-btn';
            sqlBtn.style.marginTop = '10px';
            sqlBtn.innerHTML = '<i class="fa-solid fa-code"></i> View SQL Query';
            sqlBtn.addEventListener('click', () => {
                sqlCode.textContent = sqlQuery;
                sqlPanel.classList.remove('hidden');
            });
            bubbleContent.appendChild(sqlBtn);
        }

        // Scroll chat feed
        chatFeed.scrollTop = chatFeed.scrollHeight;

    } catch (err) {
        console.error('Fetch error:', err);
        chatInput.disabled = false;
        const submitBtn = document.getElementById('chat-submit-btn');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
        const bubbleContent = botBubble.querySelector('.message-bubble');
        bubbleContent.textContent = 'Connection to the BI Agent server failed.';
    }
});

function appendMessage(text, className, id = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${className}`;
    if (id) msgDiv.id = id;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.innerHTML = className === 'bot-message' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = text;

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(bubbleDiv);
    chatFeed.appendChild(msgDiv);

    // Scroll to bottom
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return msgDiv;
}

// Extract Chart markdown configs and format Markdown
function extractAndParseContent(text) {
    let cleanText = text;
    let chartConfig = null;

    // Look for ```chart code block
    const chartRegex = /```chart\r?\n([\s\S]*?)\r?\n```/;
    const match = cleanText.match(chartRegex);
    if (match) {
        try {
            chartConfig = JSON.parse(match[1].trim());
            // Remove block from the text
            cleanText = cleanText.replace(match[0], '');
        } catch (e) {
            console.error('Error parsing chart config JSON:', e);
        }
    }

    // Basic markdown replacement
    cleanText = cleanText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/●\s+(.*?)(?=\n|$)/g, '<li>$1</li>')
        .replace(/-\s+(.*?)(?=\n|$)/g, '<li>$1</li>');

    // Replace newlines with breaks
    cleanText = cleanText.trim().replace(/\n/g, '<br>');
    
    // Group consecutive list items into ul tags
    cleanText = cleanText.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

    return { cleanText, chartConfig };
}

// Dashboard Charts Cache variables
let sectorChartInstance = null;
let pipelineChartInstance = null;
let ownerChartInstance = null;
let woChartInstance = null;

async function loadDashboardData() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        
        // Calculate Totals for Stat Widgets
        let totalWon = 0;
        let totalOpen = 0;
        let totalDeals = 0;
        
        data.deals_status.forEach(r => {
            const val = r.value || 0;
            if (r.deal_status === 'Won') {
                totalWon += val;
            } else if (r.deal_status === 'Open') {
                totalOpen += val;
            }
            totalDeals += r.count;
        });

        // Set Values
        document.getElementById('stat-won-revenue').textContent = formatCurrency(totalWon);
        document.getElementById('stat-active-pipeline').textContent = formatCurrency(totalOpen);
        document.getElementById('stat-total-deals').textContent = totalDeals;
        
        // Work Orders Active Count (Ongoing + Not Started)
        let activeWos = 0;
        data.work_orders_status.forEach(r => {
            if (r.execution_status === 'Ongoing' || r.execution_status === 'Not Started') {
                activeWos += r.count;
            }
        });
        document.getElementById('stat-active-wos').textContent = activeWos;

        // Render Dashboard Charts
        renderDashboardCharts(data);

    } catch (err) {
        console.error('Error fetching dashboard stats:', err);
    }
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(val);
}

function renderDashboardCharts(data) {
    const activeTheme = document.body.getAttribute('data-theme') || 'light';
    const textColor = activeTheme === 'dark' ? '#f5f6fa' : '#323338';
    const tickColor = activeTheme === 'dark' ? '#a4b0be' : '#676879';
    const gridColor = activeTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { labels: { color: textColor, font: { family: 'Outfit' } } }
        }
    };

    // 1. Sectoral Deals (Bar Chart)
    const sectorLabels = data.sector_deals.map(r => r.sector_service || 'Other');
    const sectorValues = data.sector_deals.map(r => r.value || 0);
    
    if (sectorChartInstance) sectorChartInstance.destroy();
    sectorChartInstance = new Chart(document.getElementById('sectorChart'), {
        type: 'bar',
        data: {
            labels: sectorLabels,
            datasets: [{
                label: 'Pipeline Value (₹)',
                data: sectorValues,
                backgroundColor: 'rgba(0, 210, 211, 0.45)',
                borderColor: '#00d2d3',
                borderWidth: 1.5
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                y: { grid: { color: gridColor }, ticks: { color: tickColor } }
            }
        }
    });

    // 2. Deals Status Pipeline Health (Pie Chart)
    const statusLabels = data.deals_status.map(r => r.deal_status || 'Unknown');
    const statusValues = data.deals_status.map(r => r.value || 0);
    
    if (pipelineChartInstance) pipelineChartInstance.destroy();
    pipelineChartInstance = new Chart(document.getElementById('pipelineChart'), {
        type: 'pie',
        data: {
            labels: statusLabels,
            datasets: [{
                data: statusValues,
                backgroundColor: [
                    'rgba(46, 213, 115, 0.55)', // Won - Green
                    'rgba(0, 210, 211, 0.55)',  // Open - Blue
                    'rgba(255, 71, 87, 0.55)',   // Dead - Red
                    'rgba(255, 165, 2, 0.55)'    // On Hold - Amber
                ],
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1.5
            }]
        },
        options: chartOptions
    });

    // 3. Top Owners Revenue (Horizontal Bar Chart)
    const ownerLabels = data.owner_ranking.map(r => r.owner_code || 'Unknown');
    const ownerValues = data.owner_ranking.map(r => r.value || 0);
    
    if (ownerChartInstance) ownerChartInstance.destroy();
    ownerChartInstance = new Chart(document.getElementById('ownerChart'), {
        type: 'bar',
        data: {
            labels: ownerLabels,
            datasets: [{
                label: 'Won Revenue (₹)',
                data: ownerValues,
                backgroundColor: 'rgba(255, 165, 2, 0.45)', // Amber
                borderColor: '#ffa502',
                borderWidth: 1.5
            }]
        },
        options: {
            ...chartOptions,
            indexAxis: 'y',
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                y: { grid: { color: gridColor }, ticks: { color: tickColor } }
            }
        }
    });

    // 4. Work Orders execution (Doughnut Chart)
    const woLabels = data.work_orders_status.map(r => r.execution_status || 'Unknown');
    const woValues = data.work_orders_status.map(r => r.value || 0);
    
    if (woChartInstance) woChartInstance.destroy();
    woChartInstance = new Chart(document.getElementById('woChart'), {
        type: 'doughnut',
        data: {
            labels: woLabels,
            datasets: [{
                data: woValues,
                backgroundColor: [
                    'rgba(46, 213, 115, 0.55)', // Completed
                    'rgba(0, 210, 211, 0.55)',  // Ongoing
                    'rgba(255, 165, 2, 0.55)',  // Executed until current
                    'rgba(255, 71, 87, 0.55)',   // Pause / struck
                    'rgba(164, 176, 190, 0.55)'  // Not Started
                ],
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1.5
            }]
        },
        options: chartOptions
    });
}

// Data Explorer variables
let explorerInitialized = false;
let explorerCurrentTab = 'deals';
let explorerDealsData = [];
let explorerWosData = [];
let explorerFilteredData = [];
let explorerCurrentPage = 1;
const explorerPageSize = 15;
let explorerSortKey = null;
let explorerSortAsc = true;

// DOM Elements cache
let explorerTabDeals;
let explorerTabWos;
let explorerSearchInput;
let filterStatusSelect;
let filterSectorSelect;
let filterSectorGroup;
let explorerResetBtn;
let explorerExportCsvBtn;
let explorerTableHeader;
let explorerTableBody;
let explorerEmptyState;
let paginationInfo;
let prevPageBtn;
let nextPageBtn;
let currentPageNum;

async function initExplorer() {
    // Cache DOM Elements if not already done
    if (!explorerTabDeals) {
        explorerTabDeals = document.getElementById('tab-deals-btn');
        explorerTabWos = document.getElementById('tab-wos-btn');
        explorerSearchInput = document.getElementById('explorer-search');
        filterStatusSelect = document.getElementById('filter-status');
        filterSectorSelect = document.getElementById('filter-sector');
        filterSectorGroup = document.getElementById('filter-sector-group');
        explorerResetBtn = document.getElementById('explorer-reset-btn');
        explorerExportCsvBtn = document.getElementById('explorer-export-csv');
        explorerTableHeader = document.getElementById('explorer-table-header');
        explorerTableBody = document.getElementById('explorer-table-body');
        explorerEmptyState = document.getElementById('explorer-empty-state');
        paginationInfo = document.getElementById('pagination-info');
        prevPageBtn = document.getElementById('prev-page-btn');
        nextPageBtn = document.getElementById('next-page-btn');
        currentPageNum = document.getElementById('current-page-num');
    }

    // Set up event listeners once
    if (!explorerInitialized) {
        explorerTabDeals.addEventListener('click', () => switchExplorerTab('deals'));
        explorerTabWos.addEventListener('click', () => switchExplorerTab('wos'));
        
        explorerSearchInput.addEventListener('input', () => {
            explorerCurrentPage = 1;
            applyFiltersAndSearch();
        });
        
        filterStatusSelect.addEventListener('change', () => {
            explorerCurrentPage = 1;
            applyFiltersAndSearch();
        });
        
        filterSectorSelect.addEventListener('change', () => {
            explorerCurrentPage = 1;
            applyFiltersAndSearch();
        });
        
        explorerResetBtn.addEventListener('click', () => resetExplorerFilters());
        explorerExportCsvBtn.addEventListener('click', () => exportExplorerToCSV());
        
        prevPageBtn.addEventListener('click', () => {
            if (explorerCurrentPage > 1) {
                explorerCurrentPage--;
                renderExplorerTable();
            }
        });
        
        nextPageBtn.addEventListener('click', () => {
            const maxPage = Math.ceil(explorerFilteredData.length / explorerPageSize);
            if (explorerCurrentPage < maxPage) {
                explorerCurrentPage++;
                renderExplorerTable();
            }
        });
        
        explorerInitialized = true;
    }

    // Fetch data if empty
    if (explorerDealsData.length === 0 || explorerWosData.length === 0) {
        explorerTableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px;"><i class="fa-solid fa-spinner fa-spin" style="font-size: 24px; margin-bottom: 12px; color: var(--accent-blue);"></i><br>Loading records from database...</td></tr>`;
        await fetchExplorerData();
    }

    applyFiltersAndSearch();
}

async function fetchExplorerData() {
    try {
        const [dealsRes, wosRes] = await Promise.all([
            fetch('/api/deals'),
            fetch('/api/work_orders')
        ]);
        explorerDealsData = await dealsRes.json();
        explorerWosData = await wosRes.json();
    } catch (e) {
        console.error('Error fetching explorer data:', e);
    }
}

function switchExplorerTab(tab) {
    if (explorerCurrentTab === tab) return;
    
    explorerCurrentTab = tab;
    explorerSortKey = null;
    explorerSortAsc = true;
    explorerCurrentPage = 1;
    explorerSearchInput.value = '';

    if (tab === 'deals') {
        explorerTabDeals.classList.add('active');
        explorerTabWos.classList.remove('active');
        filterSectorGroup.classList.remove('hidden');
    } else {
        explorerTabDeals.classList.remove('active');
        explorerTabWos.classList.add('active');
        filterSectorGroup.classList.add('hidden');
    }

    populateFilters();
    applyFiltersAndSearch();
}

function populateFilters() {
    filterStatusSelect.innerHTML = '<option value="all">All Statuses</option>';
    
    if (explorerCurrentTab === 'deals') {
        const statuses = [...new Set(explorerDealsData.map(r => r.deal_status).filter(Boolean))];
        statuses.forEach(st => {
            filterStatusSelect.innerHTML += `<option value="${st}">${st}</option>`;
        });
        
        filterSectorSelect.innerHTML = '<option value="all">All Sectors</option>';
        const sectors = [...new Set(explorerDealsData.map(r => r.sector_service).filter(Boolean))];
        sectors.forEach(sec => {
            filterSectorSelect.innerHTML += `<option value="${sec}">${sec}</option>`;
        });
    } else {
        const statuses = [...new Set(explorerWosData.map(r => r.execution_status).filter(Boolean))];
        statuses.forEach(st => {
            filterStatusSelect.innerHTML += `<option value="${st}">${st}</option>`;
        });
    }
}

function resetExplorerFilters() {
    explorerSearchInput.value = '';
    filterStatusSelect.value = 'all';
    filterSectorSelect.value = 'all';
    explorerCurrentPage = 1;
    applyFiltersAndSearch();
}

function applyFiltersAndSearch() {
    const searchVal = explorerSearchInput.value.trim().toLowerCase();
    const statusVal = filterStatusSelect.value;
    const sectorVal = filterSectorSelect ? filterSectorSelect.value : 'all';
    
    const sourceData = explorerCurrentTab === 'deals' ? explorerDealsData : explorerWosData;
    
    explorerFilteredData = sourceData.filter(row => {
        let matchesSearch = true;
        if (searchVal) {
            matchesSearch = false;
            for (const key in row) {
                if (row[key] && String(row[key]).toLowerCase().includes(searchVal)) {
                    matchesSearch = true;
                    break;
                }
            }
        }
        
        let matchesStatus = true;
        if (statusVal !== 'all') {
            const statusKey = explorerCurrentTab === 'deals' ? 'deal_status' : 'execution_status';
            matchesStatus = row[statusKey] === statusVal;
        }
        
        let matchesSector = true;
        if (explorerCurrentTab === 'deals' && sectorVal !== 'all') {
            matchesSector = row.sector_service === sectorVal;
        }
        
        return matchesSearch && matchesStatus && matchesSector;
    });

    if (filterStatusSelect.options.length <= 1) {
        populateFilters();
    }
    
    renderExplorerTable();
}

function renderExplorerTable() {
    const columns = explorerCurrentTab === 'deals' ? [
        ['deal_id', 'ID', false, false, false],
        ['deal_name', 'Deal Name', false, false, false],
        ['owner_code', 'Owner', false, false, false],
        ['client_code', 'Client', false, false, false],
        ['sector_service', 'Sector', false, false, false],
        ['deal_stage', 'Stage', false, false, false],
        ['masked_deal_value', 'Value', true, true, false],
        ['deal_status', 'Status', false, false, true]
    ] : [
        ['serial_num', 'Serial Num', false, false, false],
        ['deal_name_masked', 'Deal Name', false, false, false],
        ['customer_name_code', 'Customer', false, false, false],
        ['nature_of_work', 'Nature of Work', false, false, false],
        ['execution_status', 'Status', false, false, true],
        ['billed_excl_gst', 'Billed (Ex GST)', true, true, false],
        ['amount_receivable', 'Receivable', true, true, false],
        ['billing_status', 'Billing Status', false, false, false]
    ];

    explorerTableHeader.innerHTML = '';
    columns.forEach(([key, label, isNum, isCur, isBadge]) => {
        const th = document.createElement('th');
        th.style.cursor = 'pointer';
        
        let arrow = '';
        if (explorerSortKey === key) {
            arrow = explorerSortAsc ? ' ▲' : ' ▼';
            th.style.color = 'var(--accent-blue)';
        }
        
        th.innerHTML = `${label}${arrow}`;
        th.addEventListener('click', () => {
            if (explorerSortKey === key) {
                explorerSortAsc = !explorerSortAsc;
            } else {
                explorerSortKey = key;
                explorerSortAsc = true;
            }
            renderExplorerTable();
        });
        explorerTableHeader.appendChild(th);
    });

    if (explorerSortKey) {
        explorerFilteredData.sort((a, b) => {
            let valA = a[explorerSortKey];
            let valB = b[explorerSortKey];
            
            if (valA === null || valA === undefined) valA = '';
            if (valB === null || valB === undefined) valB = '';
            
            if (typeof valA === 'number' && typeof valB === 'number') {
                return explorerSortAsc ? valA - valB : valB - valA;
            }
            
            return explorerSortAsc 
                ? String(valA).localeCompare(String(valB)) 
                : String(valB).localeCompare(String(valA));
        });
    }

    const totalRecords = explorerFilteredData.length;
    const maxPage = Math.ceil(totalRecords / explorerPageSize) || 1;
    if (explorerCurrentPage > maxPage) explorerCurrentPage = maxPage;
    
    const startIndex = (explorerCurrentPage - 1) * explorerPageSize;
    const endIndex = Math.min(startIndex + explorerPageSize, totalRecords);
    const paginatedData = explorerFilteredData.slice(startIndex, endIndex);

    explorerTableBody.innerHTML = '';
    
    if (totalRecords === 0) {
        explorerEmptyState.classList.remove('hidden');
    } else {
        explorerEmptyState.classList.add('hidden');
        
        paginatedData.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(([key, label, isNum, isCur, isBadge]) => {
                const td = document.createElement('td');
                const val = row[key];
                
                if (isBadge && val) {
                    const badgeClass = 'badge-' + String(val).toLowerCase().replace(/[^a-z0-9]/g, '');
                    td.innerHTML = `<span class="badge ${badgeClass}">${val}</span>`;
                } else if (isCur && val !== null && val !== undefined) {
                    td.textContent = formatCurrency(val);
                } else if (val === null || val === undefined) {
                    td.innerHTML = `<span style="opacity: 0.35;">-</span>`;
                } else {
                    td.textContent = val;
                }
                tr.appendChild(td);
            });
            explorerTableBody.appendChild(tr);
        });
    }

    currentPageNum.textContent = explorerCurrentPage;
    paginationInfo.textContent = totalRecords > 0 
        ? `Showing ${startIndex + 1} to ${endIndex} of ${totalRecords} entries`
        : `Showing 0 to 0 of 0 entries`;
        
    prevPageBtn.disabled = explorerCurrentPage <= 1;
    nextPageBtn.disabled = explorerCurrentPage >= maxPage;
}

function exportExplorerToCSV() {
    if (explorerFilteredData.length === 0) return;
    
    const headers = Object.keys(explorerFilteredData[0]);
    let csvContent = headers.join(',') + '\n';
    
    explorerFilteredData.forEach(row => {
        const rowValues = headers.map(header => {
            let val = row[header];
            if (val === null || val === undefined) val = '';
            val = String(val).replace(/"/g, '""');
            if (val.includes(',') || val.includes('\n')) val = `"${val}"`;
            return val;
        });
        csvContent += rowValues.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `explorer_export_${explorerCurrentTab}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Variable to store the markdown report content for download/copy actions
let compiledReportMarkdown = "";
let compiledReportText = "";

async function loadLeadershipReport() {
    try {
        const res = await fetch('/api/leadership-report');
        const data = await res.json();

        // 1. Dynamic Calculations
        const openDealsCount = data.open_deals_count || 0;
        const openPipeline = data.open_pipeline || 0;
        const weightedRevenue = data.probability_weighted_revenue || 0;
        const wonRevenue = data.realized_won_revenue || 0;
        const deliveredWorkOrders = data.delivered_work_orders_count || 0;
        const billedWorkOrderValue = data.billed_work_order_value || 0;
        const outstandingReceivables = data.outstanding_receivables || 0;

        const pipelineCr = (openPipeline / 10000000).toFixed(2);
        const weightedCr = (weightedRevenue / 10000000).toFixed(2);
        const billedLakhs = (billedWorkOrderValue / 100000).toFixed(2);

        // Update Date label dynamically
        const dateStr = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        document.getElementById('report-date-str').textContent = dateStr;

        // 2. Executive Summary text compilation
        const summaryText = `Skylark Drones is tracking a <strong>total sales pipeline of ₹${pipelineCr} Cr</strong> across <strong>${openDealsCount} active deals</strong>, with a probability-weighted expected revenue of <strong>₹${weightedCr} Cr</strong>. Operations have successfully delivered <strong>${deliveredWorkOrders} work orders</strong>, achieving a total billed value of <strong>₹${billedLakhs} Lakhs</strong>.`;
        document.getElementById('report-exec-summary').innerHTML = summaryText;

        // 3. Table fields
        document.getElementById('td-open-pipeline').textContent = formatCurrencyWithDecimals(openPipeline);
        document.getElementById('td-weighted-rev').textContent = formatCurrencyWithDecimals(weightedRevenue);
        document.getElementById('td-realized-won').textContent = formatCurrencyWithDecimals(wonRevenue);
        document.getElementById('td-billed-wo').textContent = formatCurrencyWithDecimals(billedWorkOrderValue);
        document.getElementById('td-outstanding-ar').textContent = formatCurrencyWithDecimals(outstandingReceivables);

        // 4. Compile Markdown & Plain Text for export/copy actions
        compiledReportMarkdown = `# Skylark Drones - Executive Leadership Update

**Date:** ${dateStr}
**Data Source:** Dynamic Monday.com Integrations (Deals Board & Work Orders Board)

### 1. Executive Summary
Skylark Drones is tracking a total sales pipeline of ₹${pipelineCr} Cr across ${openDealsCount} active deals, with a probability-weighted expected revenue of ₹${weightedCr} Cr. Operations have successfully delivered ${deliveredWorkOrders} work orders, achieving a total billed value of ₹${billedLakhs} Lakhs.

### 2. Revenue & Financial Overview

| Financial Metric | Amount (INR) | Key Observations |
| :--- | :--- | :--- |
| **Total Open Pipeline** | ${formatCurrencyWithDecimals(openPipeline)} | Driven primarily by large Mining & Powerline sector proposals |
| **Probability-Weighted Revenue** | ${formatCurrencyWithDecimals(weightedRevenue)} | Adjusted for High (80%), Medium (50%), and Low (20%) closure probability |
| **Realized Won Revenue** | ${formatCurrencyWithDecimals(wonRevenue)} | Closed-won contract commitments |
| **Billed Work Order Value** | ${formatCurrencyWithDecimals(billedWorkOrderValue)} | Invoiced operational deliveries |
| **Outstanding Receivables** | ${formatCurrencyWithDecimals(outstandingReceivables)} | Requires collection prioritization for priority accounts |
`;

        compiledReportText = `Skylark Drones - Executive Leadership Update
Date: ${dateStr}
Data Source: Dynamic Monday.com Integrations (Deals Board & Work Orders Board)

1. Executive Summary
Skylark Drones is tracking a total sales pipeline of ₹${pipelineCr} Cr across ${openDealsCount} active deals, with a probability-weighted expected revenue of ₹${weightedCr} Cr. Operations have successfully delivered ${deliveredWorkOrders} work orders, achieving a total billed value of ₹${billedLakhs} Lakhs.

2. Revenue & Financial Overview
- Total Open Pipeline: ${formatCurrencyWithDecimals(openPipeline)} (Driven primarily by large Mining & Powerline sector proposals)
- Probability-Weighted Revenue: ${formatCurrencyWithDecimals(weightedRevenue)} (Adjusted for High (80%), Medium (50%), and Low (20%) closure probability)
- Realized Won Revenue: ${formatCurrencyWithDecimals(wonRevenue)} (Closed-won contract commitments)
- Billed Work Order Value: ${formatCurrencyWithDecimals(billedWorkOrderValue)} (Invoiced operational deliveries)
- Outstanding Receivables: ${formatCurrencyWithDecimals(outstandingReceivables)} (Requires collection prioritization for priority accounts)
`;

    } catch (err) {
        console.error("Error generating leadership report:", err);
    }
}

function formatCurrencyWithDecimals(val) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(val);
}

// Sub-navigation Switcher inside Reports section
document.querySelectorAll('.reports-sub-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.reports-sub-nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const targetPane = btn.getAttribute('data-pane');
        document.querySelectorAll('.reports-pane').forEach(pane => {
            if (pane.id === targetPane) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });
    });
});

// Copy Report to Clipboard
document.getElementById('copy-report-btn').addEventListener('click', () => {
    if (!compiledReportText) return;
    navigator.clipboard.writeText(compiledReportText).then(() => {
        const copyBtn = document.getElementById('copy-report-btn');
        const origHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fa-solid fa-check" style="color: #00c875;"></i> Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = origHtml;
        }, 1500);
    }).catch(err => {
        console.error("Could not copy text: ", err);
    });
});

// Download Report as Markdown file
document.getElementById('download-report-btn').addEventListener('click', () => {
    if (!compiledReportMarkdown) return;
    const blob = new Blob([compiledReportMarkdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Skylark_Executive_Report_${Date.now()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});
