// Joomoki Stock Portal App Logic - AI/Dark Theme Edition
console.log('Joomoki Stock Portal App Loaded');

document.addEventListener('DOMContentLoaded', () => {
    loadStockData();
    setupSearch();
});

let allStocks = []; // Currently displayed stocks
let domesticStocks = [];
let currentMarket = 'domestic';

// Sort State
let sortState = {
    column: null, // 'price', 'change', 'signal', 'score'
    order: 'desc' // 'asc', 'desc'
};

// Pagination State
let currentPage = 1;
const itemsPerPage = 20;
let currentDisplayedStocks = []; // Filtered list

// Fetch Data
function loadStockData() {
    try {
        if (typeof stockData === 'undefined') {
            throw new Error('Stock data not found. Please check data/stock_data.js');
        }

        const data = stockData;

        // Update Metadata
        const dateStr = data.last_updated || new Date().toLocaleString();

        // 업데이트 날짜
        let simpleDateStr = "";
        if (data.market_dates) {
            const kDate = data.market_dates.korea || '-';
            simpleDateStr = `국내 ${kDate}`;
        }

        const dateEl = document.getElementById('last-updated');
        if (dateEl) dateEl.textContent = `업데이트: ${dateStr}`;

        const marketDatesEl = document.getElementById('market-dates-display');
        if (marketDatesEl) {
            marketDatesEl.textContent = simpleDateStr;
        }

        if (data.stats) {
            const domEl = document.getElementById('count-domestic');
            if (domEl) domEl.textContent = data.stats.korea_total;
        }

        domesticStocks = data.stocks || [];

        // 정렬 사전 계산
        preprocessData(domesticStocks);

        // 초기 화면
        updateMarketView();

    } catch (error) {
        console.error('Error loading stock data:', error);
        const container = document.getElementById('top-picks-container');
        if (container) container.innerHTML = `<div class="col-12 text-center text-danger">데이터를 불러오는데 실패했습니다.<br>(${error.message})</div>`;
    }
}

function updateMarketView() {
    // 국내 주식 고정
    currentMarket = 'domestic';
    allStocks = domesticStocks;
    currentDisplayedStocks = allStocks;

    const picks = stockData.top_picks;
    renderTopPicks(picks);

    currentPage = 1;
    applySort(currentDisplayedStocks);
    renderStockListInternal(currentDisplayedStocks, true);
    setupPaginationControl();
}

// Data Pre-processing for Sorting Efficiency
function preprocessData(stocks) {
    stocks.forEach(stock => {
        // 1. Change Rate
        let changeRate = 0;
        if (stock.chart_data && stock.chart_data.length >= 2) {
            const last = stock.chart_data[stock.chart_data.length - 1].close;
            const prev = stock.chart_data[stock.chart_data.length - 2].close;
            changeRate = ((last - prev) / prev) * 100;
        }
        stock.computed_change_rate = changeRate; // Store for sorting

        // 2. AI Score (Fallback logic)
        let aiScore = stock.analysis.score;
        const pred = stock.analysis.prediction;
        if (!aiScore || aiScore === 0) {
            aiScore = (pred === 'UP' ? 70 : (pred === 'DOWN' ? 5 : 50));
        }
        stock.computed_score = aiScore;

        // 3. Signal Score for sorting (UP=3, HOLD=2, DOWN=1)
        let sigScore = 2;
        if (pred === 'UP') sigScore = 3;
        else if (pred === 'DOWN') sigScore = 1;
        stock.computed_signal_score = sigScore;
    });
}

// Sorting Handler
window.handleSort = function (column) {
    // Toggle order if clicking same column
    if (sortState.column === column) {
        sortState.order = sortState.order === 'desc' ? 'asc' : 'desc';
    } else {
        sortState.column = column;
        sortState.order = 'desc'; // Default new sort to desc
    }

    updateSortIcons();
    applySort(currentDisplayedStocks);

    // Reset pagination and render
    currentPage = 1;
    renderStockListInternal(currentDisplayedStocks, true);
    setupPaginationControl();
};

