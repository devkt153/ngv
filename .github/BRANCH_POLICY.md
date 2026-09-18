# Git 브랜치 정책

AI(Claude Code) 서브에이전트를 활용한 "바이브 코딩" 워크플로우에 맞춘, `main` 브랜치 보호 및 PR 기반 협업 정책이다.

## 브랜치 모델

- **`main`**: 항상 배포 가능한 상태를 유지하는 보호된 브랜치. 직접 커밋/푸시 금지, PR을 통해서만 병합한다.
- **작업 브랜치**: 짧게 유지하는 브랜치에서 작업하고 끝나면 PR을 올린다. 이름 규칙:
  - `feature/<주제>` — 신규 기능
  - `fix/<주제>` — 버그 수정
  - `chore/<주제>` — 설정/템플릿/스킬 등 비기능 변경 (예: `chore/add-integration-tester-skill`)
  - `docs/<주제>` — 문서만 변경

## PR 규칙

- 모든 변경은 PR을 통해서만 `main`에 들어간다(직접 push 금지).
- PR을 열면 `.github/workflows/ci.yml`의 CI 워크플로우가 자동 실행되어야 하며, **CI가 통과해야만 병합 가능**하다(Required status check).
- 병합 전 `main`과 동기화되어 있어야 한다("Require branches to be up to date before merging").
- 병합 방식은 **Squash merge**를 기본으로 한다 — AI 에이전트가 만드는 세부 커밋(사이클 단위 등)을 PR 하나당 하나의 논리적 커밋으로 정리해 `main` 히스토리를 깔끔하게 유지한다.
- 병합 후 작업 브랜치는 자동 삭제한다.
- `main`에는 force-push와 브랜치 삭제를 금지한다.
- 리뷰어 승인 필수 인원은 저장소 성격에 맞게 정한다:
  - 솔로/AI 주도 개발(현재 이 저장소): 승인 인원 0명 허용, 대신 CI 통과를 필수 게이트로 삼는다.
  - 팀 협업으로 전환 시: 최소 1명 승인(Required approving reviews)으로 상향한다.

## GitHub 저장소 설정에 적용하는 법

이 정책은 저장소의 Branch protection rule(또는 신형 Rulesets)로 적용해야 하며, 파일만으로는 강제되지 않는다. 이 세션에는 `gh` CLI가 설치되어 있지 않아 직접 적용하지 못했다. 아래 중 하나로 적용한다.

### 방법 A — GitHub 웹 UI

Settings → Branches → Add branch protection rule (Branch name pattern: `main`)에서:

- [x] Require a pull request before merging
  - Required approvals: `0` (솔로) 또는 `1`(팀)
- [x] Require status checks to pass before merging
  - Require branches to be up to date before merging
  - Status check: `Quality gates + unittest (branch coverage)` (이 워크플로우의 job 이름 — 최초 PR을 한 번 실행한 뒤에만 목록에 나타난다)
- [x] Require conversation resolution before merging
- [x] Do not allow bypassing the above settings (관리자 포함)
- [ ] Allow force pushes — 비활성(체크 해제)
- [ ] Allow deletions — 비활성(체크 해제)

Settings → General → Pull Requests에서:

- [x] Automatically delete head branches
- Default merge 방식: Squash merging만 허용(Allow merge commit / Allow rebase merging 해제)

### 방법 B — `gh` CLI (터미널에서 `gh auth login` 후 실행)

```bash
gh api -X PUT repos/devkt153/ngv/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks[strict]=true \
  -f 'required_status_checks[contexts][]=Quality gates + unittest (branch coverage)' \
  -f enforce_admins=true \
  -f required_pull_request_reviews[required_approving_review_count]=0 \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f required_conversation_resolution=true

gh repo edit devkt153/ngv --delete-branch-on-merge --enable-squash-merge \
  --enable-merge-commit=false --enable-rebase-merge=false
```

`required_status_checks[contexts][]` 값은 `.github/workflows/ci.yml`의 job 이름(`Quality gates + unittest (branch coverage)`)과 정확히 일치해야 하며, 이 워크플로우가 최소 한 번 실행된 뒤에야 GitHub가 해당 이름을 인식한다.
