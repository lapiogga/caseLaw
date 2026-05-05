# CODES — 전체 코드표 및 별칭 사전

> CaseLaw MCP 가 인식하는 모든 코드·별칭. LLM은 외울 필요 없고 한국어 그대로 써도 자동 변환.

## 목차

- [사건종류](#사건종류)
- [법원](#법원)
- [검색 범위](#검색-범위)
- [위원회 12종](#위원회-12종)
- [특별행정심판 4종](#특별행정심판-4종)
- [중앙부처 39종](#중앙부처-39종)
- [API target 매핑](#api-target-매핑)

---

## 사건종류

판례 검색 `case_type` 파라미터.

| 한국어 | 영문 alias | 코드 |
|---|---|---|
| 민사 | civil | 400101 |
| 형사 | criminal | 400102 |
| 특별 | special | 400103 |
| 가사 | family | 400104 |
| 행정 | administrative / admin | 400105 |
| 특허 | patent | 400106 |

```python
search_precedent("음주운전", case_type="형사")   # 동일
search_precedent("음주운전", case_type="criminal") # 동일
search_precedent("음주운전", case_type="400102")   # 동일
```

---

## 법원

판례 검색 `court` 파라미터.

| 영문 alias | 한국어 |
|---|---|
| supreme | 대법원 |
| constitutional | 헌법재판소 |
| high | 고등법원 |
| district | 지방법원 |

한국어로 직접 입력해도 그대로 사용됨 (예: `court="서울중앙지방법원"`).

---

## 검색 범위

`search_scope` 파라미터.

| 값 | 의미 |
|---|---|
| `"title"` 또는 1 | 사건명·법령명만 검색 |
| `"body"` 또는 2 | 본문(요지·전문)만 검색 |
| (생략) | 사건명+본문 통합 검색 |

---

## 위원회 12종

`search_committee_decision(committee, query)` 의 `committee` 값.

| 영문 약어 | 정식 명칭 | 한국어 별칭 (모두 인식) |
|---|---|---|
| `ppc` | 개인정보보호위원회 | 개인정보, 개인정보보호, 개인정보보호위원회 |
| `eiac` | 고용보험심사위원회 | 고용보험, 고용보험심사 |
| `ftc` | 공정거래위원회 | 공정거래, 공정거래위원회, 공정위 |
| `acr` | 국민권익위원회 | 국민권익, 권익위, 국민권익위원회 |
| `fsc` | 금융위원회 | 금융, 금융위원회, 금융위 |
| `nlrc` | 노동위원회 | 노동, 노동위, 노동위원회 |
| `kcc` | 방송미디어통신위원회 | 방송미디어통신, 방통위, 방송통신 |
| `iaciac` | 산업재해보상보험재심사위원회 | 산재, 산재보상, 산업재해 |
| `oclt` | 중앙토지수용위원회 | 토지수용, 중앙토지수용 |
| `ecc` | 중앙환경분쟁조정위원회 | 환경분쟁, 중앙환경분쟁 |
| `sfc` | 증권선물위원회 | 증권선물, 증선위, 증권선물위원회 |
| `nhrck` | 국가인권위원회 | 인권, 국가인권, 국가인권위원회 |

```python
search_committee_decision("공정위", "담합")
search_committee_decision("ftc", "담합")          # 동일
search_committee_decision("공정거래위원회", "담합") # 동일
```

---

## 특별행정심판 4종

`search_special_admin_judgment(tribunal, query)` 의 `tribunal` 값.

| 영문 alias | 정식 명칭 | 한국어 별칭 |
|---|---|---|
| `tax` | 조세심판원 | 조세, 조세심판, 조세심판원 |
| `maritime` | 해양안전심판원 | 해양, 해양안전, 해양안전심판원 |
| `acrh` | 국민권익위원회 (특별행정심판) | 권익특별, 국민권익특별 |
| `appeal` | 인사혁신처 소청심사위원회 | 소청, 소청심사, 소청심사위원회 |

> ⚠️ 특별행정심판 도메인은 OC 권한 별도 신청 필요할 수 있음.

---

## 중앙부처 39종

`search_central_dept_interpretation(dept, query)` 의 `dept` 값.

| 영문 약어 | 부처명 | 한국어 별칭 |
|---|---|---|
| `moel` | 고용노동부 | 고용노동부, 고용노동, 노동부 |
| `molit` | 국토교통부 | 국토교통부, 국토부, 국토 |
| `moef` | 재정경제부 | 재정경제부, 재경부 (목록만) |
| `mof` | 해양수산부 | 해양수산부, 해수부 |
| `mois` | 행정안전부 | 행정안전부, 행안부 |
| `me` | 기후에너지환경부 | 기후에너지환경부, 환경부 |
| `kcs` | 관세청 | 관세청 |
| `nts` | 국세청 | 국세청 (목록만) |
| `moe` | 교육부 | 교육부 |
| `msit` | 과학기술정보통신부 | 과학기술정보통신부, 과기정통부, 과기부 |
| `mpva` | 국가보훈부 | 국가보훈부, 보훈부 |
| `mnd` | 국방부 | 국방부 |
| `mafra` | 농림축산식품부 | 농림축산식품부, 농림부 |
| `mcst` | 문화체육관광부 | 문화체육관광부, 문체부 |
| `moj` | 법무부 | 법무부 |
| `mohw` | 보건복지부 | 보건복지부, 복지부 |
| `motie` | 산업통상부 | 산업통상부, 산자부 |
| `mogef` | 성평등가족부 | 성평등가족부, 여성가족부, 여가부 |
| `mofa` | 외교부 | 외교부 |
| `mss` | 중소벤처기업부 | 중소벤처기업부, 중기부 |
| `mou` | 통일부 | 통일부 |
| `moleg` | 법제처 | 법제처 |
| `mfds` | 식품의약품안전처 | 식품의약품안전처, 식약처 |
| `mpm` | 인사혁신처 | 인사혁신처 |
| `kma` | 기상청 | 기상청 |
| `khs` | 국가유산청 | 국가유산청, 문화재청 |
| `rda` | 농촌진흥청 | 농촌진흥청, 농진청 |
| `npa` | 경찰청 | 경찰청 |
| `dapa` | 방위사업청 | 방위사업청 |
| `mma` | 병무청 | 병무청 |
| `kfs` | 산림청 | 산림청 |
| `nfa` | 소방청 | 소방청 |
| `oka` | 재외동포청 | 재외동포청 |
| `pps` | 조달청 | 조달청 |
| `kdca` | 질병관리청 | 질병관리청, 질병청 |
| `kostat` | 국가데이터처 | 국가데이터처, 통계청 |
| `kipo` | 지식재산처 | 지식재산처, 특허청 |
| `kcg` | 해양경찰청 | 해양경찰청, 해경청 |
| `naacc` | 행정중심복합도시건설청 | 행정중심복합도시건설청, 행복청 |

> ⚠️ 중앙부처 1차해석 도메인도 OC 권한 별도 신청 필요할 수 있음.

---

## API target 매핑

CaseLawClient 가 내부적으로 사용하는 법제처 OpenAPI `target` 값.

### Phase 1·2 (직접 매핑)

| Tool | target |
|---|---|
| 판례 | `prec` |
| 현행법령(시행일) | `law` (lsEfYd*) |
| 헌재결정례 | `detc` |
| 법령해석례 | `expc` |
| 행정심판례 | `decc` |
| 법령용어 | `lstrm` |

### Phase 3 (enum → target 동적 매핑)

| 카테고리 | 패턴 |
|---|---|
| 위원회 12종 | `<committee>` (= `ftc`, `ppc`, `nlrc`, ...) |
| 특별행정심판 | `specialDeccTt` / `specialDeccKmst` / `specialDeccAcr` / `specialDeccAdap` |
| 중앙부처 1차해석 | `cgmExpc<Dept>` (예: `cgmExpcMoj`, `cgmExpcMoel`) |

---

## 응답 키 정규화 (참고)

법제처 응답의 한국어 키 → 영문 snake_case 변환 (자동 적용).

| 한국어 (원본) | 영문 (정규화) |
|---|---|
| 사건번호 | `case_number` |
| 사건명 | `case_name` |
| 판례일련번호 | `prec_id` |
| 헌재결정례일련번호 | `detc_id` |
| 법령해석례일련번호 | `expc_id` |
| 행정심판재결례일련번호 | `decc_id` |
| 법령용어ID | `term_id` |
| 법령용어명 | `term_name` |
| 선고일자 | `judgment_date` |
| 결정일자 | `decision_date` |
| 회신일자 | `response_date` |
| 종국일자 | `final_date` |
| 법원명 | `court` |
| 사건종류명 | `case_type` |
| 사건종류코드 | `case_type_code` |
| 판시사항 | `holdings` |
| 판결요지 | `summary` |
| 참조조문 | `referenced_articles` |
| 참조판례 | `referenced_precedents` |
| 판례내용 | `full_text` |
| 법령일련번호 / 법령ID | `law_id` |
| 법령명한글 / 법령명 | `law_name` |
| 시행일자 | `effective_date` |
| 공포일자 | `promulgation_date` |
| 소관부처명 | `ministry` |

전체 매핑은 `src/caselaw_mcp/parsers.py` 참조.
