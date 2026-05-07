"""변호사 트랙 결과 예측 (Phase 14).

의뢰인 첫 질문 3종 ("이길 수 있나요?·얼마 받을까요?·얼마나 걸릴까요?")
에 표본 기반 통계로 답한다.

도구 4종:
- predict_sentencing       — 형사 양형 분포 (벌금·집유·실형)
- predict_civil_outcome    — 민사 인용/기각/일부인용 비율
- estimate_case_duration   — 1심·2심·3심 소요 기간
- dispute_resolution_options — 소송 vs 조정 vs 화해 비교

모든 출력은 면책 부착 + 표본 크기 명시. 통계지 보장이 아님.
"""
