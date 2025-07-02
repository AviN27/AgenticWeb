# GrabHackPS2

# Phase 0 — Kick‑off

## 🎯 Objectives (3 h, both devs)

1. **Finalise Tech Stack & Minimal Feature Set** — 1 h
2. **Create mono‑repo `grab-agent` with pnpm workspaces** — 1 h
3. **Agree on GitFlow & Commit policy** — 1 h

---

## 1. Final Tech Stack Versions

| Layer       | Component      | Version            | Notes                       |
| ----------- | -------------- | ------------------ | --------------------------- |
| Runtime     | **Node.js**    | 20.14.0 LTS        | required for pnpm & tooling |
| Runtime     | **pnpm**       | 9.0.6              | workspace manager           |
| Runtime     | **Python**     | 3.12.2             | services & scripts          |
| API svc     | **FastAPI**    | 0.111.0            | ASGI app‑interface & router |
| Voice       | **Whisper**    | large‑v3           | local container, GGML model |
| Message Bus | **Redpanda**   | 24.1.5             | dev Kafka replacement       |
| DB          | **PostgreSQL** | 16.2‑alpine        | profiling state             |
| Cache       | **Redis**      | 7.2.4              | RedisJSON profile store     |
| Vector DB   | **Weaviate**   | 1.25.3             | hosted sandbox              |
| Infra Code  | **Terraform**  | 1.9.0              | EKS & secrets               |
| Infra Code  | **Helmfile**   | 0.162.0            | K8s releases                |
| Workflow    | **Prefect**    | 2.19.6             | data connectors             |
| LLM         | **GPT‑4o**     | 2024‑05‑13‑preview | OpenAI API                  |
| Watch SDK   | **watchOS**    | 10.4 / Swift 5.10  | Xcode 16 beta               |

### Minimal Feature Commit

* *Voice & Watch*: record → transcribe → GPT → ride‑agent → push notification.
* *Ride‑agent*: mock ETA/price, no external API.
* *GrabPay agent*: stub with success/fail toggle.
* *Error fallback* loop via GPT prompt.
* *Glasses*: Unity HUD WebSocket echo only.

---

## 2. Repository Layout (`grab-agent`)

```
grab-agent/
├── apps/
│   └── watch/          # SwiftUI project
├── services/
│   ├── app_interface/  # FastAPI WebSocket ingress
│   ├── reasoning/      # GPT wrapper + router
│   ├── ride_agent/     # domain micro‑agent (mock)
│   └── grabpay_agent/  # payment stub
├── infra/              # Terraform + Helmfile
├── ops/                # CI/CD, k6 load‑test, dashboards
├── prompts/            # prompt templates & tool schemas
└── docs/               # ADRs, diagrams, this README
```

### pnpm Workspace snippet (root `package.json`)

```json
{
  "name": "grab-agent",
  "private": true,
  "version": "0.0.0",
  "packageManager": "pnpm@9.0.6",
  "workspaces": [
    "apps/*",
    "services/*",
    "infra",
    "ops",
    "prompts"
  ],
  "engines": { "node": ">=20.14.0" }
}
```

---

## 3. Git Strategy

* **Branches**

  * `main` — protected, production deploy tags only.
  * `dev`  — integration/nightly, default branch on clone.
  * `feat/<scope>` — short‑lived feature branches.
* **Commit Convention** — *Conventional Commits* (`feat:`, `fix:`, `chore:` …) enforced by **commitlint** + **husky** pre‑commit hook.
* **PR Policy**

  * All merges to `dev` & `main` via PR, require 1 reviewer.
  * CI (lint + unit tests) must pass.
* **Tagging** — semantic version tags (`v1.0.0`) only on `main`.

---

## 4. Day 0 Task Breakdown

| Timebox | Assignee | Steps                                                                                          |
| ------- | -------- | ---------------------------------------------------------------------------------------------- |
| 10 min  | Both     | Clone empty GitHub repo `grab-agent`; set default branch `dev`.                                |
| 20 min  | Dev 1    | Add `.gitignore` (Python, Swift, Node, Terraform) & root `package.json`; install pnpm; commit. |
| 15 min  | Dev 2    | Create directory scaffold shown above + placeholder `README.md`; commit.                       |
| 15 min  | Dev 1    | Add **commitlint** (`@commitlint/config-conventional`) + **husky** pre‑commit hook.            |
| 20 min  | Dev 2    | Push **CI skeleton** `.github/workflows/ci.yml` (pnpm install → lint).                         |
| 10 min  | Both     | Verify push → CI green → PR → merge to `dev`.                                                  |

**Expected Day 0 output**

* Repo skeleton on GitHub with green CI.
* This `README_PHASE0.md` committed in `docs/`.
* Both dev laptops have pnpm 9.0.6 & Python 3.12 virtual‑env set up.
