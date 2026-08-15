const QUESTIONS = [
  {
    id: "age",
    q: "나이가 어떻게 되시나요?",
    hint: "연령대만 골라 주세요.",
    options: [
      { v: 17, l: "19세 미만" },
      { v: 25, l: "20대" },
      { v: 34, l: "30대" },
      { v: 45, l: "40대" },
      { v: 55, l: "50대" },
      { v: 67, l: "60대" },
      { v: 75, l: "70세 이상" },
    ],
  },
  {
    id: "region",
    q: "어디에 살고 계신가요?",
    hint: "주민등록 기준 시·도를 골라 주세요.",
    options: ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
      .map((r) => ({ v: r, l: r })),
  },
  {
    id: "household",
    q: "함께 사는 가족은 어떻게 되시나요?",
    options: [
      { v: "single", l: "혼자 삽니다" },
      { v: "couple", l: "배우자와 둘이" },
      { v: "kids", l: "자녀와 함께" },
      { v: "parents", l: "부모님과 함께" },
      { v: "onefam", l: "한부모 가구" },
      { v: "etc", l: "그 밖" },
    ],
  },
  {
    id: "income",
    q: "가구 소득은 어느 정도인가요?",
    hint: "기준 중위소득 대비입니다. 모르면 모르겠어요를 골라도 됩니다.",
    options: [
      { v: 50, l: "중위 50% 이하" },
      { v: 100, l: "50~100%" },
      { v: 150, l: "100~150%" },
      { v: 999, l: "150% 넘음" },
      { v: null, l: "모르겠어요" },
    ],
  },
  {
    id: "status",
    q: "요즘 상태에 가장 가까운 것은요?",
    options: [
      { v: "student", l: "학생" },
      { v: "jobless", l: "구직 중" },
      { v: "worker", l: "재직 중" },
      { v: "owner", l: "자영업·소상공인" },
      { v: "care", l: "육아·휴직 중" },
      { v: "retired", l: "은퇴·무직" },
    ],
  },
  {
    id: "marital",
    q: "혼인·자녀 상황을 알려 주세요.",
    options: [
      { v: "unmarried", l: "미혼" },
      { v: "married", l: "기혼, 자녀 없음" },
      { v: "child", l: "기혼, 자녀 있음" },
      { v: "pregnant", l: "임신 중·출산 예정" },
      { v: "onefam", l: "한부모" },
    ],
  },
  {
    id: "disability",
    q: "장애 등록 여부가 있으신가요?",
    options: [
      { v: "none", l: "없습니다" },
      { v: "self", l: "본인이 등록" },
      { v: "family", l: "가족 중 등록" },
    ],
  },
  {
    id: "interest",
    q: "어떤 도움이 필요하신가요?",
    hint: "여러 개 고를 수 있습니다.",
    multi: true,
    options: [
      { v: "주거", l: "주거" },
      { v: "일자리", l: "일자리" },
      { v: "교육", l: "교육" },
      { v: "돌봄", l: "돌봄" },
      { v: "건강", l: "건강" },
      { v: "창업", l: "창업" },
      { v: "금융", l: "생활비·금융" },
      { v: "문화", l: "문화·여가" },
    ],
  },
];

