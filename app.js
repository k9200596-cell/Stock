// ===== 내 포트폴리오 설정 =====
// avg는 달러 기준 평균매입가입니다. 0이면 매수가 대비 손익은 '-'로 표시됩니다.
// 종목/수량은 필요할 때 여기만 수정하면 됩니다.
const portfolio = [
  { ticker: "IREN", name: "IREN", shares: 610, avg: 0 },
  { ticker: "RKLB", name: "Rocket Lab", shares: 128, avg: 0 },
  { ticker: "INFQ", name: "Infleqtion", shares: 192, avg: 0 },
  { ticker: "MEMY", name: "Roundhill Memory ETF", shares: 66, avg: 0 }
];

const $ = id => document.getElementById(id);
const money = n => n == null ? "-" :
  new Intl.NumberFormat("ko-KR", {style:"currency",currency:"USD",maximumFractionDigits:2}).format(n);
const pct = n => n == null ? "-" : `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;

async function quote(p) {
  // 개인용 프로토타입: Yahoo Finance chart endpoint
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(p.ticker)}?range=1y&interval=1d`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const j = await r.json();
  const x = j.chart?.result?.[0];
  if (!x) throw new Error(`${p.ticker} 데이터 없음`);

  const m = x.meta;
  const closes = (x.indicators?.quote?.[0]?.close || []).filter(Number.isFinite);
  const price = m.regularMarketPrice ?? closes.at(-1);
  const prev = m.chartPreviousClose ?? m.previousClose;
  const high52 = Math.max(...closes);
  const day = prev ? (price / prev - 1) * 100 : null;
  const fromHigh = high52 ? (price / high52 - 1) * 100 : null;
  const gain = p.avg ? (price / p.avg - 1) * 100 : null;

  return {
    ...p, price, day, high52, fromHigh, gain,
    value: price * p.shares,
    cost: p.avg ? p.avg * p.shares : null
  };
}

function cls(n) { return n > 0 ? "up" : n < 0 ? "down" : "flat"; }
function trend(n) {
  if (n == null) return "데이터 없음";
  return n > .35 ? "▲ 상승" : n < -.35 ? "▼ 하락" : "→ 보합";
}

function card(x) {
  return `<article class="card">
    <div class="top">
      <div>
        <div class="ticker">${x.ticker}</div>
        <div class="name">${x.name} · ${x.shares}주</div>
      </div>
      <div>
        <div class="price">${money(x.price)}</div>
        <div class="change ${cls(x.day)}">${trend(x.day)} · ${pct(x.day)}</div>
      </div>
    </div>
    <div class="metrics">
      <div class="metric"><span class="label">매수가 대비</span><b class="${cls(x.gain ?? 0)}">${pct(x.gain)}</b></div>
      <div class="metric"><span class="label">52주 고점 대비</span><b class="${cls(x.fromHigh)}">${pct(x.fromHigh)}</b></div>
      <div class="metric"><span class="label">평가액</span><b>${money(x.value)}</b></div>
    </div>
    <div class="bar"><i style="width:${Math.max(2, Math.min(100, 100 + (x.fromHigh ?? -100)))}%"></i></div>
  </article>`;
}

async function load() {
  $("stocks").innerHTML = '<article class="card">시세를 불러오는 중입니다…</article>';
  try {
    const results = await Promise.allSettled(portfolio.map(quote));
    const xs = results.filter(r => r.status === "fulfilled").map(r => r.value);
    const failed = results.filter(r => r.status === "rejected");

    if (!xs.length) throw new Error("모든 시세 조회 실패");
    $("stocks").innerHTML = xs.map(card).join("") +
      (failed.length ? `<article class="card error">${failed.length}개 종목의 시세를 불러오지 못했습니다.</article>` : "");

    const value = xs.reduce((a,x) => a + x.value, 0);
    const allCostKnown = xs.length === portfolio.length && xs.every(x => x.cost != null);
    const cost = allCostKnown ? xs.reduce((a,x) => a + x.cost, 0) : null;
    const pnl = cost == null ? null : value - cost;
    const ret = cost ? 100 * pnl / cost : null;

    $("value").textContent = money(value);
    $("pnl").textContent = money(pnl);
    $("return").textContent = pct(ret);
    $("pnl").className = cls(pnl ?? 0);
    $("return").className = cls(ret ?? 0);
    $("updated").textContent = "업데이트 " + new Date().toLocaleString("ko-KR");
  } catch (e) {
    $("stocks").innerHTML =
      '<article class="card error">시세 API 호출이 브라우저에서 차단되었거나 종목 코드가 변경됐을 수 있습니다. 안정적인 운영은 금융 데이터 API와 서버리스 프록시 연결을 권장합니다.</article>';
    $("updated").textContent = "시세 조회 실패";
  }
}
$("refresh").onclick = load;
load();
