# 문서 디렉토리 (Documentation Directory)

이 디렉토리는 프로젝트와 관련된 참고 문서 및 분석 자료를 보관합니다.

## 문서 목록

### NMPC_THEORETICAL_ANALYSIS.md

자율주행 차량 제어 시스템에서 NMPC(Nonlinear Model Predictive Control)와 기하학적 제어(Pure Pursuit) 간의 이론적 불일치에 대한 상세한 분석 문서입니다.

**⚠️ 주의**: 이 문서는 andantinow 자율주행 프로젝트에 대한 이론적 분석으로, 현재 리포지토리(timemachine-reframe-ai/backend, 심리상담 AI 백엔드)와는 직접적인 관련이 없습니다. 참고 자료로 보관됩니다.

#### 주요 내용:

1. **제어 패러다임의 충돌**: Pure Pursuit의 추종(Pursuit) 논리와 NMPC의 예측(Prediction) 논리 간의 충돌
2. **시스템 동역학 모델과 예측의 괴리**: 모델 불일치로 인한 성능 저하
3. **직진 주행 불안정성 진단**: Bang-Bang 제어 현상 및 비용 함수 문제
4. **Lookahead와 NMPC의 부조화**: 유령 타겟(Phantom Target) 현상
5. **글로벌 라인 과도 추종**: 레일(Rail) 효과 분석
6. **장애물 회피 로직 실패**: 비볼록 최적화 문제
7. **해결책**: 아키텍처 재설계 및 구현 가이드

#### 대상 독자:

- 자율주행 시스템 개발자
- 제어 이론 연구자
- NMPC 및 경로 추종 알고리즘에 관심 있는 엔지니어

---

## 현재 프로젝트 소개

이 리포지토리는 **TIMEMACHINE AI** 심리상담 백엔드 시스템입니다:

- FastAPI 기반 AI 상담 서버
- RAG (Retrieval Augmented Generation) 활용
- 13,234개의 실제 상담 데이터 기반
- 전문 심리상담사 수준의 조언 생성

자세한 내용은 프로젝트 루트의 [README.md](../README.md)를 참조하세요.