const POLICIES = [
  {
    id: "p1", title: "청년 월세 특별지원", org: "국토교통부", cat: ["주거"], age: [19, 34], incomeMax: 150,
    summary: "무주택 청년에게 월세 일부를 최대 12개월 지원합니다.",
    docs: ["임대차계약서 사본", "월세 이체 증빙", "가족관계증명서"],
    deadline: "상시 접수 (예산 소진 시 조기 마감)", link: "https://www.myhome.go.kr/", linkLabel: "마이홈포털",
  },
  {
    id: "p2", title: "청년내일저축계좌", org: "보건복지부", cat: ["금융"], age: [19, 39], incomeMax: 100, status: ["worker", "owner"],
    summary: "일하는 저소득 청년이 저축하면 정부가 같은 금액을 더 얹어 줍니다.",
    docs: ["소득 증빙(재직·사업자)", "통장 사본", "가입 신청서"],
    deadline: "매년 5월 전후 집중 신청", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p3", title: "국민취업지원제도", org: "고용노동부", cat: ["일자리"], age: [15, 69], incomeMax: 150, status: ["jobless", "care", "retired"],
    summary: "구직자에게 취업 상담과 훈련, 구직촉진수당을 함께 제공합니다.",
    docs: ["신분증", "구직신청서", "소득·재산 증빙"],
    deadline: "상시 접수", link: "https://www.work24.go.kr/", linkLabel: "고용24",
  },
  {
    id: "p4", title: "신혼·신생아 전세임대주택", org: "LH", cat: ["주거"], age: [19, 49], incomeMax: 150, marital: ["married", "child", "pregnant"],
    summary: "신혼부부·출산 가구가 원하는 집을 고르면 공공이 전세 계약을 대신 맺어 재임대합니다.",
    docs: ["혼인관계증명서", "주민등록등본", "소득·자산 증빙"],
    deadline: "지역별 공고 시 접수", link: "https://apply.lh.or.kr/", linkLabel: "LH 청약플러스",
  },
  {
    id: "p5", title: "아이돌봄서비스", org: "여성가족부", cat: ["돌봄"], age: [20, 64], marital: ["child", "pregnant", "onefam"],
    summary: "돌보미가 집으로 찾아와 아이를 돌봐 줍니다. 소득에 따라 이용료를 차등 지원합니다.",
    docs: ["주민등록등본", "소득 증빙", "이용 신청서"],
    deadline: "상시 접수", link: "https://www.idolbom.go.kr/", linkLabel: "아이돌봄서비스",
  },
  {
    id: "p6", title: "첫만남이용권", org: "보건복지부", cat: ["돌봄", "금융"], marital: ["pregnant", "child"],
    summary: "출생아 한 명당 바우처 포인트를 지급해 초기 양육비 부담을 덜어 줍니다.",
    docs: ["출생신고서", "신청인 신분증"],
    deadline: "출생일로부터 1년 이내", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p7", title: "국가장학금", org: "한국장학재단", cat: ["교육"], age: [17, 34], incomeMax: 150, status: ["student"],
    summary: "소득 구간에 따라 대학 등록금을 차등 지원합니다.",
    docs: ["가족관계증명서", "소득·재산 조사 동의", "재학 증빙"],
    deadline: "학기별 1·2차 신청 기간", link: "https://www.kosaf.go.kr/", linkLabel: "한국장학재단",
  },
  {
    id: "p8", title: "평생교육이용권", org: "교육부", cat: ["교육"], age: [19, 99], incomeMax: 100,
    summary: "온·오프라인 강좌 수강료로 쓸 수 있는 교육 이용권을 지급합니다.",
    docs: ["신청서", "소득 증빙"],
    deadline: "연 1회 모집 (선착순 마감)", link: "https://www.lllcard.kr/", linkLabel: "평생교육이용권",
  },
  {
    id: "p9", title: "중장년 재취업 지원(폴리텍·전직지원)", org: "고용노동부", cat: ["일자리", "교육"], age: [40, 64],
    summary: "40대 이후 경력 전환을 위한 직업훈련과 전직 상담을 제공합니다.",
    docs: ["신분증", "경력 증빙", "훈련 신청서"],
    deadline: "과정별 모집 일정", link: "https://www.work24.go.kr/", linkLabel: "고용24",
  },
  {
    id: "p10", title: "소상공인 정책자금 융자", org: "소상공인시장진흥공단", cat: ["창업", "금융"], age: [19, 99], status: ["owner"],
    summary: "사업 운영·시설 자금을 시중보다 낮은 금리로 융자해 줍니다.",
    docs: ["사업자등록증", "부가세과세표준증명", "임대차계약서"],
    deadline: "예산 범위 내 상시 접수", link: "https://www.semas.or.kr/", linkLabel: "소상공인시장진흥공단",
  },
  {
    id: "p11", title: "노인일자리 및 사회활동 지원", org: "보건복지부", cat: ["일자리"], age: [60, 99],
    summary: "지역사회 활동형·시장형 일자리를 연결하고 활동비를 지급합니다.",
    docs: ["신분증", "참여 신청서", "건강 상태 확인서"],
    deadline: "매년 11~12월 다음 해 참여자 모집", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p12", title: "기초연금", org: "보건복지부", cat: ["금융"], age: [65, 99], incomeMax: 100,
    summary: "소득인정액이 선정기준액 이하인 어르신에게 매월 연금을 지급합니다.",
    docs: ["신분증", "통장 사본", "소득·재산 신고서"],
    deadline: "만 65세 생일이 있는 달의 한 달 전부터 신청", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p13", title: "장애인 활동지원 급여", org: "보건복지부", cat: ["건강", "돌봄"], age: [6, 64], disability: ["self"],
    summary: "활동지원사가 신체활동·가사·이동을 돕고, 이용 시간을 등급에 따라 지원합니다.",
    docs: ["장애인등록증", "활동지원 신청서", "서비스 지원 종합조사 동의"],
    deadline: "상시 접수", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p14", title: "청소년 방과후 아카데미", org: "여성가족부", cat: ["교육", "돌봄"], age: [9, 18],
    summary: "방과 후 학습·체험·급식을 제공하는 국가 돌봄 프로그램입니다.",
    docs: ["재학 증빙", "보호자 동의서"],
    deadline: "학기 시작 전 모집", link: "https://www.youth.go.kr/", linkLabel: "청소년활동정보서비스",
  },
  {
    id: "p15", title: "국민내일배움카드", org: "고용노동부", cat: ["교육", "일자리"], age: [15, 99],
    summary: "직업훈련비를 카드 한도로 지원합니다. 재직·구직 모두 신청할 수 있습니다.",
    docs: ["신분증", "카드 발급 신청서"],
    deadline: "상시 접수", link: "https://www.hrd.go.kr/", linkLabel: "HRD-Net",
  },
  {
    id: "p16", title: "통합문화이용권(문화누리카드)", org: "문화체육관광부", cat: ["문화"], age: [6, 99], incomeMax: 50,
    summary: "공연·전시·도서·여행에 쓸 수 있는 연간 문화 이용권을 지급합니다.",
    docs: ["신분증", "수급 자격 확인 동의"],
    deadline: "매년 2월부터 발급, 11월까지 사용", link: "https://www.mnuri.kr/", linkLabel: "문화누리카드",
  },
  {
    id: "p17", title: "산모·신생아 건강관리 지원", org: "보건복지부", cat: ["건강", "돌봄"], marital: ["pregnant", "child"], incomeMax: 150,
    summary: "건강관리사가 방문해 산후 회복과 신생아 돌봄을 돕습니다.",
    docs: ["출산 예정일 확인서 또는 출생증명", "건강보험료 납부확인서"],
    deadline: "출산 예정일 40일 전 ~ 출산 후 30일 이내", link: "https://www.bokjiro.go.kr/", linkLabel: "복지로",
  },
  {
    id: "p18", title: "서울 청년 대중교통비 지원", org: "서울특별시", cat: ["금융"], age: [19, 39], regions: ["서울"], incomeMax: 150,
    summary: "서울 거주 청년의 연간 대중교통 이용액 일부를 마일리지로 환급합니다.",
    docs: ["교통카드 이용내역", "주민등록초본"],
    deadline: "연 2회 모집", link: "https://youth.seoul.go.kr/", linkLabel: "서울 청년 포털",
  },
];

