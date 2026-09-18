# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 소프트웨어 개발 정보

이 소프트웨어 개발은 다음의 항목을 이용해서 개발한다.
- Python 3.14를 이용할 것
- 코드 테스트는 unittest를 활용할 것
- 순환복잡도, 함수라인수 등 측정지표는 오픈소스 도구를 이용한다.

## 프로젝트 개발 정책

### 개발 생명 주기

- 이 프로젝트는 **반드시** 분석, 설계, 구현, 테스트의 순서로 진행한다.
- 각 단계가 완료되었을때, 지정된 템플릿을 이용한 산출물이 생성되어야 한다.

### 분석 지침

- 요구사항 분석 단계 수행은 requirements-analyst 서브에이전트가 담당한다.

### 아키텍처 설계 지침

- 아키텍처 설계 단계 수행은 architecture-designer 서브에이전트가 담당한다.

### 구현지침

- 구현 단계 수행은 coding 서브 에이전트가 담당한다.
- TDD 방식으로 진행하고, TDD 스킬을 사용해야 한다.
- 다음의 품질 지표를 **반드시** 준수해야 한다.
  - 함수 라인수는 순수코드라인 50라인 이하여야 한다.
  - 함수 순환복잡도는 10 이하여야 한다.
  - 중복 코드는 7라인까지 허용한다.
  - 주석은 Doxygen 방식으로 작성하며, 20%이상 작성해야 한다.
- 함수명, 변수명은 3글자 이상 사용하고, 낙타표기법을 활용한다.

### 통합시험 지침

- 소프트웨어 통합 및 통합시험(A-SPICE SWE.5) 수행은 integration-tester 서브에이전트가 담당하며, integration-tester 스킬을 사용한다.
- 테스트 베이시스는 아키텍처 설계서(architecture-designer 산출물)의 인터페이스 정의와 통합 순서이며, 이 순서를 벗어나 임의로 통합하지 않는다.
- 구조적 커버리지 지표인 함수 커버리지와 Call 커버리지는 **반드시** 100%를 달성해야 한다.

### 시스템 테스트 지침

- SW 시스템 테스트 케이스 개발(A-SPICE SWE.6)은 sw-system-tester 서브에이전트가 담당하며, sw-system-test 스킬을 사용한다.
- 테스트 베이시스는 SW 요구사항 명세서(requirements-analyst 산출물)이며, 단위시험(SWE.4)·통합시험(SWE.5)의 시험기법·커버리지 기준과는 별개의 요구사항 기반 블랙박스 테스트임을 구분한다.

### 오케스트레이션 정책

- **Main(오케스트레이터)**: Fable 5.1, 가장 낮은 추론(effortLevel: low)으로 동작한다(`.claude/settings.json`의 `model`/`effortLevel`). Main은 이 문서의 개발 순서(분석→설계→구현→테스트)와 단계별 서브에이전트 배정을 그대로 지키고, 각 단계 작업은 직접 하지 않고 해당 서브에이전트에 위임한다.
- **필수 파이프라인 서브에이전트**(requirements-analyst, architecture-designer, detailed-designer, coding, integration-tester, sw-system-tester, aspice-cl2-auditor): 각 스킬의 판정 기준을 지킬 만한 추론 품질이 필요하므로 `model: sonnet`으로 고정한다(Main의 낮은 추론을 상속하지 않는다).
- **그 외 추가로 필요한 서브에이전트**(위 목록에 없는, Main이 작업 중 임시로 만들어 쓰는 보조 에이전트): 토큰 최적화를 위해 Sonnet 이하의 모델·추론을 사용한다.
- **반복 문제 해결**: 같은 문제가 2회 이상 반복되면 Main이 직접 반복 시도하지 말고 `problem-solver` 서브에이전트(Fable 5.1, effortLevel: medium)를 호출해 근본 원인을 진단·해결하게 한다.
- 이 정책은 `.claude/settings.json`(Main 모델/추론)과 각 `.claude/agents/*.md`의 frontmatter(서브에이전트별 모델)에 반영되어 있다. Main의 모델/추론 변경은 **다음 세션부터 적용**되며 현재 실행 중인 세션에는 즉시 적용되지 않는다.
- 시스템 테스트는 sw-system-tester가 수행한다.
- 테스트 성공률은 100%여야 한다.

### 단위 테스트 지침

- 단위 테스트는 TDD로 대체한다.
- 단위 테스트는 Branch 커버리지 100%를 달성해야 한다.
- 테스트 성공률은 100%여야 한다.

### 통합 테스트 지침

- 통합 테스트는 integration-tester가 수행한다.
- 테스트 성공률은 100%여야 한다.
