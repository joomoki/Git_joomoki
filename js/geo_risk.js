// ────────────────────────────────────────────────────────
//  전쟁/지정학적 리스크 모델 대시보드 렌더러
//  geoRiskData 전역 변수를 읽어 섹션을 동적으로 렌더링합니다.
// ────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    renderGeoRiskSection();
});

function renderGeoRiskSection() {
    const container = document.getElementById('geo-risk-container');
    if (!container) return;

    // 데이터 없으면 조용히 숨김
    if (typeof geoRiskData === 'undefined') {
        container.closest('section')?.remove();
        return;
    }

    const d = geoRiskData;
    const overall = d.overall_risk || {};
    const level = overall.level || 'NORMAL';
    const active = overall.active || false;
    const riskTypes = overall.risk_types || [];

    // 경보 레벨별 색상/아이콘 설정
    const levelConfig = {
        NORMAL:   { color: '#28a745', bg: 'rgba(40,167,69,0.08)',   border: 'rgba(40,167,69,0.3)',   icon: '✅', label: '정상 (위험 없음)' },
        MODERATE: { color: '#ffc107', bg: 'rgba(255,193,7,0.08)',   border: 'rgba(255,193,7,0.3)',   icon: '⚠️', label: '주의 (지정학 변동)' },
        HIGH:     { color: '#fd7e14', bg: 'rgba(253,126,20,0.10)',  border: 'rgba(253,126,20,0.4)',  icon: '🔶', label: '경계 (리스크 상승)' },
        EXTREME:  { color: '#dc3545', bg: 'rgba(220,53,69,0.12)',   border: 'rgba(220,53,69,0.5)',   icon: '🚨', label: '위험 (극단적 변동)' },
        UNKNOWN:  { color: '#6c757d', bg: 'rgba(108,117,125,0.08)', border: 'rgba(108,117,125,0.3)', icon: '❓', label: '분석 불가' }
    };
    const lc = levelConfig[level] || levelConfig.NORMAL;

    // ── 1. 자산 현황 카드들 ──
    const assets = d.assets || {};
    const assetCardsHtml = Object.entries(assets).map(([key, a]) => {
        if (a.error) {
            return `
            <div class="geo-asset-card" style="opacity:0.5;">
                <div class="asset-header">${a.icon || ''} ${a.name}</div>
                <div class="asset-price text-muted">데이터 없음</div>
            </div>`;
        }
        const alertLvl = a.alert_level || 'NORMAL';
        const ac = levelConfig[alertLvl] || levelConfig.NORMAL;
        const priceStr = a.latest_price != null
            ? a.latest_price.toLocaleString(undefined, { maximumFractionDigits: 2 })
            : '-';
        const retStr = a.latest_return != null
            ? (a.latest_return >= 0 ? '+' : '') + a.latest_return.toFixed(2) + '%'
            : '-';
        const retColor = (a.latest_return || 0) > 0 ? '#ff4d7d' : ((a.latest_return || 0) < 0 ? '#4da3ff' : '#adb5bd');
        const zStr = a.z_score != null ? a.z_score.toFixed(2) : '-';
        const sigStr = a.sigma != null ? a.sigma.toFixed(3) + '%' : '-';

        return `
        <div class="geo-asset-card" style="border-color:${ac.border}; background:${ac.bg};">
            <div class="asset-header">
                <span>${a.icon || ''} ${a.name}</span>
                <span class="geo-level-badge" style="background:${ac.color}20; color:${ac.color}; border:1px solid ${ac.color}40;">
                    ${ac.icon} ${alertLvl}
                </span>
            </div>
            <div class="asset-price">${priceStr}</div>
            <div class="asset-meta">
                <span style="color:${retColor};">${retStr}</span>
                <span class="text-muted" style="font-size:0.7rem;">Z: <strong style="color:${ac.color};">${zStr}</strong> σ기준: ${sigStr}</span>
            </div>
            ${a.alert ? `<div class="asset-alert-bar" style="background:${ac.color};"></div>` : ''}
        </div>`;
    }).join('');

    // ── 2. 수혜 섹터 + 종목 ──
    const sectors = d.beneficiary_sectors || [];
    const sectorsHtml = sectors.map(sec => {
        const stocksHtml = (sec.stocks || []).map(s => {
            const predColor = s.prediction === 'UP' ? '#ff4d7d' : (s.prediction === 'DOWN' ? '#4da3ff' : '#adb5bd');
            const predText  = s.prediction === 'UP' ? '매수' : (s.prediction === 'DOWN' ? '매도' : '보유');
            return `
            <div class="geo-stock-item" onclick="showStockDetail('${s.code}')" style="cursor:pointer;">
                <div>
                    <span class="fw-bold text-white" style="font-size:0.85rem;">${s.name}</span>
                    <span class="text-muted" style="font-size:0.7rem; margin-left:4px;">${s.code}</span>
                </div>
                <div style="display:flex; gap:6px; align-items:center;">
                    <span style="font-size:0.75rem; color:#adb5bd;">AI ${s.ai_score}</span>
                    <span style="font-size:0.72rem; color:${predColor}; border:1px solid ${predColor}40; padding:1px 5px; border-radius:3px;">${predText}</span>
                </div>
            </div>`;
        }).join('');

        return `
        <div class="geo-sector-card">
            <div class="geo-sector-header">
                <span>${sec.icon} <strong>${sec.sector}</strong></span>
                <span class="text-muted" style="font-size:0.72rem;">${sec.reason}</span>
            </div>
            <div class="geo-stock-list">${stocksHtml}</div>
        </div>`;
    }).join('');

    // ── 3. 헤더 배너 ──
    const bannerHtml = `
    <div class="geo-risk-banner" style="
        background: ${lc.bg};
        border: 1px solid ${lc.border};
        border-radius: 12px;
        padding: 16px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 20px;
    ">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.6rem;">${lc.icon}</span>
            <div>
                <div style="color:${lc.color}; font-weight:700; font-size:1rem;">${lc.label}</div>
                <div class="text-muted" style="font-size:0.75rem;">
                    ${active
                        ? `⚡ 경보 자산 ${overall.alert_count}개 감지 — ${riskTypes.join(', ')}`
                        : `감시 자산 ${Object.keys(assets).length}개 모두 정상 범위 내`}
                </div>
            </div>
        </div>
        <div class="text-muted" style="font-size:0.7rem;">
            기준: 최근 ${d.lookback_days || 20}일 σ × ${d.sigma_threshold || 2} | 갱신: ${d.generated_at || '-'}
        </div>
    </div>`;

    container.innerHTML = `
        ${bannerHtml}
        <div class="geo-assets-grid">${assetCardsHtml}</div>
        ${sectors.length > 0 ? `
        <div class="geo-sectors-wrapper">
            <h6 class="text-muted mb-3" style="font-size:0.8rem; letter-spacing:0.05em; text-transform:uppercase;">
                <i class="fas fa-crosshairs me-2"></i>수혜 예상 종목
            </h6>
            <div class="geo-sectors-grid">${sectorsHtml}</div>
        </div>` : ''}
    `;
}
