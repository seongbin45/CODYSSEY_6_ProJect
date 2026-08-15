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
const userAge = document.getElementById('user-age');
const userRegion = document.getElementById('user-region');
const userEmployment = document.getElementById('user-employment');
const geoHint = document.getElementById('geo-hint');
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

let regionTouched = false;
if (userRegion) {
  userRegion.addEventListener('input', () => { regionTouched = true; });
  userRegion.addEventListener('change', () => { regionTouched = true; });
}

async function suggestRegionFromIp() {
  if (!userRegion || regionTouched) return;
  try {
    const res = await fetch('/api/geo');
    const data = await res.json().catch(() => ({}));
    const place = (data.city || data.label || data.region || '').trim();
    if (!res.ok || !place) return;
    if (regionTouched) return;
    userRegion.value = place;
    if (geoHint) {
      geoHint.textContent = `접속 위치를 기준으로 「${place}」을 추천했습니다. 다르면 직접 바꿔 주세요.`;
    }
  } catch (_) {
    if (geoHint) geoHint.textContent = '';
  }
}

// ── 통신 ──────────────────────────────────────────────
function readProfile() {
  const ageRaw = userAge ? userAge.value.trim() : '';
  const age = ageRaw === '' ? null : Number(ageRaw);
  return {
    age: Number.isInteger(age) ? age : null,
    region: (userRegion && userRegion.value.trim()) || '',
    employment: (userEmployment && userEmployment.value) || '',
  };
}

async function requestSummary(text, profile) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input: text,
        age: profile.age,
        region: profile.region,
        employment: profile.employment,
      }),
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
  const verdict = r.verdict === 'yes' ? 'yes' : r.verdict === 'no' ? 'no' : 'unknown';
  const verdictCopy = {
    yes: { label: '됩니다', reason: r.verdict_reason || '입력한 조건으로 보면 이 공고의 핵심 자격에 들어갑니다.' },
    no: { label: '안됩니다', reason: r.verdict_reason || '입력한 조건으로는 이 공고의 자격에 들지 않습니다.' },
    unknown: { label: '지금은 단정하기 어려워요', reason: r.verdict_reason || '나이·거주 외에 소득처럼 확인할 수 없는 조건이 남아 있습니다.' },
  }[verdict];
  const matchLabel = { yes: '됩니다', no: '안됩니다', unknown: '확인 필요' };

  const block = (title, inner) =>
    `<section class="result-block"><h3>${esc(title)}</h3>${inner}</section>`;

  const html = [
    `<section class="verdict verdict-${verdict}" aria-live="assertive">
      <p class="verdict-kicker">참고 결론 · 최종 자격 확정 아님</p>
      <h3>${esc(verdictCopy.label)}</h3>
      <p>${esc(verdictCopy.reason)}</p>
    </section>`,

    r.title ? `<p class="result-title">${esc(r.title)}</p>` : '',

    block('한눈에 보기',
      `<ol class="summary">${summary.map(s => `<li>${esc(s)}</li>`).join('')}</ol>`),

    block('조건별 판정',
      eligibility.length
        ? `<ul class="checklist">${eligibility.map((e, i) => {
            const match = e.match === 'yes' || e.match === 'no' ? e.match : 'unknown';
            return `
            <li>
              <span class="mark-${match}">${esc(matchLabel[match])}</span>
              <label for="elig-${i}">${esc(e.item)}
                ${e.note ? `<span class="note">${esc(e.note)}</span>` : ''}
              </label>
            </li>`;
          }).join('')}</ul>`
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

    `<p class="disclaimer">⚠️ AI가 지원 가능 여부를 대신 결정하지 않습니다.
      됩니다 / 안됩니다는 입력한 조건과 붙여넣은 문장만 본 참고 결론입니다.
      최종 자격과 서류는 공고 원문과 담당 기관에서 확인하세요.</p>`,
  ].join('');

  result.innerHTML = html;
}

// ── 상태 전환 ─────────────────────────────────────────
function setLoading(on) {
  btn.disabled = on;
  btn.textContent = on ? '공고문을 읽는 중...' : '참고 결론 보기';
  if (on) {
    notice.textContent = '';
    result.innerHTML = '<p class="loading-hint" aria-busy="true">공고 조건을 나누고 있습니다. 잠시만 기다려 주세요.</p>';
  }
}

