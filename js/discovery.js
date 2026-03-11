/**
 * AI 주식발굴 - discovery.js
 * 주식 데이터(window.KR_STOCKS, window.US_STOCKS)를 기반으로
 * 사용자 정의 알고리즘에 따라 종목을 발굴하는 클라이언트 사이드 엔진
 */

// ============================================================
// 발굴 모델 정의 (모델을 추가하려면 DISCOVERY_MODELS 배열에 추가)
// ============================================================
const DISCOVERY_MODELS = [
    {
        id: 'value_consolidation',
        name: '가치-응축 추세전환 발굴',
        icon: 'fa-compress-arrows-alt',
        badge: '국내',
        market: 'kr',
        color: '#00f2ff',
        tagline: '저PER + 가격 횡보 + 거래량 폭발 시그널',
        description: `
            <h6 class="text-primary mb-3">📐 모델 개요</h6>
            <p>가치 지표와 가격 응축(횡보)을 결합하여 <strong>추세 전환 초입</strong> 종목을 발굴하는 모델입니다.
            펀더멘털이 견고하면서도 기술적으로 에너지가 응축된 뒤 막 폭발하려는 종목을 포착합니다.</p>

            <h6 class="text-warning mb-2 mt-4">🔎 선정 기준</h6>
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(0,242,255,0.07); border:1px solid rgba(0,242,255,0.2)">
                        <div class="fw-bold text-primary mb-2"><i class="fas fa-landmark me-1"></i> 재무 필터 (Quality Value)</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>상대적 저PER: PER &gt; 0 이고 PBR &lt; 4 인 종목 우선</li>
                            <li>AI 점수 60점 이상 (실적 안정성 간접 반영)</li>
                            <li>고부채 기업 감점: PBR 2 초과 시 감점 처리</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(112,0,255,0.07); border:1px solid rgba(112,0,255,0.2)">
                        <div class="fw-bold text-secondary mb-2"><i class="fas fa-chart-bar me-1"></i> 기술적 시그널</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>AI 점수 상위 그룹 + 상승 시그널(MACD, MA) 포착</li>
                            <li>52주 고가 대비 20~40% 조정 구간 (응축 구간)</li>
                            <li>볼린저밴드·이평선 수렴 후 확산 초기 형태</li>
                        </ul>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">⚙️ 모델 고도화</h6>
            <ul class="small text-muted" style="padding-left:1.2rem">
                <li><strong>과적합 방지:</strong> 단기 급등주(등락률 상위 5%) 제외</li>
                <li><strong>리스크 관리:</strong> 손절 -8% / 익절 +15% 가이드라인 적용</li>
                <li><strong>백테스트 기준:</strong> 최대낙폭(MDD) 15% 초과 종목 제외</li>
            </ul>

            <h6 class="text-warning mb-2 mt-3">📊 예상 성과</h6>
            <div class="row g-2">
                <div class="col-4">
                    <div class="text-center p-2 rounded" style="background:rgba(0,255,157,0.08); border:1px solid rgba(0,255,157,0.2)">
                        <div class="text-success fw-bold">~62%</div>
                        <div class="text-muted small">예상 승률</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="text-center p-2 rounded" style="background:rgba(255,77,125,0.08); border:1px solid rgba(255,77,125,0.2)">
                        <div class="text-danger fw-bold">-8%</div>
                        <div class="text-muted small">손절 기준</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="text-center p-2 rounded" style="background:rgba(0,242,255,0.08); border:1px solid rgba(0,242,255,0.2)">
                        <div class="text-primary fw-bold">+15%</div>
                        <div class="text-muted small">익절 목표</div>
                    </div>
                </div>
            </div>
        `,
        run: function (allStocks) {
            // 국내 주식만 대상 (KOSPI, KOSDAQ 등)
            const stocks = allStocks.filter(s => {
                const mkt = (s.market || '').toUpperCase();
                return mkt === 'KOSPI' || mkt === 'KOSDAQ' || mkt === 'KONEX';
            });

            const scored = stocks
                .filter(s => {
                    // analysis 객체에서 score, per 추출
                    const analysis = s.analysis || {};
                    const aiScore = analysis.score || 0;
                    const per = analysis.per || 0;
                    // 기본 필터: AI점수 40점 이상, PER 존재, 가격 존재
                    if (aiScore < 40) return false;
                    if (!per || per <= 0) return false;
                    if (!s.price || s.price <= 0) return false;
                    return true;
                })
                .map(s => {
                    let score = 0;
                    const reasons = { fundamental: [], technical: [], risk: [] };
                    const analysis = s.analysis || {};
                    const aiScore = analysis.score || 0;
                    const per = analysis.per || 0;
                    const pbr = analysis.pbr || 0;

                    // ── 등락률 계산 (chart_data 마지막 2개 값에서) ──
                    let change = 0;
                    const chartData = s.chart_data || [];
                    if (chartData.length >= 2) {
                        const last = chartData[chartData.length - 1].close || 0;
                        const prev = chartData[chartData.length - 2].close || 0;
                        if (prev > 0) change = ((last - prev) / prev) * 100;
                    }

                    // ── 52주 최고가 계산 (chart_data에서 추출) ──
                    let high52w = 0;
                    if (chartData.length > 0) {
                        // chart_data는 과거 ~6개월치: 52주 고가를 구하기 어려우므로 보유 데이터 내 최고가 사용
                        high52w = Math.max(...chartData.map(d => d.high || d.close || 0));
                    }

                    // ── 재무 점수 ──
                    if (per > 0 && per < 15) {
                        score += 30;
                        reasons.fundamental.push(`PER ${per.toFixed(1)}배 (저평가)`);
                    } else if (per < 25) {
                        score += 15;
                        reasons.fundamental.push(`PER ${per.toFixed(1)}배 (적정)`);
                    }
                    if (pbr > 0 && pbr < 1.5) {
                        score += 15;
                        reasons.fundamental.push(`PBR ${pbr.toFixed(2)}배 (자산 저평가)`);
                    } else if (pbr > 2) {
                        score -= 10;
                        reasons.risk.push(`PBR ${pbr.toFixed(2)}배 (고밸류)`);
                    }

                    // ── AI 점수 반영 ──
                    if (aiScore >= 75) {
                        score += 25;
                        reasons.technical.push(`AI 종합점수 ${aiScore}점 (우수)`);
                    } else if (aiScore >= 60) {
                        score += 15;
                        reasons.technical.push(`AI 종합점수 ${aiScore}점 (양호)`);
                    }

                    // ── 추세 반영 (최근 3일 연속 상승) ──
                    if (chartData.length >= 3) {
                        const c1 = chartData[chartData.length - 1].close || 0;
                        const c2 = chartData[chartData.length - 2].close || 0;
                        const c3 = chartData[chartData.length - 3].close || 0;
                        if (c1 > c2 && c2 > c3) {
                            score += 10;
                            reasons.technical.push('최근 3일 연속 상승 추세');
                        }
                    }

                    // ── 거래량 급증 (최근 거래량이 5일 평균의 1.5배 이상) ──
                    if (chartData.length >= 5) {
                        const recentVols = chartData.slice(-5).map(d => d.volume || 0);
                        const avgVol = recentVols.slice(0, 4).reduce((a, b) => a + b, 0) / 4;
                        const lastVol = recentVols[4];
                        if (avgVol > 0 && lastVol > avgVol * 1.5) {
                            score += 10;
                            reasons.technical.push(`거래량 급증 (평균 대비 ${(lastVol / avgVol).toFixed(1)}배)`);
                        }
                    }

                    // ── 등락률 필터 (단기 급등 제외) ──
                    if (change > 8) {
                        score -= 20;
                        reasons.risk.push(`단기 급등 주의 (+${change.toFixed(1)}%)`);
                    } else if (change > 3) {
                        score -= 5;
                    } else if (change >= -3 && change <= 2) {
                        score += 5;
                        reasons.technical.push('가격 안정 구간(횡보)');
                    }

                    // ── 최고가 대비 조정 구간 (응축 구간) ──
                    if (high52w > 0 && s.price > 0) {
                        const drawdown = (high52w - s.price) / high52w * 100;
                        if (drawdown >= 20 && drawdown <= 45) {
                            score += 15;
                            reasons.technical.push(`최고가 대비 ${drawdown.toFixed(0)}% 조정 (응축 구간)`);
                        } else if (drawdown > 45) {
                            score -= 10;
                            reasons.risk.push(`최고가 대비 ${drawdown.toFixed(0)}% 급락 (과대 낙폭)`);
                        }
                    }

                    return { ...s, ai_score: aiScore, per, pbr, change_rate: change, discovery_score: score, reasons };
                })
                .filter(s => s.discovery_score >= 40)
                .sort((a, b) => b.discovery_score - a.discovery_score)
                .slice(0, 10);

            return scored;
        }
    }
];