function applySort(stocks) {
    if (!sortState.column) return;

    stocks.sort((a, b) => {
        let valA, valB;

        switch (sortState.column) {
            case 'price':
                valA = a.price;
                valB = b.price;
                break;
            case 'change':
                valA = a.computed_change_rate;
                valB = b.computed_change_rate;
                break;
            case 'signal':
                valA = a.computed_signal_score;
                valB = b.computed_signal_score;
                break;
            case 'score':
                valA = a.computed_score;
                valB = b.computed_score;
                break;
            default:
                return 0;
        }

        if (sortState.order === 'asc') {
            return valA - valB;
        } else {
            return valB - valA;
        }
    });
}

function updateSortIcons() {
    // defined columns in HTML: price, change, signal, score
    const cols = ['price', 'change', 'signal', 'score'];
    cols.forEach(col => {
        const iconEl = document.getElementById(`sort-icon-${col}`);
        if (iconEl) {
            if (sortState.column === col) {
                iconEl.className = sortState.order === 'asc' ? 'fas fa-sort-up ms-1' : 'fas fa-sort-down ms-1';
                iconEl.style.color = '#fff'; // Active color
            } else {
                iconEl.className = 'fas fa-sort ms-1';
                iconEl.style.color = '#6c757d'; // Muted
            }
        }
    });
}

// 국내 주식 키보드 이벤트 (🔒 해외 제거)
const btnDomestic = document.getElementById('btn-domestic');
if (btnDomestic) btnDomestic.addEventListener('change', updateMarketView);


