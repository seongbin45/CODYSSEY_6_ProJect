const state = {
  screen: "home",
  step: 0,
  answers: {},
  multiPicked: [],
  messages: [],
  detailId: null,
  filter: "all",
  fontIdx: 0,
  liveItems: [],
};

const els = {
  views: {
    home: document.getElementById("view-home"),
    chat: document.getElementById("view-chat"),
    result: document.getElementById("view-result"),
    detail: document.getElementById("view-detail"),
    guide: document.getElementById("view-guide"),
  },
  fontBtn: document.getElementById("font-btn"),
  logoBtn: document.getElementById("logo-btn"),
  guideBtn: document.getElementById("guide-btn"),
  startBtn: document.getElementById("start-btn"),
  guideStartBtn: document.getElementById("guide-start-btn"),
  backBtn: document.getElementById("back-btn"),
  progressBar: document.getElementById("progress-bar"),
  progressLabel: document.getElementById("progress-label"),
  chatLog: document.getElementById("chat-log"),
  choiceList: document.getElementById("choice-list"),
  multiBtn: document.getElementById("multi-btn"),
  segmentGrid: document.getElementById("segment-grid"),
  profileLine: document.getElementById("profile-line"),
  resultHeadline: document.getElementById("result-headline"),
  resultFilter: document.getElementById("result-filter"),
  resultList: document.getElementById("result-list"),
  resultEmpty: document.getElementById("result-empty"),
  liveStatus: document.getElementById("live-status"),
  restartBtn: document.getElementById("restart-btn"),
  resultGuideBtn: document.getElementById("result-guide-btn"),
  backResultBtn: document.getElementById("back-result-btn"),
  detailBanner: document.getElementById("detail-banner"),
  detailMeta: document.getElementById("detail-meta"),
  detailTitle: document.getElementById("detail-title"),
  detailSummary: document.getElementById("detail-summary"),
  detailChecks: document.getElementById("detail-checks"),
  detailDocs: document.getElementById("detail-docs"),
  detailDeadline: document.getElementById("detail-deadline"),
  detailLink: document.getElementById("detail-link"),
};

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function applyFont() {
  const font = FONTS[state.fontIdx];
  document.documentElement.style.fontSize = font.px + "px";
  els.fontBtn.textContent = "가 " + font.label;
  els.fontBtn.setAttribute("aria-label", "글씨 크기: " + font.label + ". 누르면 다음 크기로 바뀝니다.");
  try { localStorage.setItem("doenayo-font", font.label); } catch (_) { /* ignore */ }
}