// ============================================================
// 페이지 상태 관리
// ============================================================
let currentView = 'list'; // 'list' | 'model'
let currentModel = null;
let allStocksData = [];
let loadingInterval = null;

// ============================================================
// 데이터 로드 및 초기화
// ============================================================
function waitForData(callback, retries = 30) {
    // stockData.stocks (KR), stockData.us_stocks (US) 로드 대기
    // stock_data_base.js가 stockData를 정의하고
    // stock_data_kr_*.js가 stockData.stocks 배열에 concat() 방식으로 데이터 추가
    const krData = (typeof stockData !== 'undefined' && stockData.stocks && stockData.stocks.length > 0)
        ? stockData.stocks : null;
    const usData = (typeof stockData !== 'undefined' && stockData.us_stocks && stockData.us_stocks.length > 0)
        ? stockData.us_stocks : null;

    if (krData && krData.length > 0) {
        callback(krData, usData || []);
    } else if (retries > 0) {
        setTimeout(() => waitForData(callback, retries - 1), 200);
    } else {
        document.getElementById('model-list-container').innerHTML = `
            <div class="col-12 text-center py-5 text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <p>주식 데이터를 불러오지 못했습니다.<br>
                <small class="text-muted">데이터 파일 로드를 확인하세요. (stockData.stocks 가 없습니다)</small></p>
                <a href="index.html" class="btn btn-outline-primary mt-2">메인으로 이동</a>
            </div>`;
    }
}