function renderTopPicks(picks) {
    const container = document.getElementById('top-picks-container');
    if (!container) return;
    container.innerHTML = '';

    if (!picks || picks.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted">현재 강력 매수 신호가 감지되지 않았습니다.</div>';
        return;
    }

    // Limit to 6 items
    const displayPicks = picks.slice(0, 6);

    displayPicks.forEach(stock => {
        // AI Score (Server provided + Fallback)
        let aiScore = stock.analysis.score;
        if (!aiScore || aiScore === 0) aiScore = 70; // Top picks are usually UP

        const cardHtml = `
            <div class="col-6 col-md-2">
                <div class="glass-card h-100 position-relative p-2" onclick="showStockDetail('${stock.code}')" style="cursor: pointer;">
                    <span class="badge badge-ai position-absolute top-0 end-0 m-2" style="font-size: 0.6rem;">AI: ${aiScore}</span>
                    <h6 class="fw-bold text-white mb-1" style="font-size: 0.9rem;">${stock.name}</h6>
                    <span class="text-muted" style="font-size: 0.7rem;">${stock.code}</span> ${getMarketBadge(stock)}
                    
                    <h5 class="text-primary fw-bold my-2" style="font-size: 1.1rem;">${formatPriceSimple(stock.price, currentMarket)}</h5>
                    
                    <p class="text-muted mb-2" style="font-size: 0.7rem; min-height: 30px; line-height: 1.2;">
                        ${stock.analysis.summary || '강력한 상승 모멘텀 감지.'}
                    </p>
                    
                    <div class="d-flex justify-content-between text-muted border-top border-secondary pt-2" style="font-size: 0.65rem;">
                        <span>PER: <span class="text-white">${formatNumber(stock.analysis.per)}</span></span>
                        <span>PBR: <span class="text-white">${formatNumber(stock.analysis.pbr)}</span></span>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', cardHtml);
    });
}

// Optimized Render function with Pagination
function renderStockListInternal(stocks, reset = false) {
    const tbody = document.getElementById('stock-list-body');
    if (!tbody) return;

    if (reset) {
        tbody.innerHTML = '';
        currentPage = 1;
    }

    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = stocks.slice(start, end);

    pageItems.forEach(stock => {
        const prediction = stock.analysis.prediction;
        let signalBadge = '<span class="badge bg-secondary">보유</span>';

        if (prediction === 'UP') {
            signalBadge = '<span class="badge badge-up">매수</span>';
        } else if (prediction === 'DOWN') {
            signalBadge = '<span class="badge badge-down">매도</span>';
        }

        // AI Score (Server provided + Client Fallback)
        let aiScore = stock.analysis.score;
        if (!aiScore || aiScore === 0) {
            aiScore = (prediction === 'UP' ? 70 : (prediction === 'DOWN' ? 5 : 50));
        }
        let barColor = 'bg-secondary';

        // High Contrast Logic for Dark Theme
        if (aiScore >= 80) {
            scoreColor = 'text-info'; // Bright Cyan
            barColor = 'bg-info';
        } else if (aiScore <= 40) {
            scoreColor = 'text-danger'; // Bright Red/Pink
            barColor = 'bg-danger';
        } else {
            scoreColor = 'text-light'; // White for neutral
            barColor = 'bg-secondary';
        }

        let changeText = '-';
        let changeClass = 'text-white';

        if (stock.chart_data && stock.chart_data.length >= 2) {
            const last = stock.chart_data[stock.chart_data.length - 1].close;
            const prev = stock.chart_data[stock.chart_data.length - 2].close;
            const diff = last - prev;
            const pct = (diff / prev) * 100;

            const sign = diff > 0 ? '+' : '';
            // Use bright colors: Cyan/Blue for Down/Neutral? No, standard is Red Up, Blue Down in KR.
            // In dark mode: 
            // Up (Red) -> text-danger (#ff3366 or similar bright red)
            // Down (Blue) -> text-info or custom bright blue
            changeClass = diff > 0 ? 'text-danger' : (diff < 0 ? 'text-info' : 'text-white');
            changeText = `${sign}${pct.toFixed(2)}%`;
        }

        // Use pre-calculated score
        aiScore = stock.computed_score;

        const rowHtml = `
            <tr onclick="showStockDetail('${stock.code}')" style="cursor: pointer;">
                <td>
                    <div class="fw-bold text-white d-flex align-items-center gap-2">
                        ${getDisplayName(stock)}
                        ${getMarketBadge(stock)}
                    </div>
                    <div class="text-muted" style="font-size:0.75rem;">${stock.code}</div>
                </td>
                <td class="fw-bold text-white">${formatPriceSimple(stock.price, currentMarket)}</td>
                <td class="${changeClass}">${changeText}</td>
                <td>${signalBadge}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <span class="fw-bold ${scoreColor} me-2">${aiScore}</span>
                        <div class="progress" style="height: 4px; width: 50px; background: rgba(255,255,255,0.1);">
                            <div class="progress-bar ${barColor}" role="progressbar" style="width: ${aiScore}%"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <small class="text-muted" style="color: #adb5bd !important;">PER: ${formatNumber(stock.analysis.per)}</small>
                </td>
                <td>
                     <canvas id="miniChart-${stock.code}" width="120" height="40"></canvas>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', rowHtml);

        // Defer Chart Rendering minimal delay
        setTimeout(() => renderMiniChart(stock.code, stock.chart_data), 0);
    });

    updateLoadMoreButton(stocks.length);
}

// Wrapper for initial call or search
function renderStockList(stocks) {
    currentDisplayedStocks = stocks;
    renderStockListInternal(stocks, true);
    setupPaginationControl();
}

function setupPaginationControl() {
    const container = document.getElementById('pagination-controls');
    if (!container) return;

    // Create Load More Button
    container.innerHTML = `
        <button id="btn-load-more" class="btn btn-outline-light btn-sm px-4 rounded-pill">
            더 보기 <i class="fas fa-chevron-down ms-1"></i>
        </button>
    `;

    // Bind click
    const btn = document.getElementById('btn-load-more');
    if (btn) {
        btn.addEventListener('click', () => {
            currentPage++;
            renderStockListInternal(currentDisplayedStocks, false);
        });
    }
}

function updateLoadMoreButton(totalItems) {
    const btn = document.getElementById('btn-load-more');
    if (!btn) return;

    const shownCount = currentPage * itemsPerPage;
    if (shownCount >= totalItems) {
        btn.style.display = 'none';
    } else {
        btn.style.display = 'inline-block';
        btn.innerHTML = `더 보기 (${Math.min(itemsPerPage, totalItems - shownCount)}개 더) <i class="fas fa-chevron-down ms-1"></i>`;
    }
}

