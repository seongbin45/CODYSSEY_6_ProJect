// ── 설정 ──────────────────────────────────────────────
const TIMEOUT_MS = 25000;
const MIN_LEN = 10;
const MAX_LEN = 2000;

// 군산시 청년정책 포털 「2026 군산 청년 서포터즈 2기 참여자 모집」 발췌
const SAMPLE_TEXT = `2026 군산 청년 서포터즈 2기 참여자 모집 공고

1. 모집대상
  - 군산시에 주소를 둔 청년(18세 이상 39세 이하)
  - 청년정책 및 사회참여에 관심이 있는 자
  - SNS를 활발히 운영하며 콘텐츠 제작이 가능한 자

2. 모집인원
  - 12명 (3인 1조 팀 프로젝트로 운영)

3. 활동기간
  - 2026. 7. 1.(수) ~ 10. 30.(금) (4개월)

4. 활동내용
  - 군산시 주요 축제·관광·캐릭터 등을 활용한 온라인 콘텐츠 제작
  - 오프라인 축제 현장 홍보
  - 필수 교육 및 네트워킹 참석

5. 활동혜택
  - 온라인 미션 성공 시 월 15만원 지급 (기타소득 8.8% 징수)
  - 오프라인 미션 참여 시 회당 10만원 추가 지급
  - 저작권, 홍보 트렌드, AI 디자인·영상 제작 교육 제공
  - 서포터즈 ID카드, 활동증명서 발급, 우수팀 시상

6. 제출서류
  - 참여신청서, 주민등록초본, 개인정보동의서, 활동계획서
  - 포트폴리오(선택)

7. 모집기간
  - 2026. 6. 3.(수) ~ 6. 25.(목)

8. 문의처
  - 063-471-1555 / 0hee@kunsan.ac.kr`;

// ── DOM ───────────────────────────────────────────────
const form      = document.getElementById('check-form');
const input     = document.getElementById('policy-input');
const counter   = document.getElementById('char-count');
const btn       = document.getElementById('submit-btn');
const notice    = document.getElementById('notice');
const result    = document.getElementById('result');
const sampleBtn = document.getElementById('sample-btn');
const youthQuery = document.getElementById('youth-query');
const youthLoadBtn = document.getElementById('youth-load-btn');
const youthStatus = document.getElementById('youth-status');
const youthList = document.getElementById('youth-list');
const hamburger = document.querySelector('.hamburger');
const navLinks  = document.querySelector('.nav-links');
const themeBtn  = document.getElementById('theme-toggle');

// ── 글자수 카운터 ──────────────────────────────────────
function updateCounter() {
  const n = input.value.trim().length;
  counter.textContent = `${n.toLocaleString()} / ${MAX_LEN.toLocaleString()}자`;
  counter.classList.toggle('over', n > MAX_LEN);
}

input.addEventListener('input', updateCounter);

// ── 통신 ──────────────────────────────────────────────
async function requestSummary(text) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: text }),
      signal: controller.signal,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      // 서버가 내려준 안내 문구를 그대로 사용 (400 / 500 / 502)
      throw new Error(data.error || '요청을 처리하지 못했습니다.');
    }
    return data.result;

  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.');
    }
    if (err instanceof TypeError) {
      throw new Error('네트워크 연결을 확인해 주세요.');
    }
    throw err;

  } finally {
    clearTimeout(timer);
  }
}

// ── 렌더링 ────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]
  ));
}

function showError(message) {
  result.innerHTML = '';
  notice.textContent = message;
}