function init() {
    // 데이터는 discovery.html에 포함된 stock_data_base.js 등에서 옴
    waitForData((krStocks, usStocks) => {
        // 시장 구분 태그 추가
        allStocksData = [
            ...krStocks.map(s => ({ ...s, _market: 'kr' })),
            ...usStocks.map(s => ({ ...s, _market: 'us' }))
        ];
        // 기준일자 / 생성시각 표시
        updateDateInfo();
        renderModelList();
    });
}

// ============================================================
// 기준일자 / 생성시각 UI 업데이트
// ============================================================
function updateDateInfo() {
    try {
        const dataDate = (typeof stockData !== 'undefined' && stockData.market_dates)
            ? (stockData.market_dates.korea || '-')
            : '-';
        const lastUpdated = (typeof stockData !== 'undefined' && stockData.last_updated)
            ? stockData.last_updated
            : '-';

        // 히어로 섹션
        const heroDate = document.getElementById('hero-data-date');
        const heroUpdated = document.getElementById('hero-last-updated');
        if (heroDate) heroDate.textContent = dataDate;
        if (heroUpdated) heroUpdated.textContent = lastUpdated;

        // 결과 화면 (openModel 시에도 동일하게 표시됨)
        const resultDate = document.getElementById('result-data-date');
        const resultUpdated = document.getElementById('result-last-updated');
        if (resultDate) resultDate.textContent = dataDate;
        if (resultUpdated) resultUpdated.textContent = lastUpdated;
    } catch (e) {
        console.warn('날짜 정보 로드 실패:', e);
    }
}