function renderMiniChart(code, chartData) {
    if (!chartData || chartData.length === 0) return;
    const ctx = document.getElementById(`miniChart-${code}`);
    if (!ctx) return;

    const prices = chartData.map(d => d.close || d.c || 0);
    const labels = chartData.map((_, i) => i);

    // Determine color
    const start = prices[0];
    const end = prices[prices.length - 1];
    // Bright neon colors for dark mode
    const color = end >= start ? '#ff4d7d' : '#4da3ff';

    new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: prices,
                borderColor: color,
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1, // Less tension for performance
                fill: false
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            animation: false, // Critical for performance
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: { x: { display: false }, y: { display: false } },
            layout: { padding: 0 }
        }
    });
}

// --- Detail View Helpers ---
let detailChartInstance = null;
let investorChartInstance = null;

window.showStockDetail = function (code) {
    console.log(`[DEBUG] showStockDetail called for code: ${code}`);

    // 1. Robust Finding (String comparison)
    const stock = allStocks.find(s => String(s.code) === String(code));

    if (!stock) {
        console.error(`[ERROR] Stock not found for code: ${code}`);
        alert('해당 종목의 데이터를 찾을 수 없습니다.');
        return;
    }

    try {
        // 2. Populate Data
        // Use innerHTML to render HTML tags in display name
        document.getElementById('modalStockName').innerHTML = `${getDisplayName(stock)}`; // Removed redundant code display as it is in getDisplayName
        document.getElementById('modalAnalysisSummary').textContent = stock.analysis.summary || '분석 데이터 없음';
        const priceEl = document.getElementById('modalPrice');
        if (priceEl) {
            priceEl.innerHTML = formatPrice(stock.price, currentMarket);
        }

        document.getElementById('modalPER').textContent = formatNumber(stock.analysis.per);
        document.getElementById('modalPBR').textContent = formatNumber(stock.analysis.pbr);

        // Description
        const descEl = document.getElementById('modalDescription');
        if (descEl) {
            descEl.textContent = stock.description || '기업 정보가 없습니다.';
        }

        // Signals
        const signalsList = document.getElementById('modalSignals');
        if (signalsList) {
            signalsList.innerHTML = '';
            if (stock.analysis.prediction === 'UP') {
                signalsList.innerHTML = '<li class="list-group-item text-danger border-0 ps-0"><i class="fas fa-check-circle me-2"></i> 강력 매수 신호 감지됨</li>';
            } else if (stock.analysis.prediction === 'DOWN') {
                signalsList.innerHTML = '<li class="list-group-item text-info border-0 ps-0"><i class="fas fa-exclamation-triangle me-2"></i> 매도 신호 감지됨</li>';
            } else {
                signalsList.innerHTML = '<li class="list-group-item text-muted border-0 ps-0"><i class="fas fa-minus-circle me-2"></i> 중립 / 보유</li>';
            }
        }

        // Financials Tab
        const finBody = document.getElementById('financial-table-body');
        if (finBody) {
            const f = stock.financials || {};
            finBody.innerHTML = `
                <tr><td class="text-muted">시가총액</td><td class="text-end text-white">${formatNumber(f.market_cap / 100000000)} 억원</td></tr>
                <tr><td class="text-muted">매출액</td><td class="text-end text-white">${f.sales ? formatNumber(f.sales / 100000000) : '-'} 억원</td></tr>
                <tr><td class="text-muted">영업이익</td><td class="text-end text-white">${f.op_profit ? formatNumber(f.op_profit / 100000000) : '-'} 억원</td></tr>
                <tr><td class="text-muted">PER</td><td class="text-end text-white">${formatNumber(f.per)}배</td></tr>
                <tr><td class="text-muted">PBR</td><td class="text-end text-white">${formatNumber(f.pbr)}배</td></tr>
                <tr><td class="text-muted">EPS</td><td class="text-end text-white">${formatNumber(f.eps)}원</td></tr>
            `;
        }

        // News Tab
        const newsListEl = document.getElementById('modalNewsList');
        if (newsListEl) {
            newsListEl.innerHTML = '';
            const newsArr = stock.analysis.news || [];
            if (newsArr.length === 0) {
                newsListEl.innerHTML = '<li class="list-group-item bg-transparent text-muted text-center">최신 뉴스가 없습니다.</li>';
            } else {
                newsArr.forEach(n => {
                    newsListEl.innerHTML += `
                        <li class="list-group-item bg-transparent border-secondary text-white">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="badge ${n.sentiment === 'Positive' ? 'bg-success' : 'bg-secondary'}">${n.sentiment || '뉴스'}</span>
                                <small class="text-muted">${n.date}</small>
                            </div>
                            <a href="${n.link}" target="_blank" class="text-white text-decoration-none fw-bold">${n.title}</a>
                        </li>
                     `;
                });
            }
        }

        // 3. Show Modal (Bootstrap Check)
        if (typeof bootstrap === 'undefined') {
            throw new Error('Bootstrap 라이브러리가 로드되지 않았습니다.');
        }

        const modalEl = document.getElementById('stockModal');
        if (!modalEl) throw new Error('모달 요소(stockModal)를 찾을 수 없습니다.');

        const modal = new bootstrap.Modal(modalEl);
        modal.show();

        // 4. Render Chart after show
        modalEl.addEventListener('shown.bs.modal', () => {
            try {
                renderDetailChart(stock);
            } catch (chartErr) {
                console.error('Char rendering failed:', chartErr);
            }
        }, { once: true });

    } catch (err) {
        console.error('[CRITICAL] Failed to open modal:', err);
        alert(`상세 화면을 여는 중 오류가 발생했습니다.\n(${err.message})`);
    }
};