function render(r) {
  if (!r || typeof r !== 'object') {
    throw new Error('결과를 정리하지 못했습니다. 내용을 조금 줄여서 다시 시도해 주세요.');
  }

  result.innerHTML = '';
  if (!r.is_policy) {
    showError('정책 공고문으로 보이지 않습니다. 지원 자격이나 신청 방법이 담긴 부분을 붙여넣어 주세요.');
    return;
  }
  notice.textContent = '';

  const summary = Array.isArray(r.summary) ? r.summary : [];
  const eligibility = Array.isArray(r.eligibility) ? r.eligibility : [];
  const documents = Array.isArray(r.documents) ? r.documents : [];
  const terms = Array.isArray(r.terms) ? r.terms : [];

  const block = (title, inner) =>
    `<section class="result-block"><h3>${esc(title)}</h3>${inner}</section>`;

  const html = [
    r.title ? `<p class="result-title">${esc(r.title)}</p>` : '',

    block('한눈에 보기',
      `<ol class="summary">${summary.map(s => `<li>${esc(s)}</li>`).join('')}</ol>`),

    block('내가 대상인지 확인하기',
      eligibility.length
        ? `<ul class="checklist">${eligibility.map((e, i) => `
            <li>
              <input type="checkbox" id="elig-${i}">
              <label for="elig-${i}">${esc(e.item)}
                ${e.note ? `<span class="note">${esc(e.note)}</span>` : ''}
              </label>
            </li>`).join('')}</ul>`
        : '<p class="empty">공고문에서 자격 조건을 찾지 못했습니다.</p>'),

    block('준비할 서류',
      documents.length
        ? `<ul class="docs">${documents.map(d => `<li>${esc(d)}</li>`).join('')}</ul>`
        : '<p class="empty">공고문에 명시되지 않음</p>'),

    block('신청 기한', `<p class="deadline">${esc(r.deadline || '공고문에 명시되지 않음')}</p>`),

    terms.length
      ? block('어려운 말 풀이',
          `<dl class="terms">${terms.map(t =>
            `<dt>${esc(t.word)}</dt><dd>${esc(t.meaning)}</dd>`).join('')}</dl>`)
      : '',

    `<p class="disclaimer">⚠️ 이 결과는 AI가 붙여넣은 텍스트만 보고 정리한 참고 자료입니다.
      최종 자격과 서류는 반드시 공고 원문과 담당 기관을 통해 확인하세요.</p>`,
  ].join('');

  result.innerHTML = html;
}

// ── 상태 전환 ─────────────────────────────────────────
function setLoading(on) {
  btn.disabled = on;
  btn.textContent = on ? '정리하는 중...' : '결과 확인하기';
  if (on) {
    notice.textContent = '';
    result.innerHTML = '<p class="loading-hint" aria-busy="true">공고문을 읽고 있습니다. 잠시만 기다려 주세요.</p>';
  }
}

