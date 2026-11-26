<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**QuWork 일일 보상 내부 POC: 상태 확인, 확인 원장 기록, claim, 재조회**

> Version: **v0.1.0** (스크립트 2026-11-12 · Release 2026-11-24) · Status: `implemented_unverified`

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · **[한국어](README.ko.md)** · [Português (BR)](README.pt-BR.md)

상태 우선 · confirming 원장 · claim 재조회 · Token 갱신 · 다중 계정 · 선택 알림

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

</div>

---

<a id="policy"></a>
## 사용 경계

QuWork Daily는 계정 소유자가 자신의 일일 보상을 관리하기 위한 내부 POC입니다. 저장소와 배포 문서는 무료로 제공되며, 유료 재배포, 작성자 사칭, 출처 삭제 후 재배포를 허용하지 않습니다.

프로토콜 상태는 `implemented_unverified`입니다. 단위 테스트는 상태 머신의 내부 일관성만 증명하며, 실제 계정의 수령과 포인트 반영은 서버 상태 재조회로 확인해야 합니다.

---

<a id="overview"></a>
## 30초 개요

| 항목 | 설명 |
| :--- | :--- |
| **목적** | 보상 상태를 확인하고 필요할 때 claim한 뒤 다시 조회합니다. |
| **입력** | `QUWORK_ACCOUNTS` 또는 `QUWORK_ACCESS_TOKEN`. |
| **보호** | 첫 claim 전에 `confirming`을 저장하고 불확실한 결과는 재전송하지 않습니다. |
| **출력** | `query`, `done`, `claimed`, `inactive`, `pending`, `failed`. |
| **실행** | Windows, Linux, Qinglong, 수동 GitHub Actions. |
| **릴리스** | `v0.1.0` 내부 POC, [GitHub Release](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) 게시됨. |

---

<a id="what"></a>
## 무엇인가

QuWork Daily는 단일 파일 보상 실행기입니다. 상태 확인, 확인 원장 저장, claim, 상태 재조회를 순서대로 수행합니다.

`quwork_get_token.py`는 로컬 QuWork 클라이언트 SQLite를 읽기 전용으로 열고 기본적으로 자격 증명을 마스킹하며 `--export`에서만 전체 JSON을 출력합니다.

---

<a id="protocol"></a>
## 프로토콜과 재조회

| 항목 | 현재 값 |
| :--- | :--- |
| 기본 URL | `https://llm.rrzu.com` |
| 클라이언트 버전 | `1.6.0` |
| 상태 | `GET /api/user/daily-reward/status` |
| 수령 | `POST /api/user/daily-reward/claim` |
| 갱신 | `GET /api/user/refresh` |
| 환경 헤더 | `X-QurWork-Env: prod` |
| 버전 헤더 | `X-QurWork-Version: 1.6.0` |

상태에는 boolean `claimed`, `can_claim`, 숫자 `points`, 정수 `consecutive_days`, 유효한 `next_refresh_at`이 필요합니다. claim 후 재조회에서 `claimed=true`이고 `next_refresh_at`이 같아야 성공입니다.

---

<a id="credentials"></a>
## 자격 증명과 계정

| 변수 | 필수 | 설명 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 둘 중 하나 | `accessToken`이 있는 JSON 배열 또는 객체 |
| `QUWORK_ACCESS_TOKEN` | 둘 중 하나 | 단일 계정 Bearer Token |
| `QUWORK_PROXY` | 아니오 | 전체 HTTP/HTTPS 프록시 |
| `QUWORK_STATE_DIR` | 아니오 | 상태 디렉터리 |
| `QUWORK_QUERY_ONLY` | 아니오 | `1`이면 조회만 수행 |

`secret`, `session`, `data`, `auth`, `user` 내부의 token 필드도 인식합니다.

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

---

<a id="quickstart"></a>
## 빠른 시작

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

다중 계정:

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"main","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

먼저 `--query`로 상태 계약을 확인한 뒤 claim을 활성화하세요.

---

<a id="qinglong"></a>
## Qinglong

| 단계 | 작업 |
| :---: | :--- |
| 1 | `quwork_daily.py`와 선택적으로 `quwork_get_token.py` 업로드 |
| 2 | `requests>=2.25.0` 설치 |
| 3 | `QUWORK_ACCOUNTS` 또는 `QUWORK_ACCESS_TOKEN` 설정 |
| 4 | 영속 `QUWORK_STATE_DIR` 설정 |
| 5 | 처음에는 `task quwork_daily.py --query`로 확인 |

상태 디렉터리가 유지되지 않으면 갱신된 Token과 `confirming` 원장을 복구할 수 없습니다.

---

<a id="actions"></a>
## GitHub Actions

현재 저장소에는 `.github/workflows`가 없습니다. 비공개 Actions에서는 다음 Secrets를 사용할 수 있습니다.

| Secret | 필수 | 설명 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 둘 중 하나 | 다중 계정 JSON |
| `QUWORK_ACCESS_TOKEN` | 둘 중 하나 | 단일 계정 Token |
| `QUWORK_PROXY` | 아니오 | 프록시 URL |