function renderDetailChart(stock) {
    const canvas = document.getElementById('detailChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (detailChartInstance) {
        detailChartInstance.destroy();
    }

    const ohlcData = stock.chart_data.map(d => ({
        x: new Date(d.date).valueOf(),
        o: d.open,
        h: d.high,
        l: d.low,
        c: d.close
    }));

    if (ohlcData.length === 0) return;

    detailChartInstance = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [{
                label: '주가',
                data: ohlcData,
                color: { up: '#ff4d7d', down: '#4da3ff', unchanged: '#888' },
                borderColor: { up: '#ff4d7d', down: '#4da3ff', unchanged: '#888' }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'timeseries',
                    time: { unit: 'day', displayFormats: { day: 'MM-dd' } },
                    ticks: { source: 'data', color: '#adb5bd' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    ticks: { color: '#adb5bd' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function setupSearch() {
    const input = document.getElementById('stats-search');
    if (!input) return;
    input.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = allStocks.filter(s =>
            s.name.toLowerCase().includes(term) || s.code.toLowerCase().includes(term)
        );
        renderStockList(filtered);
    });
}


// Utils
function getDisplayName(stock) {
    return stock.name;
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

function formatPriceSimple(price) {
    if (!price) return '-';
    return price.toLocaleString() + '원';
}

function formatPrice(price) {
    if (price === null || price === undefined) return '-';
    return price.toLocaleString() + '원';
}

function getMarketBadge(stock) {
    if (stock.market === 'KOSPI') {
        return '<span class="badge ms-1" style="background:rgba(13,110,253,0.25); color:#6ea8fe; border:1px solid rgba(13,110,253,0.4); font-size:0.65em; vertical-align:middle;"><i class="fas fa-chart-line me-1" style="font-size:0.8em;"></i>KOSPI</span>';
    } else if (stock.market === 'KOSDAQ') {
        return '<span class="badge ms-1" style="background:rgba(25,135,84,0.25); color:#75b798; border:1px solid rgba(25,135,84,0.4); font-size:0.65em; vertical-align:middle;"><i class="fas fa-seedling me-1" style="font-size:0.8em;"></i>KOSDAQ</span>';
    }
    return '';
}