function showScreen(name) {
  state.screen = name;
  Object.entries(els.views).forEach(([key, node]) => {
    if (node) node.hidden = key !== name;
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function botMsg(q) {
  return { role: "bot", text: q.q, hint: q.hint || "" };
}

function startChat() {
  state.step = 0;
  state.answers = {};
  state.multiPicked = [];
  state.messages = [botMsg(QUESTIONS[0])];
  state.detailId = null;
  state.filter = "all";
  state.liveItems = [];
  renderChat();
  showScreen("chat");
}

function goHome() { showScreen("home"); }
function goGuide() { showScreen("guide"); }

function goBackStep() {
  if (state.step === 0) {
    goHome();
    return;
  }
  const prev = QUESTIONS[state.step - 1];
  delete state.answers[prev.id];
  state.step -= 1;
  state.multiPicked = [];
  state.messages = state.messages.slice(0, Math.max(0, state.messages.length - 2));
  renderChat();
}

function answer(q, label, value) {
  state.answers[q.id] = value;
  state.messages.push({ role: "user", text: label });
  const next = state.step + 1;
  if (next >= QUESTIONS.length) {
    state.step = next;
    state.multiPicked = [];
    finishToResult();
    return;
  }
  state.step = next;
  state.multiPicked = [];
  state.messages.push(botMsg(QUESTIONS[next]));
  renderChat();
}

function toggleMulti(v) {
  if (state.multiPicked.includes(v)) {
    state.multiPicked = state.multiPicked.filter((x) => x !== v);
  } else {
    state.multiPicked = state.multiPicked.concat(v);
  }
}

function confirmMulti() {
  const q = QUESTIONS[state.step];
  const labels = q.options
    .filter((o) => state.multiPicked.includes(o.v))
    .map((o) => o.l);
  answer(q, labels.length ? labels.join(", ") : "특별히 없음", state.multiPicked.slice());
}

function ageOk(p, age) {
  return !p.age || (age >= p.age[0] && age <= p.age[1]);
}

function evaluate(p, answers) {
  const a = answers;
  const checks = [];
  let worst = "yes";
  const push = (m, text) => {
    checks.push({ match: m, text });
    if (m === "no") worst = "no";
    else if (m === "unknown" && worst !== "no") worst = "unknown";
  };

  if (p.age) {
    const ok = ageOk(p, a.age);
    push(ok ? "yes" : "no", `연령 ${p.age[0]}세~${p.age[1] >= 99 ? "제한 없음" : p.age[1] + "세"} · 고른 답 ${a.age}세 전후`);
  }
  if (p.regions) {
    const ok = p.regions.includes(a.region);
    push(ok ? "yes" : "no", `${p.regions.join("·")} 거주 · 고른 답 ${a.region}`);
  } else {
    push("yes", "전국 사업 · 거주지 제한 없음");
  }
  if (p.incomeMax) {
    const label = p.incomeMax >= 999 ? "소득 제한 없음" : `기준 중위소득 ${p.incomeMax}% 이하`;
    if (a.income == null) push("unknown", `${label} · 소득을 모르겠다고 답하셨습니다`);
    else push(a.income <= p.incomeMax ? "yes" : "no", `${label} · 고른 답 ${a.income >= 999 ? "150% 넘음" : a.income + "% 이하"}`);
  }
  if (p.status) {
    const ok = p.status.includes(a.status);
    push(ok ? "yes" : "no", `${p.status.map((s) => STATUS_LABEL[s]).join(", ")} 대상 · 고른 답 ${STATUS_LABEL[a.status]}`);
  }
  if (p.marital) {
    const ok = p.marital.includes(a.marital) || (p.marital.includes("child") && a.household === "kids");
    push(ok ? "yes" : "no", `${p.marital.map((s) => MARITAL_LABEL[s]).join(", ")} 가구 대상 · 고른 답 ${MARITAL_LABEL[a.marital]}`);
  }
  if (p.disability) {
    const ok = p.disability.includes(a.disability);
    push(ok ? "yes" : "no", `장애 등록 본인 · 고른 답 ${DISABILITY_LABEL[a.disability]}`);
  }
  push("unknown", "예산 소진·서류 심사 등 남은 조건은 기관에서 확인해야 합니다.");

  const reason = worst === "yes"
    ? "고른 답으로 보면 공개된 핵심 자격에 모두 들어갑니다."
    : worst === "unknown"
      ? "핵심 자격은 걸리지 않지만 확인하지 못한 조건이 남아 있습니다."
      : "고른 답과 맞지 않는 조건이 있습니다. 아래 항목을 확인해 보세요.";
  return { verdict: worst, checks, reason };
}

function matched() {
  const a = state.answers;
  const interests = Array.isArray(a.interest) ? a.interest : [];
  const rows = POLICIES.map((p) => ({ p, ev: evaluate(p, a) }))
    .filter(({ ev }) => ev.verdict !== "no")
    .map((row) => ({ ...row, hit: row.p.cat.some((c) => interests.includes(c)) }));
  const wanted = rows.filter((r) => r.hit);
  const list = wanted.length ? wanted : rows;
  const order = { yes: 0, unknown: 1 };
  const catalog = list.sort((x, y) => order[x.ev.verdict] - order[y.ev.verdict]);
  return catalog.concat(state.liveItems);
}

function renderSegments() {
  els.segmentGrid.innerHTML = SEGMENTS.map((seg) => `
    <div class="segment-card">
      <strong>${esc(seg.name)}</strong>
      <span>${esc(seg.desc)}</span>
    </div>
  `).join("");
}

function renderChat() {
  const q = QUESTIONS[Math.min(state.step, QUESTIONS.length - 1)];
  const pct = Math.round((Math.min(state.step, QUESTIONS.length) / QUESTIONS.length) * 100);
  els.progressBar.style.width = pct + "%";
  els.progressLabel.textContent = `${Math.min(state.step + 1, QUESTIONS.length)} / ${QUESTIONS.length}`;

  els.chatLog.innerHTML = state.messages.map((m) => {
    if (m.role === "user") {
      return `<div class="bubble bubble-user"><p>${esc(m.text)}</p></div>`;
    }
    return `<div class="bubble bubble-bot">
      <p><strong>${esc(m.text)}</strong></p>
      ${m.hint ? `<p class="bubble-hint">${esc(m.hint)}</p>` : ""}
    </div>`;
  }).join("");
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
  renderChoices(true);
}

function renderChoices(focusFirst) {
  const q = QUESTIONS[Math.min(state.step, QUESTIONS.length - 1)];
  els.choiceList.innerHTML = "";
  q.options.forEach((opt) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.textContent = opt.l;
    if (q.multi && state.multiPicked.includes(opt.v)) btn.classList.add("is-on");
    btn.addEventListener("click", () => {
      if (q.multi) {
        toggleMulti(opt.v);
        renderChoices(false);
      } else {
        answer(q, opt.l, opt.v);
      }
    });
    els.choiceList.appendChild(btn);
  });
  if (q.multi) {
    els.multiBtn.hidden = false;
    els.multiBtn.textContent = state.multiPicked.length
      ? `${state.multiPicked.length}개 고름 · 결과 보기`
      : "고르지 않고 결과 보기";
  } else {
    els.multiBtn.hidden = true;
  }
  if (focusFirst) {
    const first = els.choiceList.querySelector(".choice");
    if (first) first.focus();
  }
}

function ageLabel() {
  const found = QUESTIONS[0].options.find((o) => o.v === state.answers.age);
  return found ? found.l : "";
}

function renderResults() {
  const rows = matched();
  const visible = state.filter === "all" ? rows : rows.filter((r) => r.ev.verdict === state.filter);
  const yesCount = rows.filter((r) => r.ev.verdict === "yes").length;
  const unknownCount = rows.filter((r) => r.ev.verdict === "unknown").length;
  const interests = Array.isArray(state.answers.interest) ? state.answers.interest : [];

  els.profileLine.textContent = [ageLabel(), state.answers.region, interests.join("·")].filter(Boolean).join(" · ");
  els.resultHeadline.textContent = rows.length ? `받을 수 있어 보이는 정책 ${rows.length}건` : "결과";

  els.resultFilter.innerHTML = [
    { id: "all", label: `전체 ${rows.length}` },
    { id: "yes", label: `됩니다 ${yesCount}` },
    { id: "unknown", label: `확인 필요 ${unknownCount}` },
  ].map((tab) => `
    <button type="button" data-filter="${tab.id}" ${state.filter === tab.id ? 'aria-selected="true" class="is-on"' : ""}>${esc(tab.label)}</button>
  `).join("");

  els.resultList.innerHTML = "";
  visible.forEach(({ p, ev }) => {
    const chip = CHIP[ev.verdict];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "policy-card";
    btn.innerHTML = `
      <span class="policy-top">
        <span class="stamp" style="background:${chip.bg};color:${chip.color}">${esc(chip.label)}</span>
        <span class="meta-tiny">${esc([p.org, p.cat.join("·")].filter(Boolean).join(" · "))}</span>
      </span>
      <strong>${esc(p.title)}</strong>
      <em>${esc(p.summary)}</em>
    `;
    btn.addEventListener("click", () => openDetail(p.id));
    els.resultList.appendChild(btn);
  });

  els.resultEmpty.hidden = visible.length > 0;
  showScreen("result");
}

function openDetail(id) {
  const row = matched().find((r) => r.p.id === id);
  if (!row) return;
  state.detailId = id;
  const { p, ev } = row;
  const tone = ev.verdict === "yes" ? "yes" : ev.verdict === "unknown" ? "unknown" : "no";
  const title = ev.verdict === "yes" ? "됩니다" : ev.verdict === "unknown" ? "확인이 필요합니다" : "어렵습니다";
  els.detailBanner.className = "verdict-banner verdict-" + tone;
  els.detailBanner.innerHTML = `
    <p class="kicker">참고 결론 · 최종 자격 확정 아님</p>
    <h2>${title}</h2>
    <p>${esc(ev.reason)}</p>
  `;
  els.detailMeta.textContent = [p.org, p.cat.join("·")].filter(Boolean).join(" · ");
  els.detailTitle.textContent = p.title;
  els.detailSummary.textContent = p.summary;
  els.detailChecks.innerHTML = ev.checks.map((c) => {
    const chip = CHIP[c.match];
    return `<li><span class="stamp" style="background:${chip.bg};color:${chip.color}">${esc(chip.label)}</span><span>${esc(c.text)}</span></li>`;
  }).join("");
  els.detailDocs.innerHTML = (p.docs || []).map((d) => `<li>${esc(d)}</li>`).join("")
    || "<li>공고 원문에서 확인해 주세요.</li>";
  els.detailDeadline.textContent = p.deadline || "공고 원문에서 확인해 주세요.";
  if (p.link) {
    els.detailLink.innerHTML = `<a href="${esc(p.link)}" target="_blank" rel="noopener noreferrer">${esc(p.linkLabel || p.link)}</a>`;
  } else {
    els.detailLink.textContent = "담당 기관 공고를 확인해 주세요.";
  }
  showScreen("detail");
}

async function maybeFetchYouth() {
  const age = state.answers.age;
  const region = state.answers.region;
  if (age == null || age < 19 || age > 39) return;
  els.liveStatus.textContent = "온통청년에서 같은 나이·지역 정책을 더 찾고 있습니다.";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const params = new URLSearchParams({ source: "policy", age: String(age) });
    if (region) params.set("region", region);
    const res = await fetch(`/api/policies?${params}`, { signal: controller.signal });
    const data = await res.json().catch(() => ({}));
    const items = Array.isArray(data.items) ? data.items : [];
    const known = new Set(POLICIES.map((p) => p.title));
    state.liveItems = items.slice(0, 6).filter((it) => it.title && !known.has(it.title)).map((it) => ({
      p: {
        id: "live-" + it.id,
        title: it.title,
        org: it.inst || "온통청년",
        cat: ["일자리"],
        summary: it.summary || "온통청년 목록에서 가져온 정책입니다. 원문에서 자격과 서류를 확인하세요.",
        docs: ["공고 원문에서 확인"],
        deadline: "공고 원문에서 확인",
        link: "https://www.youthcenter.go.kr/",
        linkLabel: "온통청년",
        live: true,
      },
      ev: {
        verdict: "unknown",
        reason: "온통청년 목록에서 더 가져온 항목입니다. 공개 요약만 있어 확인이 필요합니다.",
        checks: [
          { match: "yes", text: `나이 ${age}세 전후 · 온통청년 청년 정책 목록` },
          { match: region ? "yes" : "unknown", text: region ? `거주 ${region}` : "거주 미확인" },
          { match: "unknown", text: "서류·소득·세부 자격은 공고 원문에서 확인해야 합니다." },
        ],
      },
      hit: true,
    }));
    if (state.screen === "result") renderResults();
    els.liveStatus.textContent = state.liveItems.length
      ? `온통청년에서 ${state.liveItems.length}건을 더 붙였습니다.`
      : "온통청년에서 더 붙일 항목이 없습니다.";
  } catch (_) {
    els.liveStatus.textContent = "온통청년 추가 목록은 생략했습니다. 위 결과만 보시면 됩니다.";
  } finally {
    clearTimeout(timer);
  }
}

function finishToResult() {
  renderResults();
  maybeFetchYouth();
}

function bind() {
  els.logoBtn.addEventListener("click", goHome);
  els.guideBtn.addEventListener("click", goGuide);
  els.startBtn.addEventListener("click", startChat);
  els.guideStartBtn.addEventListener("click", startChat);
  els.backBtn.addEventListener("click", goBackStep);
  els.multiBtn.addEventListener("click", confirmMulti);
  els.restartBtn.addEventListener("click", startChat);
  els.resultGuideBtn.addEventListener("click", goGuide);
  els.backResultBtn.addEventListener("click", () => { renderResults(); });
  els.fontBtn.addEventListener("click", () => {
    state.fontIdx = (state.fontIdx + 1) % FONTS.length;
    applyFont();
  });
  els.resultFilter.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-filter]");
    if (!btn) return;
    state.filter = btn.getAttribute("data-filter");
    renderResults();
  });
}

function restoreFont() {
  try {
    const saved = localStorage.getItem("doenayo-font");
    const idx = FONTS.findIndex((f) => f.label === saved);
    if (idx >= 0) state.fontIdx = idx;
  } catch (_) { /* ignore */ }
  applyFont();
}

function demoIfNeeded() {
  if (new URLSearchParams(location.search).get("demo") !== "1") return;
  state.answers = {
    age: 25,
    region: "대전",
    household: "single",
    income: 150,
    status: "student",
    marital: "unmarried",
    disability: "none",
    interest: ["주거", "교육", "일자리"],
  };
  finishToResult();
}

restoreFont();
renderSegments();
bind();
showScreen("home");
demoIfNeeded();
