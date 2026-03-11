// Joomoki Stock History Logic

document.addEventListener('DOMContentLoaded', () => {
    loadHistoryData();
    setupFilters();
});

let allHistory = [];
let displayedHistory = [];
let returnChart = null;
let currentStockFilter = null; // 종목 필터 (이름)

function loadHistoryData() {
    try {
        if (typeof stockHistoryData !== 'undefined') {
            allHistory = stockHistoryData;

            // 날짜 드롭다운 구성 및 기본값 설정
            setupDateFilter();

            // 초기 렌더링은 setupDateFilter 내부에서 호출됨 (기본값 설정 후)
        } else {
            console.error("No history data found.");
        }
    } catch (e) {
        console.error("Error loading history data:", e);
    }
}

function updateDateDropdown() {
    const dateSelect = document.getElementById('date-select');
    if (!dateSelect) return;

    // 국내 데이터만 (is_us === false)
    const krHistory = allHistory.filter(item => !item.is_us);
    const dates = [...new Set(krHistory.map(item => item.date))].sort((a, b) => new Date(b) - new Date(a));

    const currentValue = dateSelect.value;
    dateSelect.innerHTML = '<option value="all">전체 날짜</option>';

    dates.forEach(date => {
        const option = document.createElement('option');
        option.value = date;
        option.textContent = date;
        dateSelect.appendChild(option);
    });

    if (currentValue === 'all') {
        dateSelect.value = 'all';
    } else if (currentValue && dates.includes(currentValue)) {
        dateSelect.value = currentValue;
    } else if (dates.length > 0) {
        let defaultDate = dates[0];
        for (const dateStr of dates) {
            const date = new Date(dateStr);
            if (date.getDay() === 1) {
                defaultDate = dateStr;
                break;
            }
        }
        dateSelect.value = defaultDate;
    } else {
        dateSelect.value = 'all';
    }
}

function setupDateFilter() {
    const dateSelect = document.getElementById('date-select');

    updateDateDropdown();

    if (dateSelect) {
        dateSelect.addEventListener('change', () => {
            currentStockFilter = null;
            filterAndRender();
        });
    }

    filterAndRender();
}

// 상세 차트 모달 (app.js 로직 일부 재사용/변형)
let detailChartInstance = null;

function showStockHistoryDetail(stockCode) {
    // 1. Find Data
    const stock = displayedHistory.find(item => item.code === stockCode);
    if (!stock) return;

    // 2. Populate Data
    document.getElementById('modalStockName').innerHTML = `${stock.name} <span class="badge bg-secondary ms-2">${stock.code}</span>`;

    document.getElementById('modalAnalysisSummary').innerHTML = `
        <strong>추천일:</strong> ${stock.date}<br>
        <strong>AI 점수:</strong> <span class="badge bg-warning text-dark">${stock.score}</span><br>
        <strong>수익률:</strong> <span class="${getReturnColorClass(stock.return_rate)}">${stock.return_rate.toFixed(2)}%</span>
    `;

    const priceEl = document.getElementById('modalPrice');
    if (priceEl) {
        priceEl.textContent = formatPrice(stock.current_price);
    }

    // 기업 개요 표시
    const descEl = document.getElementById('modalDescription');
    if (descEl) {
        descEl.textContent = stock.description || "기업 정보가 없습니다.";
    }

    // Signals
    /* 이력 데이터에 signals가 없다면 생략
    const signalsList = document.getElementById('modalSignals');
    signalsList.innerHTML = '';
    if (stock.signals) {
        stock.signals.forEach(sig => {
           // ...
        });
    } else {
        signalsList.innerHTML = '<li class="list-group-item bg-dark text-muted">신호 데이터 없음</li>';
    }
    */

    // 3. Render Chart
    renderDetailChart(stock);

    // 4. Show Modal
    const modal = new bootstrap.Modal(document.getElementById('stockModal'));
    modal.show();
}

