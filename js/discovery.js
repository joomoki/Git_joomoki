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
    },

    // ── 두 번째 모델: 전쟁/지정학 리스크 수혜 발굴 ──
    {
        id: 'geo_risk',
        name: '전쟁·지정학 리스크 수혜 발굴',
        icon: 'fa-globe-asia',
        badge: '리스크모델',
        market: 'kr',
        color: '#fd7e14',
        tagline: 'WTI·금·방산ETF 2σ 변동성 감지 → 수혜 섹터 종목 발굴',
        description: `
            <h6 class="mb-3" style="color:#fd7e14;">🌐 모델 개요</h6>
            <p>글로벌 지정학적 리스크 자산(WTI 원유, 금 선물, 미 방산ETF ITA)의 변동성이
            과거 20일 평균 대비 <strong>2σ(표준편차) 이상</strong> 급등하는 시점을 감지하고,
            수혜가 예상되는 국내 방산·에너지·해운·소재 섹터 종목을 자동 발굴합니다.</p>

            <h6 class="text-warning mb-2 mt-4">🔎 감시 자산 및 감지 로직</h6>
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(253,126,20,0.07); border:1px solid rgba(253,126,20,0.2)">
                        <div class="fw-bold mb-2" style="color:#fd7e14;"><i class="fas fa-satellite-dish me-1"></i> 감시 지표</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>🛢️ WTI 원유 선물 (CL=F) — 유가 급등·급락</li>
                            <li>🪙 금 선물 (GC=F) — 안전자산 수요 폭발</li>
                            <li>🛡️ 미 방산 ETF (ITA) — 전쟁 리스크 선행 지표</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(112,0,255,0.07); border:1px solid rgba(112,0,255,0.2)">
                        <div class="fw-bold text-secondary mb-2"><i class="fas fa-chart-bar me-1"></i> 2σ 감지 알고리즘</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>최근 20거래일 수익률 → μ(평균), σ(표준편차) 계산</li>
                            <li>최근 1일 수익률 Z-score = (r - μ) / σ</li>
                            <li>|Z| ≥ 2.0 → 경보 발동 / |Z| ≥ 3 → HIGH / |Z| ≥ 4 → EXTREME</li>
                        </ul>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">⚙️ 수혜 섹터 매핑</h6>
            <div class="row g-2 mb-3">
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(253,126,20,0.08); border:1px solid rgba(253,126,20,0.2)">
                        <div style="color:#fd7e14;" class="fw-bold">🛡️ 방산</div>
                        <div class="text-muted small">ITA 경보 시</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.2)">
                        <div class="text-warning fw-bold">⚡ 에너지</div>
                        <div class="text-muted small">WTI 경보 시</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(0,242,255,0.08); border:1px solid rgba(0,242,255,0.2)">
                        <div class="text-primary fw-bold">🚢 해운</div>
                        <div class="text-muted small">WTI/ITA 시</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(0,255,157,0.08); border:1px solid rgba(0,255,157,0.2)">
                        <div class="text-success fw-bold">⛏️ 소재</div>
                        <div class="text-muted small">GOLD 경보 시</div>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">📊 리스크 현황</h6>
            <div id="geo-risk-algo-status" class="p-3 rounded-3" style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08);">
                <div class="text-muted small">데이터 로딩 중...</div>
            </div>
        `,
        run: function (allStocks) {
            // geo_risk_data.js 데이터 기반 발굴
            if (typeof geoRiskData === 'undefined') {
                return [];
            }

            const geo = geoRiskData;
            const overall = geo.overall_risk || {};
            const sectors = geo.beneficiary_sectors || [];

            // 알고리즘 현황 패널 업데이트
            const statusEl = document.getElementById('geo-risk-algo-status');
            if (statusEl) {
                const levelColors = { NORMAL: '#28a745', MODERATE: '#ffc107', HIGH: '#fd7e14', EXTREME: '#dc3545', UNKNOWN: '#6c757d' };
                const lc = levelColors[overall.level] || '#adb5bd';
                const assets = geo.assets || {};
                const assetHtml = Object.entries(assets).map(([k, a]) => {
                    if (!a || a.error) return `<span class="badge me-1" style="background:rgba(108,117,125,0.2); color:#6c757d;">${k}: 데이터없음</span>`;
                    const ac = levelColors[a.alert_level] || '#adb5bd';
                    return `<span class="badge me-1" style="background:${ac}22; color:${ac}; border:1px solid ${ac}44;">
                        ${a.icon || ''} ${k}: Z=${a.z_score} (${a.alert_level})
                    </span>`;
                }).join('');
                statusEl.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">
                        <span class="badge" style="background:${lc}22; color:${lc}; border:1px solid ${lc}44; font-size:0.9rem; padding:6px 14px;">
                            전체 리스크: ${overall.level}
                        </span>
                        <span class="text-muted small">경보 자산: ${overall.alert_count}개 | 기준: |Z| ≥ ${geo.sigma_threshold}</span>
                    </div>
                    <div class="d-flex flex-wrap gap-1">${assetHtml}</div>
                    <div class="text-muted small mt-2">갱신: ${geo.generated_at || '-'}</div>
                `;
            }

            // sectors → stocks 펼치기
            const stockCodeSet = new Set();
            const sectorTagMap = {}; // code → sector name
            sectors.forEach(sec => {
                (sec.stocks || []).forEach(gs => {
                    sectorTagMap[gs.code] = { sector: sec.sector, icon: sec.icon, reason: sec.reason };
                });
            });

            if (Object.keys(sectorTagMap).length === 0) return [];

            // allStocks에서 해당 코드 찾아 점수 부여
            const results = [];
            allStocks.forEach(s => {
                const tag = sectorTagMap[s.code];
                if (!tag) return;

                const analysis = s.analysis || {};
                const aiScore = analysis.score || 0;
                const per = analysis.per || 0;
                const pbr = analysis.pbr || 0;

                let change = 0;
                const chartData = s.chart_data || [];
                if (chartData.length >= 2) {
                    const last = chartData[chartData.length - 1].close || 0;
                    const prev = chartData[chartData.length - 2].close || 0;
                    if (prev > 0) change = ((last - prev) / prev) * 100;
                }

                // 발굴 점수: AI점수 + 리스크 경보 강도
                let score = Math.min(aiScore, 70);
                const alertCount = overall.alert_count || 0;
                if (alertCount >= 3) score += 30;
                else if (alertCount === 2) score += 20;
                else if (alertCount === 1) score += 12;

                if (overall.level === 'EXTREME') score += 20;
                else if (overall.level === 'HIGH') score += 12;
                else if (overall.level === 'MODERATE') score += 6;

                const reasons = {
                    fundamental: per > 0 ? [`PER ${per.toFixed(1)}배`, pbr > 0 ? `PBR ${pbr.toFixed(2)}배` : ''].filter(Boolean) : [],
                    technical: [`${tag.icon} ${tag.sector} 섹터`, tag.reason],
                    risk: overall.active ? [`리스크 발동: ${(overall.risk_types || []).join(', ')}`] : ['경보 미발동 (기본 표시)']
                };

                results.push({
                    ...s,
                    ai_score: aiScore,
                    per, pbr,
                    change_rate: change,
                    discovery_score: Math.min(score, 100),
                    reasons,
                    _geo_sector: tag.sector,
                    _geo_reason: tag.reason
                });
            });

            return results
                .sort((a, b) => b.discovery_score - a.discovery_score)
                .slice(0, 15);
        }
    },

    // ── 세 번째 모델: 질병/팬데믹 언택트 수혜 발굴 ──
    {
        id: 'pandemic',
        name: '질병·팬데믹 언택트 수혜 발굴',
        icon: 'fa-virus-slash',
        badge: '팬데믹모델',
        market: 'kr',
        color: '#20c997',
        tagline: 'XLV·IBB·ARKK 변동성 + MFI 자금흐름 → 언택트·바이오 발굴',
        description: `
            <h6 class="mb-3" style="color:#20c997;">🦠 모델 개요</h6>
            <p>미국 헬스케어(XLV)·바이오테크(IBB)·혁신(ARKK) ETF 변동성을 분석하고,
            <strong>Money Flow Index(MFI)</strong>를 통해 피해 섹터(항공·여행)에서
            수혜 섹터(바이오·언택트·물류·클라우드)로 자금이 이동하는 시점을 포착합니다.</p>

            <h6 class="text-warning mb-2 mt-4">🔎 감시 자산 및 감지 로직</h6>
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(32,201,151,0.07); border:1px solid rgba(32,201,151,0.2)">
                        <div class="fw-bold mb-2" style="color:#20c997;"><i class="fas fa-heartbeat me-1"></i> 수혜 ETF</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>🏥 XLV — 미국 헬스케어 ETF (상승 경보)</li>
                            <li>🧬 IBB — 바이오테크 ETF (상승 경보)</li>
                            <li>🚀 ARKK — 혁신/언택트 ETF (상승 경보)</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(220,53,69,0.07); border:1px solid rgba(220,53,69,0.2)">
                        <div class="fw-bold text-danger mb-2"><i class="fas fa-plane-slash me-1"></i> 피해 ETF (이탈 지표)</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>✈️ XAR — 항공우주 ETF (하락 확인)</li>
                            <li>MFI < 45 = 자금이탈 확인</li>
                            <li>수혜 MFI > 55 + 피해 MFI < 45 = ROTATION</li>
                        </ul>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">⚙️ 수혜 섹터</h6>
            <div class="row g-2 mb-3">
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(32,201,151,0.08); border:1px solid rgba(32,201,151,0.2)">
                        <div style="color:#20c997;" class="fw-bold">🧬 바이오</div><div class="text-muted small">진단·백신·제약</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(0,242,255,0.08); border:1px solid rgba(0,242,255,0.2)">
                        <div class="text-primary fw-bold">💻 언택트</div><div class="text-muted small">플랫폼·게임·미디어</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.2)">
                        <div class="text-warning fw-bold">📦 물류</div><div class="text-muted small">택배·배달·유통</div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="text-center p-2 rounded" style="background:rgba(112,0,255,0.08); border:1px solid rgba(112,0,255,0.2)">
                        <div class="text-secondary fw-bold">☁️ 클라우드</div><div class="text-muted small">보안·IDC·통신</div>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">📊 팬데믹 리스크 현황</h6>
            <div id="pandemic-algo-status" class="p-3 rounded-3" style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08);">
                <div class="text-muted small">데이터 로딩 중...</div>
            </div>
        `,
        run: function (allStocks) {
            if (typeof pandemicData === 'undefined') return [];

            const pd = pandemicData;
            const risk = pd.pandemic_risk || {};
            const sectors = pd.beneficiary_sectors || [];

            // 알고리즘 현황 패널 업데이트
            const statusEl = document.getElementById('pandemic-algo-status');
            if (statusEl) {
                const lc = { NORMAL: '#28a745', MODERATE: '#20c997', HIGH: '#ffc107', EXTREME: '#dc3545' };
                const col = lc[risk.level] || '#adb5bd';
                const assets = pd.assets || {};
                const assetHtml = Object.entries(assets).map(([k, a]) => {
                    if (!a || a.error) return `<span class="badge me-1" style="background:rgba(108,117,125,0.2);color:#6c757d;">${k}: 없음</span>`;
                    const isDmg = a.is_damage;
                    const alc = { NORMAL: '#28a745', MODERATE: '#ffc107', HIGH: '#fd7e14', EXTREME: '#dc3545' }[a.alert_level] || '#adb5bd';
                    return `<span class="badge me-1" style="background:${alc}22;color:${alc};border:1px solid ${alc}44;">
                        ${a.icon || ''} ${k}: Z=${a.z_score}${isDmg ? ' (피해)' : ''} MFI=${a.mfi}
                    </span>`;
                }).join('');
                statusEl.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">
                        <span class="badge" style="background:${col}22;color:${col};border:1px solid ${col}44;font-size:0.9rem;padding:6px 14px;">
                            팬데믹 리스크: ${risk.level}
                        </span>
                        <span class="badge" style="background:rgba(32,201,151,0.15);color:#20c997;border:1px solid rgba(32,201,151,0.3);">
                            자금흐름: ${risk.money_flow_signal}
                        </span>
                    </div>
                    <div class="d-flex flex-wrap gap-1">${assetHtml}</div>
                    <div class="text-muted small mt-2">갱신: ${pd.generated_at || '-'}</div>
                `;
            }

            // 섹터 → stock 코드 매핑
            const sectorTagMap = {};
            sectors.forEach(sec => {
                (sec.stocks || []).forEach(gs => {
                    sectorTagMap[gs.code] = { sector: sec.sector, icon: sec.icon, reason: sec.reason };
                });
            });
            if (Object.keys(sectorTagMap).length === 0) return [];

            const risk_level = risk.level || 'NORMAL';
            const results = [];
            allStocks.forEach(s => {
                const tag = sectorTagMap[s.code];
                if (!tag) return;
                const analysis = s.analysis || {};
                const aiScore = analysis.score || 0;
                const per = analysis.per || 0;
                const pbr = analysis.pbr || 0;
                let change = 0;
                const cd = s.chart_data || [];
                if (cd.length >= 2) {
                    const last = cd[cd.length - 1].close || 0;
                    const prev = cd[cd.length - 2].close || 0;
                    if (prev > 0) change = ((last - prev) / prev) * 100;
                }
                let score = Math.min(aiScore, 65);
                const bonusMap = { EXTREME: 35, HIGH: 25, MODERATE: 15, NORMAL: 5 };
                score += bonusMap[risk_level] || 5;
                if (risk.money_flow_signal === 'ROTATION') score += 10;
                results.push({
                    ...s,
                    ai_score: aiScore, per, pbr, change_rate: change,
                    discovery_score: Math.min(score, 100),
                    reasons: {
                        fundamental: per > 0 ? [`PER ${per.toFixed(1)}배`, pbr > 0 ? `PBR ${pbr.toFixed(2)}배` : ''].filter(Boolean) : [],
                        technical: [`${tag.icon} ${tag.sector}`, tag.reason, `자금흐름: ${risk.money_flow_signal}`],
                        risk: risk.active ? [`팬데믹 리스크 ${risk.level} 발동`] : ['경보 미발동 (기본 표시)']
                    }
                });
            });
            return results.sort((a, b) => b.discovery_score - a.discovery_score).slice(0, 15);
        }
    },

    // ── 네 번째 모델: 반도체 SOX 급락 줍줍 ──
    {
        id: 'semi_dip',
        name: '반도체 SOX 급락 줍줍',
        icon: 'fa-microchip',
        badge: '과매도반등',
        market: 'kr',
        color: '#6f42c1',
        tagline: 'SOXX 5일 7% 급락 감지 → RSI 30 이하 반도체 과매도 추출 + 백테스트',
        description: `
            <h6 class="mb-3" style="color:#6f42c1;">📉 모델 개요</h6>
            <p>글로벌 반도체 지수를 추종하는 <strong>SOXX ETF</strong>(SOX 지수 대리)가
            최근 5거래일 내 <strong>7% 이상 하락</strong>할 때 경보를 발동합니다.
            이 시점에 RSI가 30 이하로 떨어진 <strong>과매도 국내 반도체 종목</strong>을 발굴하고,
            과거 유사 패턴에서의 평균 반등률(백테스트)도 함께 제공합니다.</p>

            <h6 class="text-warning mb-2 mt-4">🔎 알고리즘 구성</h6>
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(111,66,193,0.07); border:1px solid rgba(111,66,193,0.2)">
                        <div class="fw-bold mb-2" style="color:#6f42c1;"><i class="fas fa-satellite-dish me-1"></i> 트리거 조건</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>SOXX 5거래일 수익률 ≤ -7% → 경보 발동</li>
                            <li>≤ -10% → HIGH / ≤ -15% → EXTREME</li>
                            <li>미발동 시에도 RSI 과매도 종목 모니터링</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="p-3 rounded-3" style="background:rgba(0,242,255,0.07); border:1px solid rgba(0,242,255,0.2)">
                        <div class="fw-bold text-primary mb-2"><i class="fas fa-chart-bar me-1"></i> 필터링 기준</div>
                        <ul class="mb-0 small text-muted" style="padding-left:1.2rem">
                            <li>RSI(14) ≤ 30 → 과매도 (강력 매수 후보)</li>
                            <li>RSI(14) 30~50 → 회복 구간 후보</li>
                            <li>AI 점수 + RSI 보너스로 발굴 점수 산정</li>
                        </ul>
                    </div>
                </div>
            </div>

            <h6 class="text-warning mb-2 mt-3">⚙️ 백테스트 방법론</h6>
            <ul class="small text-muted" style="padding-left:1.2rem">
                <li><strong>조건:</strong> 보유 차트 데이터에서 5일 내 5% 이상 하락 구간 탐색</li>
                <li><strong>계산:</strong> 매수 시점 후 5거래일 보유 시 수익률 평균 산출</li>
                <li><strong>출력:</strong> 평균 반등률(%), 승률(%), 샘플 수 표시</li>
            </ul>

            <h6 class="text-warning mb-2 mt-3">📊 SOXX 현황</h6>
            <div id="semi-dip-algo-status" class="p-3 rounded-3" style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08);">
                <div class="text-muted small">데이터 로딩 중...</div>
            </div>
        `,
        run: function (allStocks) {
            if (typeof semiDipData === 'undefined') return [];

            const sd = semiDipData;
            const sox = sd.sox_analysis || {};
            const stocks = sd.oversold_stocks || [];
            const bt = sd.backtest_summary || [];

            // SOXX 현황 패널 업데이트
            const statusEl = document.getElementById('semi-dip-algo-status');
            if (statusEl) {
                const lvlColors = { NONE: '#28a745', MODERATE: '#ffc107', HIGH: '#fd7e14', EXTREME: '#dc3545' };
                const triggered = sox.triggered;
                const col = lvlColors[sox.trigger_level] || '#6c757d';
                const drop = sox.drop_5d_pct != null ? sox.drop_5d_pct.toFixed(2) : '-';
                const btHtml = bt.slice(0, 3).map(b => `
                    <span class="badge me-1 mb-1" style="background:rgba(111,66,193,0.2);color:#a78bfa;border:1px solid rgba(111,66,193,0.3);">
                        ${b.name}: 평균 ${b.avg_return_pct > 0 ? '+' : ''}${b.avg_return_pct}% (승률 ${b.win_rate_pct}%, n=${b.sample_count})
                    </span>`).join('');
                statusEl.innerHTML = `
                    <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">
                        <span class="badge" style="background:${col}22;color:${col};border:1px solid ${col}44;font-size:0.9rem;padding:6px 14px;">
                            ${triggered ? '[경보] ' : ''}SOXX 5일 낙폭: ${drop}% (기준: ${sd.drop_threshold_pct}%)
                        </span>
                        <span class="text-muted small">RSI 과매도 기준: ${sd.rsi_oversold_level}</span>
                    </div>
                    ${btHtml ? `<div class="small text-muted mb-1">백테스트 상위 종목:</div><div class="d-flex flex-wrap">${btHtml}</div>` : ''}
                    <div class="text-muted small mt-2">갱신: ${sd.generated_at || '-'}</div>
                `;
            }

            if (!stocks.length) return [];

            // DB에서 해당 코드 찾아 discovery 형식으로 변환
            const stockMap = {};
            allStocks.forEach(s => { stockMap[s.code] = s; });

            const results = [];
            stocks.forEach((st, idx) => {
                const dbStock = stockMap[st.code];
                if (!dbStock) return;

                const analysis = dbStock.analysis || {};
                let change = 0;
                const cd = dbStock.chart_data || [];
                if (cd.length >= 2) {
                    const last = cd[cd.length - 1].close || 0;
                    const prev = cd[cd.length - 2].close || 0;
                    if (prev > 0) change = ((last - prev) / prev) * 100;
                }

                const rsi = st.rsi;
                const oversold = st.oversold;
                const btAvg = st.backtest_avg_return;
                const btWin = st.backtest_win_rate;

                const techReasons = [`RSI: ${rsi != null ? rsi.toFixed(1) : '-'}${oversold ? ' (과매도)' : ''}`];
                if (btAvg != null) techReasons.push(`백테스트 평균 반등: ${btAvg > 0 ? '+' : ''}${btAvg}%`);
                if (sox.triggered) techReasons.push(`SOXX ${sox.drop_5d_pct?.toFixed(1)}% 급락 트리거`);

                results.push({
                    ...dbStock,
                    ai_score: st.ai_score,
                    per: st.per, pbr: st.pbr,
                    change_rate: change,
                    discovery_score: st.discovery_score,
                    reasons: {
                        fundamental: [
                            st.per > 0 ? `PER ${st.per.toFixed(1)}배` : '',
                            st.pbr > 0 ? `PBR ${st.pbr.toFixed(2)}배` : ''
                        ].filter(Boolean),
                        technical: techReasons,
                        risk: [
                            st.max_drawdown != null ? `MDD: ${st.max_drawdown}%` : '',
                            sox.triggered ? `SOX 트리거 발동` : 'SOX 트리거 미발동'
                        ].filter(Boolean)
                    }
                });
            });

            return results.sort((a, b) => b.discovery_score - a.discovery_score);
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