const SEGMENTS = [
  { name: "청소년", desc: "학습·돌봄·진로" },
  { name: "청년", desc: "주거·일자리·자산" },
  { name: "중장년", desc: "재취업·전직 훈련" },
  { name: "노년", desc: "연금·일자리·건강" },
  { name: "임신·육아 가구", desc: "출산·돌봄·산후" },
  { name: "장애인·취약계층", desc: "활동지원·문화" },
  { name: "소상공인", desc: "정책자금·경영" },
  { name: "전 국민 공통", desc: "훈련·교육 이용권" },
];

const CHIP = {
  yes: { label: "됩니다", bg: "#e4f6ec", color: "#0b7a4b" },
  unknown: { label: "확인 필요", bg: "#fff3e0", color: "#b4700a" },
  no: { label: "어렵습니다", bg: "#fdeaea", color: "#c23434" },
};

const FONTS = [
  { label: "보통", px: 16 },
  { label: "크게", px: 18 },
  { label: "더 크게", px: 21 },
];

const STATUS_LABEL = {
  student: "학생",
  jobless: "구직 중",
  worker: "재직 중",
  owner: "자영업·소상공인",
  care: "육아·휴직 중",
  retired: "은퇴·무직",
};

const MARITAL_LABEL = {
  unmarried: "미혼",
  married: "기혼(자녀 없음)",
  child: "기혼(자녀 있음)",
  pregnant: "임신 중",
  onefam: "한부모",
};

const DISABILITY_LABEL = {
  none: "없음",
  self: "본인 등록",
  family: "가족 중 등록",
};