function renderDetailChart(stock) {
    const ctx = document.getElementById('detailChart');
    if (!ctx) return;

    if (detailChartInstance) {
        detailChartInstance.destroy();
    }

    // 데이터 확인
    if (!stock.price_history || stock.price_history.length === 0 || stock.price_history.every(d => d.close === 0)) {
        // 데이터가 없으면 메시지 표시
        ctx.parentNode.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-muted">차트 데이터가 없습니다.</div>';
        console.warn("No price history for chart");
        return;
    }

    // 데이터 가공 (Candlestick)
    // price_history: [{date, open, high, low, close, volume}, ...]

    // 날짜 오름차순 정렬
    const sortedHistory = [...stock.price_history].sort((a, b) => new Date(a.date) - new Date(b.date));

    const ohlcData = sortedHistory.map(d => ({
        x: new Date(d.date).valueOf(), // timestamp
        o: d.open,
        h: d.high,
        l: d.low,
        c: d.close
    }));

    // 이동평균선 계산 (간단히)
    const ma5 = calculateMA(sortedHistory, 5);
    const ma20 = calculateMA(sortedHistory, 20);
    const ma60 = calculateMA(sortedHistory, 60);

    detailChartInstance = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [
                {
                    label: '주가',
                    data: ohlcData,
                    color: {
                        up: '#ff5252', // 상승 (빨강)
                        down: '#007bff', // 하락 (파랑)
                        unchanged: '#999',
                    },
                    borderColor: {
                        up: '#ff5252',
                        down: '#007bff',
                        unchanged: '#999',
                    },
                    borderWidth: 1,
                    order: 1
                },
                {
                    label: 'MA5',
                    data: ma5,
                    type: 'line',
                    borderColor: '#fab1a0', // 연한 빨강
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.1,
                    order: 0
                },
                {
                    label: 'MA20',
                    data: ma20,
                    type: 'line',
                    borderColor: '#ffeaa7', // 노랑
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.1,
                    order: 0
                },
                {
                    label: 'MA60',
                    data: ma60,
                    type: 'line',
                    borderColor: '#74b9ff', // 연한 파랑
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0.1,
                    order: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#adb5bd' }
                },
                tooltip: {
                    position: 'nearest'
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: { day: 'MM/dd' }
                    },
                    grid: { color: '#333' },
                    ticks: { color: '#adb5bd' }
                },
                y: {
                    grid: { color: '#333' },
                    ticks: { color: '#adb5bd' }
                }
            }
        }
    });
}

function calculateMA(data, period) {
    let ma = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            ma.push({ x: new Date(data[i].date).valueOf(), y: null });
            continue;
        }
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        ma.push({ x: new Date(data[i].date).valueOf(), y: sum / period });
    }
    return ma;
}

function setupFilters() {
    // market-filter가 누락된 경우 대비 (HTML에서 date-select만 남김)
    const marketFilter = document.getElementById('market-filter');
    if (marketFilter) {
        marketFilter.addEventListener('change', () => {
            currentStockFilter = null;
            updateDateDropdown();
            filterAndRender();
        });
    }
}

function resetStockFilter() {
    currentStockFilter = null;
    filterAndRender();
}

function filterAndRender() {
    const dateSelect = document.getElementById('date-select');
    const marketFilter = document.getElementById('market-filter');
    const resetBtn = document.getElementById('reset-stock-btn');

    const selectedDate = dateSelect ? dateSelect.value : 'all';
    const selectedMarket = marketFilter ? marketFilter.value : 'all';

    // 국내 데이터만 필터 (is_us === false)
    displayedHistory = allHistory.filter(item => {
        const matchDate = selectedDate === 'all' || item.date === selectedDate;
        const matchKr = !item.is_us; // 해외 제외
        const matchStock = currentStockFilter === null || item.name === currentStockFilter;
        return matchDate && matchKr && matchStock;
    });

    // 초기화 버튼 표시 여부
    if (resetBtn) {
        resetBtn.style.display = currentStockFilter ? 'block' : 'none';

        // 버튼 텍스트에 선택된 종목명 표시 (옵션)
        if (currentStockFilter) {
            resetBtn.innerHTML = `<i class="fas fa-times me-1"></i> ${currentStockFilter} 해제`;
        } else {
            resetBtn.innerHTML = `<i class="fas fa-times me-1"></i> 종목 필터 해제`;
        }
    }

    // 테이블 렌더링
    renderTable(displayedHistory);
    updateSummary(displayedHistory);

    // 차트 렌더링 (특정 날짜 선택 시에만)
    const chartContainer = document.getElementById('chart-container');
    if (selectedDate !== 'all') {
        if (chartContainer) chartContainer.style.display = 'block';
        renderChart(displayedHistory);
    } else {
        if (chartContainer) chartContainer.style.display = 'none';
        if (returnChart) {
            returnChart.destroy();
            returnChart = null;
        }
    }
}

function renderChart(data) {
    const ctx = document.getElementById('return-chart');
    if (!ctx) return;

    if (returnChart) {
        returnChart.destroy();
    }

    // 데이터가 없으면 리턴
    if (data.length === 0) return;

    // 모든 종목의 performance_history 수집
    let allDates = new Set();
    data.forEach(item => {
        if (item.performance_history) {
            item.performance_history.forEach(ph => allDates.add(ph.date));
        }
    });
    const labels = [...allDates].sort();

    // 데이터셋 생성
    const datasets = data.map(item => {
        const phMap = {};
        if (item.performance_history) {
            item.performance_history.forEach(ph => phMap[ph.date] = ph.return);
        }

        // 레이블 날짜에 맞춰 데이터 배열 생성
        const d = labels.map(date => phMap[date] !== undefined ? phMap[date] : null);

        const color = getRandomColor();

        return {
            label: `${item.name} (${item.market})`,
            stockName: item.name, // 필터링을 위한 원본 이름 저장
            data: d,
            backgroundColor: color,
            borderColor: color,
            borderWidth: 1
        };
    });

    returnChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'nearest', // 클릭 시 가장 가까운 요소 선택
                axis: 'x',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#fff' },
                    onClick: function (e, legendItem, legend) {
                        const index = legendItem.datasetIndex;
                        const stockName = legend.chart.data.datasets[index].stockName;

                        // 범례 클릭 시 해당 종목 필터링
                        applyStockFilter(stockName);
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            },
            onClick: (e, elements, chart) => {
                if (elements.length > 0) {
                    // 첫 번째 요소의 데이터셋 인덱스를 가져옴
                    const datasetIndex = elements[0].datasetIndex;
                    const stockName = chart.data.datasets[datasetIndex].stockName;

                    // 종목 필터 적용
                    applyStockFilter(stockName);
                }
            },
            scales: {
                x: {
                    ticks: { color: '#888' },
                    grid: { color: '#333' }
                },
                y: {
                    ticks: { color: '#888', callback: function (value) { return value + '%' } },
                    grid: { color: '#333' }
                }
            }
        }
    });
}

