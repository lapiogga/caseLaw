"""변호사 상담 준비 키트 — case_profile 기반 마크다운 문서 자동 생성.

다른 citizen 도구 결과를 종합하여 변호사 첫 상담(보통 30분 무료~5만원 유료)을
3배 효율로 만드는 준비 자료 출력.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


def prepare_consultation_kit(
    case_profile: dict[str, str],
    *,
    triage_result: dict[str, Any] | None = None,
    statute_result: dict[str, Any] | None = None,
    cost_result: dict[str, Any] | None = None,
    similar_precedents: list[dict[str, Any]] | None = None,
    pro_bono_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """변호사 상담 준비 자료 생성.

    Args:
        case_profile: interview_facts 6턴 결과
            {"incident_summary", "counterparty", "evidence",
             "actions_taken", "desired_outcome", "quantitative"}
        triage_result: triage_dispute 응답 (선택)
        statute_result: check_statute_of_limitations 응답 (선택)
        cost_result: estimate_litigation_cost 응답 (선택)
        similar_precedents: search_precedent items 리스트 (선택, 3건 권장)
        pro_bono_result: recommend_pro_bono 응답 (선택)

    Returns:
        {
            "markdown": str,           # 그대로 인쇄·전송 가능
            "checklist_evidence": [...],
            "questions_for_lawyer": [...],
            "next_steps": [...],
            "estimated_lawyer_session_minutes": int,
            "disclaimers": [...]
        }
    """
    if not case_profile:
        raise ValueError("case_profile 비어있음 — interview_facts 6턴 먼저 완료 필요")

    md_lines: list[str] = ["# 변호사 상담 준비 자료", ""]
    md_lines.append("> 본 자료는 caselaw-mcp v0.7.0 으로 자동 생성.")
    md_lines.append("> 변호사 첫 상담을 효율화하기 위한 사전 정리본입니다.")
    md_lines.append("")

    # ── 1. 사건 요약 ──
    md_lines.append("## 1. 사건 요약")
    md_lines.append(case_profile.get("incident_summary", "_미입력_"))
    md_lines.append("")

    # ── 2. 분쟁 분류 (triage) ──
    if triage_result and triage_result.get("candidates"):
        primary = triage_result["candidates"][0]
        md_lines.append("## 2. 추정 분쟁 유형")
        md_lines.append(f"- **{primary['name']}** ({primary['domain']})")
        if primary.get("applicable_laws"):
            md_lines.append(f"- 적용 법률: {', '.join(primary['applicable_laws'])}")
        if primary.get("typical_path"):
            md_lines.append(f"- 일반 절차: {primary['typical_path']}")
        if len(triage_result["candidates"]) > 1:
            others = ", ".join(c["name"] for c in triage_result["candidates"][1:3])
            md_lines.append(f"- 다른 가능성: {others}")
        md_lines.append("")

    # ── 3. 시효 ──
    if statute_result:
        md_lines.append("## 3. 소멸시효 점검")
        md_lines.append(f"- 카테고리: {statute_result.get('category')}")
        md_lines.append(f"- 한도: {statute_result.get('period_years')}년")
        md_lines.append(f"- 경과: {statute_result.get('elapsed_years')}년")
        md_lines.append(f"- 잔여: {statute_result.get('remaining_years')}년")
        md_lines.append(f"- 상태: **{statute_result.get('status')}**")
        if statute_result.get("advice"):
            md_lines.append(f"- 조언: {statute_result['advice']}")
        md_lines.append("")

    # ── 4. 상대방 ──
    md_lines.append("## 4. 분쟁 상대방")
    md_lines.append(case_profile.get("counterparty", "_미입력_"))
    md_lines.append("")

    # ── 5. 증거 목록 ──
    md_lines.append("## 5. 보유 증거")
    md_lines.append(case_profile.get("evidence", "_미입력_"))
    md_lines.append("")

    md_lines.append("### 5.1 증거 보강 체크리스트")
    checklist = _build_evidence_checklist(triage_result)
    for item in checklist:
        md_lines.append(f"- [ ] {item}")
    md_lines.append("")

    # ── 6. 지금까지 시도 ──
    md_lines.append("## 6. 지금까지 시도한 조치")
    md_lines.append(case_profile.get("actions_taken", "_미입력_"))
    md_lines.append("")

    # ── 7. 원하는 결과 ──
    md_lines.append("## 7. 원하는 결과")
    md_lines.append(case_profile.get("desired_outcome", "_미입력_"))
    md_lines.append("")

    # ── 8. 정량 정보 ──
    md_lines.append("## 8. 정량 정보 (사건일·청구액)")
    md_lines.append(case_profile.get("quantitative", "_미입력_"))
    md_lines.append("")

    # ── 9. 비용 ──
    if cost_result:
        md_lines.append("## 9. 예상 비용")
        md_lines.append(f"- 인지대: {cost_result.get('court_fee_stamp_krw', 0):,}원")
        md_lines.append(f"- 송달료: {cost_result.get('service_fee_krw', 0):,}원")
        if cost_result.get("lawyer_fee"):
            lf = cost_result["lawyer_fee"]
            md_lines.append(
                f"- 변호사비 통상: {lf.get('low', 0):,} ~ {lf.get('high', 0):,}원 "
                f"(평균 {lf.get('typical', 0):,}원)"
            )
        if cost_result.get("small_claim_eligible"):
            md_lines.append(
                f"- ✅ 소액사건심판 가능 — 셀프 진행 시 약 "
                f"{cost_result.get('total_self_litigation_krw', 0):,}원"
            )
        md_lines.append(
            f"- 총 통상 (변호사 위임): "
            f"{cost_result.get('total_typical_with_lawyer_krw', 0):,}원"
        )
        md_lines.append("")

    # ── 10. 유사 판례 ──
    if similar_precedents:
        md_lines.append("## 10. 참고 판례 (유사 사건)")
        for i, p in enumerate(similar_precedents[:3], 1):
            md_lines.append(
                f"{i}. **{p.get('case_number')}** "
                f"({p.get('court')}, {p.get('judgment_date')}) — "
                f"{(p.get('case_name') or '')[:120]}"
            )
        md_lines.append("")

    # ── 11. 변호사에게 물어볼 질문 ──
    md_lines.append("## 11. 변호사에게 물어볼 질문 10가지")
    questions = _build_questions(triage_result, statute_result, cost_result)
    for i, q in enumerate(questions, 1):
        md_lines.append(f"{i}. {q}")
    md_lines.append("")

    # ── 12. 무료 상담처 ──
    if pro_bono_result:
        md_lines.append("## 12. 무료/저비용 상담처")
        for entry in pro_bono_result.get("national", [])[:5]:
            md_lines.append(f"- **{entry['name']}** {entry.get('phone', '')} — {entry.get('scope', '')}")
        for entry in pro_bono_result.get("regional_bar", [])[:3]:
            md_lines.append(f"- {entry['name']}: {entry['phone']} ({entry['region']})")
        if pro_bono_result.get("emergency"):
            md_lines.append("")
            md_lines.append("### 12.1 긴급")
            for entry in pro_bono_result["emergency"]:
                md_lines.append(f"- ⚠️ **{entry['name']}** {entry['phone']}")
        md_lines.append("")

    # ── 13. 면책 ──
    md_lines.append("## 13. 안내사항")
    md_lines.append("- 본 자료는 일반 안내용이며 법률 자문이 아닙니다.")
    md_lines.append("- 구체적 판단은 반드시 변호사 상담을 받으세요.")
    md_lines.append("- 시효·증거·법령은 상황에 따라 달라질 수 있습니다.")
    md_lines.append("")

    markdown = "\n".join(md_lines)

    return attach(
        {
            "markdown": markdown,
            "markdown_length": len(markdown),
            "checklist_evidence": checklist,
            "questions_for_lawyer": questions,
            "estimated_lawyer_session_minutes": _estimate_session_minutes(triage_result),
            "next_steps": _build_next_steps(statute_result, cost_result, pro_bono_result),
        },
        kinds=["standard", "ai_limitation"],
    )


def _build_evidence_checklist(triage_result: dict[str, Any] | None) -> list[str]:
    if not triage_result or not triage_result.get("candidates"):
        return [
            "사건 관련 모든 문서·메시지 백업",
            "녹음·영상·사진 원본 보관",
            "증인 연락처 확보",
            "시간 순서 메모",
        ]
    primary = triage_result["candidates"][0]
    base = list(primary.get("key_evidence", []))
    base.append("위 증거의 원본 + 사본 안전 보관 (휴대폰 분실 대비)")
    base.append("증거 입수일·출처 메모")
    return base


def _build_questions(
    triage_result: dict[str, Any] | None,
    statute_result: dict[str, Any] | None,
    cost_result: dict[str, Any] | None,
) -> list[str]:
    qs = [
        "제 사건이 변호사님이 보시기에 승소 가능성이 어느 정도인가요?",
        "변호사님은 비슷한 사건을 몇 건이나 해보셨나요?",
        "예상 소요 기간은 얼마나 될까요?",
        "수임료·성공보수 구조와 합계 금액은 어떻게 되나요?",
        "이 사건에서 가장 위험한 변수는 무엇인가요?",
    ]
    if triage_result and triage_result["candidates"]:
        primary = triage_result["candidates"][0]
        for issue in primary.get("common_issues", [])[:2]:
            qs.append(f"'{issue}' 쟁점은 어떻게 다투면 좋을까요?")
    if statute_result and statute_result.get("status") in ("imminent", "expired"):
        qs.append("시효 임박/만료 상태인데 구제 방법이 있을까요? (시효 중단·정지)")
    if cost_result and cost_result.get("small_claim_eligible"):
        qs.append("소액사건심판 셀프 진행 vs 변호사 위임 중 어느 것이 유리한가요?")

    # 보편적 질문으로 10개 채우기
    universal = [
        "합의·조정으로 해결할 가능성과 예상 합의금은 어느 정도일까요?",
        "패소했을 때의 손실(상대방 변호사비 등)과 위험은 얼마나 되나요?",
        "지금 시점에 추가로 모아야 할 증거가 있나요?",
        "내용증명 등 사전 조치를 먼저 해야 하나요, 바로 소송하는 게 나을까요?",
        "사건 진행 중 제가 직접 챙겨야 할 것이 무엇인가요?",
        "변호사님과 어떤 방식·주기로 소통하게 되나요?",
    ]
    for u in universal:
        if len(qs) >= 10:
            break
        if u not in qs:
            qs.append(u)
    return qs[:10]


def _estimate_session_minutes(triage_result: dict[str, Any] | None) -> int:
    """첫 상담 권장 시간 (분)."""
    if not triage_result or not triage_result.get("candidates"):
        return 30
    complexity = triage_result["candidates"][0].get("complexity", "medium")
    return {
        "very_low": 20,
        "low": 30,
        "medium": 45,
        "high": 60,
        "very_high": 90,
    }.get(complexity, 30)


def _build_next_steps(
    statute_result: dict[str, Any] | None,
    cost_result: dict[str, Any] | None,
    pro_bono_result: dict[str, Any] | None,
) -> list[str]:
    steps = []
    if statute_result and statute_result.get("status") in ("imminent", "expired"):
        steps.append("🚨 시효 임박/만료 — 변호사 상담을 1주일 내 잡으세요.")
    elif statute_result and statute_result.get("status") == "warning":
        steps.append("시효 1~2년 남음 — 1개월 내 변호사 상담 + 내용증명 권장.")
    else:
        steps.append("증거 보강 + 1개월 내 변호사 상담 일정 잡기.")
    if cost_result and cost_result.get("small_claim_eligible"):
        steps.append(
            "소액사건심판 가능 — 대법원 전자소송 (https://ecfs.scourt.go.kr) "
            "확인 후 셀프 vs 위임 결정."
        )
    if pro_bono_result and pro_bono_result.get("national"):
        steps.append("무료 상담처 1~2곳 먼저 이용해 분쟁의 방향성 확인.")
    steps.append("본 마크다운을 인쇄하거나 변호사에게 메일로 미리 전달.")
    return steps