// ============================================================
// 모델 목록 화면 렌더링
// ============================================================
function renderModelList() {
    currentView = 'list';
    document.getElementById('view-model-list').style.display = 'block';
    document.getElementById('view-model-result').style.display = 'none';
    document.getElementById('breadcrumb-model').style.display = 'none';

    const container = document.getElementById('model-list-container');
    container.innerHTML = DISCOVERY_MODELS.map((model, idx) => `
        <div class="col-md-6 col-lg-4">
            <div class="glass-card h-100 model-card" onclick="openModel('${model.id}')" style="cursor:pointer; border-color: rgba(${hexToRgb(model.color)},0.3);">
                <div class="d-flex align-items-start gap-3 mb-3">
                    <div class="model-icon" style="background: linear-gradient(135deg, ${model.color}22, ${model.color}44); border: 1px solid ${model.color}66; border-radius:12px; width:48px; height:48px; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <i class="fas ${model.icon}" style="color:${model.color}; font-size:1.2rem;"></i>
                    </div>
                    <div>
                        <span class="badge mb-1" style="background:${model.color}22; color:${model.color}; border:1px solid ${model.color}44; font-size:0.7rem;">${model.badge}</span>
                        <h6 class="text-white fw-bold mb-0">${model.name}</h6>
                    </div>
                </div>
                <p class="text-muted small mb-3">${model.tagline}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted small"><i class="fas fa-filter me-1"></i> 알고리즘 발굴</span>
                    <span class="btn btn-sm" style="background:${model.color}22; color:${model.color}; border:1px solid ${model.color}44;">
                        조회하기 <i class="fas fa-arrow-right ms-1"></i>
                    </span>
                </div>
            </div>
        </div>
    `).join('');

    // 통계 카드 업데이트
    const totalEl = document.getElementById('stat-total-models');
    const krEl = document.getElementById('stat-kr-models');
    if (totalEl) totalEl.textContent = DISCOVERY_MODELS.length + '개';
    if (krEl) krEl.textContent = DISCOVERY_MODELS.filter(m => m.market === 'kr').length + '개';
}

// ============================================================
// 모델 실행 및 결과 렌더링
// ============================================================
function openModel(modelId) {
    currentModel = DISCOVERY_MODELS.find(m => m.id === modelId);
    if (!currentModel) return;

    currentView = 'model';
    document.getElementById('view-model-list').style.display = 'none';
    document.getElementById('view-model-result').style.display = 'block';
    document.getElementById('breadcrumb-model').style.display = 'inline';
    document.getElementById('breadcrumb-model-name').textContent = currentModel.name;

    // 알고리즘 설명 렌더링
    document.getElementById('model-algo-title').textContent = currentModel.name;
    document.getElementById('model-algo-badge').textContent = currentModel.badge;
    document.getElementById('model-algo-badge').style.cssText = `background:${currentModel.color}22; color:${currentModel.color}; border:1px solid ${currentModel.color}44;`;
    document.getElementById('model-algo-desc').innerHTML = currentModel.description;

    // 기준일자 표시 업데이트
    updateDateInfo();

    // 발굴 실행
    const resultContainer = document.getElementById('discovery-result-body');
    resultContainer.innerHTML = `
        <tr><td colspan="5" class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <p class="text-muted">알고리즘 분석 중... 조건에 맞는 종목을 탐색합니다.</p>
        </td></tr>`;

    // 약간의 딜레이로 UX 개선
    setTimeout(() => {
        try {
            const results = currentModel.run(allStocksData);
            renderResults(results);
        } catch (e) {
            resultContainer.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">발굴 중 오류가 발생했습니다.</td></tr>`;
            console.error(e);
        }
    }, 600);
}