function applyStockFilter(stockName) {
    if (currentStockFilter === stockName) {
        // 이미 선택된 종목이면 해제? (사용자 경험상 명시적 해제 버튼이 나음)
        // 여기선 재클릭 시 해제하지 않고 유지, 해제는 버튼으로
    } else {
        currentStockFilter = stockName;
        filterAndRender();
    }
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function renderTable(data) {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">이력 데이터가 없습니다.</td></tr>';
        return;
    }

    // 정렬 (수익률 내림차순 기본 X, 날짜 내림차순은 이미 필터링 전제)
    // 여기서는 기본 표시 순서를 유지하거나 수익률 순으로

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "cursor-pointer history-row"; // CSS for hover effect
        tr.onclick = () => showStockHistoryDetail(item.code);

        const returnClass = getReturnColorClass(item.return_rate);
        const returnIcon = item.return_rate > 0 ? '<i class="fas fa-caret-up"></i>' : (item.return_rate < 0 ? '<i class="fas fa-caret-down"></i>' : '-');

        tr.innerHTML = `
            <td>${item.date}</td>
            <td>
                <div class="fw-bold text-white">
                    ${item.name} ${getMarketBadge(item)}
                </div>
                <div class="small text-muted">${item.code}</div>
            </td>
            <td>${formatPrice(item.base_price)}</td>
            <td>${formatPrice(item.current_price)}</td>
            <td class="${returnClass} fw-bold">
                ${returnIcon} ${item.return_rate.toFixed(2)}%
            </td>
            <td><span class="badge bg-warning text-dark">${item.score}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateSummary(data) {
    const totalCount = document.getElementById('total-count');
    const avgReturn = document.getElementById('avg-return');
    const winRate = document.getElementById('win-rate');

    if (totalCount) totalCount.textContent = data.length + "건";

    if (data.length > 0) {
        const avg = data.reduce((sum, item) => sum + item.return_rate, 0) / data.length;
        const wins = data.filter(item => item.return_rate > 0).length;
        const winPct = (wins / data.length) * 100;

        if (avgReturn) {
            avgReturn.textContent = avg.toFixed(2) + "%";
            avgReturn.className = "text-white fw-bold mb-0 " + getReturnColorClass(avg); // class overwrite fix
            // But we need to keep h2 style
            avgReturn.setAttribute('class', "text-white fw-bold mb-0 " + getReturnColorClass(avg));
        }
        if (winRate) winRate.textContent = winPct.toFixed(1) + "%";
    } else {
        if (avgReturn) avgReturn.textContent = "-";
        if (winRate) winRate.textContent = "-";
    }
}

function getReturnColorClass(val) {
    if (val > 0) return 'text-danger';
    if (val < 0) return 'text-primary';
    return 'text-white';
}

function formatPrice(price) {
    return price.toLocaleString() + '원';
}

let currentSort = { key: 'date', dir: 'desc' };
function sortHistory(key) {
    if (currentSort.key === key) {
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.key = key;
        currentSort.dir = 'desc';
    }

    if (key === 'return') {
        displayedHistory.sort((a, b) => {
            return currentSort.dir === 'asc' ? a.return_rate - b.return_rate : b.return_rate - a.return_rate;
        });
    }
}

function getMarketBadge(item) {
    if (item.market === 'KOSPI') {
        return '<span class="badge ms-1" style="background:rgba(13,110,253,0.25); color:#6ea8fe; border:1px solid rgba(13,110,253,0.4); font-size:0.75em;"><i class="fas fa-chart-line me-1" style="font-size:0.8em;"></i>KOSPI</span>';
    }
    if (item.market === 'KOSDAQ') {
        return '<span class="badge ms-1" style="background:rgba(25,135,84,0.25); color:#75b798; border:1px solid rgba(25,135,84,0.4); font-size:0.75em;"><i class="fas fa-seedling me-1" style="font-size:0.8em;"></i>KOSDAQ</span>';
    }
    return '<span class="badge ms-1" style="background:rgba(108,117,125,0.25); color:#adb5bd; border:1px solid rgba(108,117,125,0.4); font-size:0.75em;">KR</span>';
}