// ── 제출 ──────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = input.value.trim();

  // 클라이언트 1차 검증 — 서버 왕복 없이 즉시 안내 (무료 쿼터 절약)
  if (!text) {
    showError('공고문 내용을 붙여넣어 주세요.');
    input.focus();
    return;
  }
  if (text.length < MIN_LEN) {
    showError('내용이 너무 짧습니다. 지원 자격이나 서류 부분을 함께 붙여넣어 주세요.');
    input.focus();
    return;
  }
  if (text.length > MAX_LEN) {
    showError(`${MAX_LEN.toLocaleString()}자까지 입력할 수 있습니다.`);
    input.focus();
    return;
  }

  setLoading(true);
  try {
    render(await requestSummary(text));
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

// ── 온통청년 목록 ─────────────────────────────────────
function setYouthStatus(message) {
  if (youthStatus) youthStatus.textContent = message || '';
}

function renderYouthList(items) {
  if (!youthList) return;
  youthList.innerHTML = '';
  if (!items.length) {
    youthList.hidden = true;
    return;
  }
  items.forEach((item) => {
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.innerHTML = `
      <strong>${esc(item.title || '제목 없음')}</strong>
      <span class="meta">${esc([item.region, item.inst].filter(Boolean).join(' · '))}</span>
      ${item.summary ? `<p class="snippet">${esc(item.summary)}</p>` : ''}
    `;
    button.addEventListener('click', () => pickYouthPolicy(item.id, button));
    li.appendChild(button);
    youthList.appendChild(li);
  });
  youthList.hidden = false;
}

async function loadYouthPolicies() {
  if (!youthLoadBtn) return;
  const q = (youthQuery && youthQuery.value.trim()) || '';
  youthLoadBtn.disabled = true;
  setYouthStatus('온통청년에서 전북·군산 정책을 찾는 중입니다.');
  try {
    const params = new URLSearchParams({ scope: q.includes('군산') ? 'gunsan' : 'jeonbuk' });
    if (q) params.set('q', q);
    const res = await fetch(`/api/policies?${params.toString()}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || '온통청년 목록을 가져오지 못했습니다.');
    }
    const items = Array.isArray(data.items) ? data.items : [];
    renderYouthList(items);
    setYouthStatus(items.length
      ? `${items.length}건입니다. 고르면 아래 입력창에 채워집니다.`
      : '조건에 맞는 정책이 없습니다. 검색어를 바꾸거나 직접 붙여넣어 주세요.');
  } catch (err) {
    renderYouthList([]);
    setYouthStatus(err.message || '온통청년 목록을 가져오지 못했습니다.');
  } finally {
    youthLoadBtn.disabled = false;
  }
}

async function pickYouthPolicy(id, button) {
  if (!id) return;
  if (button) button.disabled = true;
  setYouthStatus('선택한 정책의 상세를 불러오는 중입니다.');
  try {
    const res = await fetch(`/api/policies?id=${encodeURIComponent(id)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || '정책 상세를 가져오지 못했습니다.');
    }
    const text = (data.item && data.item.text) || '';
    if (!text) {
      throw new Error('정책 본문이 비어 있습니다. 다른 항목을 고르거나 직접 붙여넣어 주세요.');
    }
    input.value = text.slice(0, MAX_LEN);
    input.dispatchEvent(new Event('input'));
    input.focus();
    setYouthStatus(`「${data.item.title || '선택한 정책'}」을 입력창에 넣었습니다. 결과 확인하기를 눌러 주세요.`);
  } catch (err) {
    setYouthStatus(err.message);
  } finally {
    if (button) button.disabled = false;
  }
}

if (youthLoadBtn) {
  youthLoadBtn.addEventListener('click', loadYouthPolicies);
}
if (youthQuery) {
  youthQuery.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      loadYouthPolicies();
    }
  });
}

// ── 샘플 넣어보기 ─────────────────────────────────────
sampleBtn.addEventListener('click', () => {
  input.value = SAMPLE_TEXT;
  input.dispatchEvent(new Event('input'));
  input.focus();
});

// ── 홈 CTA → 입력창 포커스 ────────────────────────────
document.querySelectorAll('[data-goto-check]').forEach(el => {
  el.addEventListener('click', () => setTimeout(() => input.focus(), 400));
});

// ── 모바일 햄버거 메뉴 ────────────────────────────────
function setMenuOpen(open) {
  if (!hamburger || !navLinks) return;
  hamburger.setAttribute('aria-expanded', String(open));
  hamburger.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
  navLinks.classList.toggle('is-open', open);
  document.body.classList.toggle('menu-open', open);
}

if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    const open = hamburger.getAttribute('aria-expanded') !== 'true';
    setMenuOpen(open);
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => setMenuOpen(false));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setMenuOpen(false);
  });
}

// ── 다크 모드 ─────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (themeBtn) {
    themeBtn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    themeBtn.textContent = theme === 'dark' ? '낮' : '밤';
    themeBtn.setAttribute('aria-label', theme === 'dark' ? '라이트 모드로 바꾸기' : '다크 모드로 바꾸기');
  }
}

const savedTheme = localStorage.getItem('doenayo-theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
applyTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

if (themeBtn) {
  themeBtn.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem('doenayo-theme', next);
    applyTheme(next);
  });
}