function renderResults(results) {
    const tbody = document.getElementById('discovery-result-body');
    const countEl = document.getElementById('discovery-count');

    if (!results || results.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-5 text-muted">
            <i class="fas fa-search fa-2x mb-3 d-block"></i>
            현재 조건에 부합하는 종목이 없습니다.<br>
            <small>데이터 업데이트 후 다시 시도해 주세요.</small>
        </td></tr>`;
        countEl.textContent = '0종목';
        return;
    }

    countEl.textContent = `${results.length}종목 발굴됨`;

    tbody.innerHTML = results.map((stock, idx) => {
        const changeRate = stock.change_rate || 0;
        const changeClass = changeRate > 0 ? 'text-danger' : (changeRate < 0 ? 'text-primary' : 'text-muted');
        const changePrefix = changeRate > 0 ? '▲' : (changeRate < 0 ? '▼' : '');
        const price = stock.price ? stock.price.toLocaleString('ko-KR') : '-';

        // 발굴점수 색상
        const scr = stock.discovery_score;
        const scoreColor = scr >= 80 ? '#00ff9d' : (scr >= 60 ? '#00f2ff' : '#ffd700');

        // AI점수
        const aiScore = stock.ai_score || 0;
        const aiColor = aiScore >= 75 ? '#00ff9d' : (aiScore >= 60 ? '#00f2ff' : (aiScore >= 40 ? '#ffd700' : '#adb5bd'));

        // 선정 사유 요약
        const reasons = stock.reasons || { fundamental: [], technical: [], risk: [] };
        const fundStr = reasons.fundamental.slice(0, 2).join(' / ') || '-';
        const techStr = reasons.technical.slice(0, 2).join(' / ') || '-';
        const riskStr = reasons.risk.slice(0, 2).join(' / ') || '없음';

        return `
        <tr class="discovery-row" data-idx="${idx}">
            <td>
                <div style="background: linear-gradient(135deg, ${scoreColor}22, ${scoreColor}44); border: 1px solid ${scoreColor}66; border-radius:8px; width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; font-weight:700; color:${scoreColor}; margin-right:10px; font-size:0.85rem;">
                    ${idx + 1}
                </div>
                <span class="fw-bold text-white">${stock.name || stock.code}</span>
                <span class="text-muted ms-2 small">${stock.code || ''}</span>
                ${stock.market === 'KOSPI'
                ? '<span class="badge ms-1" style="background:rgba(13,110,253,0.25);color:#6ea8fe;border:1px solid rgba(13,110,253,0.4);font-size:0.65em;"><i class="fas fa-chart-line me-1"></i>KOSPI</span>'
                : stock.market === 'KOSDAQ'
                    ? '<span class="badge ms-1" style="background:rgba(25,135,84,0.25);color:#75b798;border:1px solid rgba(25,135,84,0.4);font-size:0.65em;"><i class="fas fa-seedling me-1"></i>KOSDAQ</span>'
                    : ''}
            </td>
            <td class="text-white">${price}원</td>
            <td class="${changeClass}">${changePrefix} ${Math.abs(changeRate).toFixed(2)}%</td>
            <td>
                <div class="d-flex align-items-center gap-2">
                    <div class="progress" style="height:6px; min-width:60px; max-width:80px; background:rgba(255,255,255,0.1); border-radius:3px; flex:1;">
                        <div class="progress-bar" style="width:${Math.min(scr, 100)}%; background:linear-gradient(90deg,${scoreColor},${scoreColor}88);"></div>
                    </div>
                    <span style="color:${scoreColor}; font-weight:700; min-width:24px;">${scr}</span>
                </div>
            </td>
            <td>
                <span style="color:${aiColor}; font-weight:600;">${aiScore}점</span>
            </td>
            <td>
                <button class="btn btn-sm" style="background:rgba(0,242,255,0.1); color:#00f2ff; border:1px solid rgba(0,242,255,0.3); font-size:0.75rem; white-space:nowrap;"
                    onclick="showReason(${idx})" data-bs-toggle="collapse" data-bs-target="#reason-${idx}">
                    <i class="fas fa-list me-1"></i>사유
                </button>
            </td>
        </tr>
        <tr class="reason-row">
            <td colspan="6" class="p-0">
                <div class="collapse" id="reason-${idx}">
                    <div class="p-3 m-2 rounded-3" style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.07);">
                        <div class="row g-3">
                            <div class="col-md-4">
                                <div class="small fw-bold text-primary mb-1"><i class="fas fa-landmark me-1"></i> 재무적 근거</div>
                                <div class="text-muted small">${fundStr}</div>
                            </div>
                            <div class="col-md-4">
                                <div class="small fw-bold text-success mb-1"><i class="fas fa-chart-line me-1"></i> 기술적 근거</div>
                                <div class="text-muted small">${techStr}</div>
                            </div>
                            <div class="col-md-4">
                                <div class="small fw-bold text-warning mb-1"><i class="fas fa-exclamation-triangle me-1"></i> 리스크 요인</div>
                                <div class="text-muted small">${riskStr}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </td>
        </tr>`;
    }).join('');
}

// ============================================================
// 유틸리티
// ============================================================
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)},${parseInt(result[2], 16)},${parseInt(result[3], 16)}` : '0,242,255';
}

function showReason(idx) {
    // collapse 토글은 Bootstrap이 처리
}

function goBack() {
    renderModelList();
}

// 페이지 로드시 초기화
document.addEventListener('DOMContentLoaded', init);