// ── 제출 ──────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  const profile = readProfile();

  // 클라이언트 1차 검증 — 서버 왕복 없이 즉시 안내 (무료 쿼터 절약)
  if (profile.age == null) {
    showError('됩니다·안됩니다를 보려면 만나이를 넣어 주세요.');
    if (userAge) userAge.focus();
    return;
  }
  if (!profile.region) {
    showError('거주 시·군을 입력해 주세요.');
    if (userRegion) userRegion.focus();
    return;
  }
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
    render(await requestSummary(text, profile));
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
    const sourceLabel = { policy: '정책', content: '콘텐츠', space: '청년공간' }[item.source] || '정책';
    button.innerHTML = `
      <strong>${esc(item.title || '제목 없음')}</strong>
      <span class="meta">${esc([sourceLabel, item.region, item.inst].filter(Boolean).join(' · '))}</span>
      ${item.summary ? `<p class="snippet">${esc(item.summary)}</p>` : ''}
    `;
    button.addEventListener('click', () => pickYouthPolicy(item.id, item.source || 'policy', button));
    li.appendChild(button);
    youthList.appendChild(li);
  });
  youthList.hidden = false;
}

async function loadYouthPolicies() {
  if (!youthLoadBtn) return;
  const q = (youthQuery && youthQuery.value.trim()) || '';
  youthLoadBtn.disabled = true;
  const profile = readProfile();
  setYouthStatus('온통청년 정책·콘텐츠·청년공간을 조건에 맞춰 찾는 중입니다.');
  try {
    const params = new URLSearchParams({ source: 'all' });
    if (q) params.set('q', q);
    if (profile.age != null) params.set('age', String(profile.age));
    if (profile.region) params.set('region', profile.region);
    const res = await fetch(`/api/policies?${params.toString()}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || '온통청년 목록을 가져오지 못했습니다.');
    }
    const items = Array.isArray(data.items) ? data.items : [];
    renderYouthList(items);
    const stats = data.stats || {};
    const bits = ['정책', '콘텐츠', '청년공간'].map((label, i) => {
      const key = ['policy', 'content', 'space'][i];
      const row = stats[key] || {};
      return `${label} ${row.kept ?? 0}`;
    });
    const cond = [profile.age != null ? `나이 ${profile.age}` : '', profile.region ? `거주 ${profile.region}` : '']
      .filter(Boolean).join(' · ');
    setYouthStatus(items.length
      ? `${cond ? cond + ' 기준 · ' : ''}${bits.join(' · ')}건. 고르면 아래 입력창에 채워집니다.`
      : '조건에 맞는 항목이 없습니다. 나이·거주를 확인하거나 검색어를 바꿔 보세요.');
  } catch (err) {
    renderYouthList([]);
    setYouthStatus(err.message || '온통청년 목록을 가져오지 못했습니다.');
  } finally {
    youthLoadBtn.disabled = false;
  }
}

async function pickYouthPolicy(id, source, button) {
  if (!id) return;
  if (button) button.disabled = true;
  setYouthStatus('선택한 항목의 상세를 불러오는 중입니다.');
  try {
    const res = await fetch(`/api/policies?id=${encodeURIComponent(id)}&source=${encodeURIComponent(source || 'policy')}`);
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
  el.addEventListener('click', () => setTimeout(() => (userAge || input).focus(), 400));
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

if (new URLSearchParams(location.search).get('demo') !== '1') {
  suggestRegionFromIp();
}

// README·증빙용 미리보기: ?demo=1
if (new URLSearchParams(location.search).get('demo') === '1') {
  if (userAge) userAge.value = '24';
  if (userRegion) userRegion.value = '군산';
  input.value = SAMPLE_TEXT;
  input.dispatchEvent(new Event('input'));
  render({
    is_policy: true,
    verdict: 'yes',
    verdict_reason: '만 24세·군산 거주라 나이와 지역 조건에 들어갑니다. 관심·SNS 조건은 직접 확인하세요.',
    title: '2026 군산 청년 서포터즈 2기 참여자 모집',
    summary: [
      '군산시 청년 12명이 축제·관광 홍보를 하는 서포터즈입니다.',
      '온라인 미션 성공 시 월 15만원을 받습니다.',
      '6월 3일부터 25일까지 신청합니다.',
    ],
    eligibility: [
      { item: '군산시에 주소를 둔 청년', note: '18세 이상 39세 이하', match: 'yes' },
      { item: '만 18세 이상 39세 이하', note: '신청일 기준', match: 'yes' },
      { item: '청년정책·사회참여에 관심이 있을 것', note: '주관 조건', match: 'unknown' },
    ],
    documents: ['참여신청서', '주민등록초본', '개인정보동의서', '활동계획서'],
    deadline: '2026. 6. 3.(수) ~ 6. 25.(목)',
    terms: [{ word: '기타소득', meaning: '근로소득이 아닌 일시적 수입입니다. 활동비에 세금이 붙는다는 뜻으로 자주 나옵니다.' }],
  });
  location.hash = '#check';
}