상태 파일에는 갱신된 access token이 있으므로 일반 artifact로 업로드하지 마세요.

---

<a id="cli"></a>
## CLI 및 환경 변수

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

| 변수 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | `1`이면 `--query`와 동일 |
| `QUWORK_STATE_DIR` | 스크립트 디렉터리 | `.quwork_state.json` 저장 |
| `QUWORK_PROXY` | 비어 있음 | 계정 내 `proxy` 우선 |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | 비어 있음 | WeCom 알림 |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | 비어 있음 | PushPlus 알림 |

---

<a id="result-codes"></a>
## 결과 코드

| 결과 | 의미 | 성공 |
| :--- | :--- | :---: |
| `query` | 조회 완료 | 중립 |
| `done` | 실행 전 이미 수령 | 예 |
| `claimed` | 이번에 수령하고 재조회 완료 | 예 |
| `inactive` | 현재 수령 불가 | 중립 |
| `pending` | 결과 불확실, 다음 실행은 조회만 | 아니오 |
| `failed` | 설정, 인증, 비즈니스, 네트워크 실패 | 아니오 |

종료 코드 `0`은 failed 계정 없음, `1`은 설정 오류 또는 하나 이상의 실패를 의미합니다.

---

<a id="success"></a>
## 성공 기준

다음을 모두 만족해야 성공입니다.

1. 상태 객체가 완전하고 타입이 정확합니다.
2. 이미 `claimed=true`이거나 `claimed=false`, `can_claim=true`에서 시작합니다.
3. claim 후 재조회 결과가 `claimed=true`입니다.
4. `next_refresh_at`이 claim 전후 동일합니다.
5. 원장이 `confirming`에서 `claimed`로 바뀝니다.

단위 테스트 통과는 실제 계정의 수령이나 포인트 변화를 보장하지 않습니다.

---

<a id="tests"></a>
## 테스트

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

7개 테스트가 session 파싱, 이미 수령 시 POST 없음, claim 재조회, pending 복구, 401 1회 갱신, 명시적 거부, 상태 타입 검증을 다룹니다.

---

<a id="design"></a>
## 설계 원칙

- **상태 우선**: 알 수 없는 상태에서는 claim하지 않습니다.
- **의도 기록**: 첫 POST 전에 `confirming`을 저장합니다.
- **서버 재조회**: `claimed=true`와 동일 reset이 성공 조건입니다.
- **POST 중복 방지**: 불확실한 결과는 pending으로 유지합니다.
- **엄격한 계약**: 타입 오류는 즉시 실패합니다.
- **원자적 상태 저장**: 임시 파일, `fsync`, `os.replace`.
- **자격 증명 마스킹**: 메시지에서 Token을 제거합니다.

---

<a id="privacy"></a>
## 개인정보와 보안

`.quwork_state.json`에는 갱신된 access token이 있어 비밀번호 수준의 파일이며 Git에서 제외됩니다.

상태 파일, `QUWORK_ACCOUNTS`, `QUWORK_ACCESS_TOKEN`, `--export` 출력, 전체 JWT, Cookie, 전화번호, UID, 프록시 자격 증명을 공개하지 마세요.

---

<a id="layout"></a>
## 디렉터리 구조

```text
QuWork-Daily/
├── assets/
├── docs/
├── tests/test_quwork_daily.py
├── CHANGELOG.md
├── README.md
├── quwork_daily.py
├── quwork_get_token.py
└── requirements.txt
```

---

<a id="release"></a>
## 버전 및 릴리스

| 항목 | 현재 값 |
| :--- | :--- |
| 스크립트 버전 | `v0.1.0` |
| 스크립트 날짜 | `2026-11-12` |
| Git tag | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) |
| GitHub Release | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) (2026-11-24) |
| 프로토콜 상태 | `implemented_unverified` |

실제 계정의 `can_claim=true -> claimed=true` 재조회, 포인트 변화 확인, reset 불변, 실패 상태 회귀 증거, `.quwork_state.json` 제외가 릴리스 조건입니다.

---

<a id="disclaimer"></a>
## 면책 조항

이 프로젝트는 자신의 계정 유지 목적으로 사용하세요. 사용 전 계정, 서비스 약관, 지역 규칙을 확인해야 합니다. 계정 제한, 포인트 변화, API 변경, 네트워크 실패, 타사 배포 결과는 보장하지 않습니다.

---

<a id="donate"></a>
## 후원 QR 코드

후원은 자발적이며 코드, 문서, Issue 처리에 영향을 주지 않습니다.

<div align="center">
<table>
<tr>
<td align="center"><strong>WeChat</strong><br /><img src="../assets/donate-wechat.png" width="260" alt="WeChat 후원 QR" /></td>
<td align="center"><strong>Alipay</strong><br /><img src="../assets/donate-alipay.jpg" width="260" alt="Alipay 후원 QR" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## 피드백 및 Star History

- [Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [변경 로그](../CHANGELOG.md)

마스킹된 로그, 결과, HTTP 상태, 재현 단계를 포함하세요. Token, Cookie, 계정 DB, `.quwork_state.json`은 공개하지 마세요.

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
