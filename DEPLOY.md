# Deployment Guide / 部署指南

> EN first, 中文在后 ↓

---

## English

### Architecture

```
                         ┌─────────────────────────────┐
   user ───────────────▶ │  Vercel (static landing)    │   sa-ai-toolkit.vercel.app
                         │  docs/index.html aggregates │   • pure aggregation page
                         │  links + snapshots          │   • /demo-results.html viewer
                         └──────────────┬──────────────┘
                                        │ links out to isolated apps
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
   sa-industrial-ai.fly.dev   sa-karpathy-kb.fly.dev   …   sa-persona-distill.fly.dev
   (one Fly app per demo, FastAPI + static frontend, scales to 0 when idle)
            │                           │                           │
            └───────────────────────────┴───────────────────────────┘
                                        ▲ polled every 15s
                         ┌──────────────┴──────────────┐
                         │  sa-status.fly.dev          │   central health aggregator
                         │  /api/status                │
                         └─────────────────────────────┘
```

Two layers:

1. **Vercel** hosts the static landing page (`docs/`) — a pure aggregation/landing page. No serverless functions (we hit Hobby's 12-function limit, so `api/`, `server/` are excluded via `.vercelignore`).
2. **Fly.io** runs one isolated app per demo. Each demo is a FastAPI backend (`demos/<name>-py/server.py`) bundled with its static frontend (`docs/<name>/`) into a single container. Apps scale to **0 machines when idle** (`min_machines_running = 0`, `auto_stop_machines = "stop"`) → **$0 idle cost**.
3. A **status aggregator** (`status-aggregator/`, deployed as `sa-status`) polls every demo's `/health` + key API every 15s and exposes `/api/status`.

### App ↔ folder mapping

| Demo (`<name>`)    | Fly app                  | Backend folder              | Frontend folder        |
|--------------------|--------------------------|-----------------------------|------------------------|
| industrial-ai      | `sa-industrial-ai`       | `demos/industrial-ai-py/`   | `docs/industrial-ai/`  |
| ceo-agent          | `sa-ceo-agent`           | `demos/ceo-agent-py/`       | `docs/ceo-agent/`      |
| autoresearch       | `sa-autoresearch`        | `demos/autoresearch-py/`    | `docs/autoresearch/`   |
| autoresearch-vrp   | `sa-autoresearch-vrp`    | `demos/autoresearch-vrp-py/`| `docs/autoresearch-vrp/`|
| enterprise-gen     | `sa-enterprise-gen`      | `demos/enterprise-gen-py/`  | `docs/enterprise-gen/` |
| gstack             | `sa-gstack`              | `demos/gstack-py/`          | `docs/gstack/`         |
| hypothesis         | `sa-hypothesis`          | `demos/hypothesis-py/`      | `docs/hypothesis/`     |
| karpathy-kb        | `sa-karpathy-kb`         | `demos/karpathy-kb-py/`     | `docs/karpathy-kb/`    |
| maestro            | `sa-maestro`             | `demos/maestro-py/`         | `docs/maestro/`        |
| org-uplift         | `sa-org-uplift`          | `demos/org-uplift-py/`      | `docs/org-uplift/`     |
| playwright         | `sa-playwright`          | `demos/playwright-py/`      | `docs/playwright/`     |
| ppt-gen            | `sa-ppt-gen`             | `demos/ppt-gen-py/`         | `docs/ppt-gen/`        |
| sa-toolkit         | `sa-sa-toolkit`          | `demos/sa-toolkit-py/`      | `docs/sa-toolkit/`     |
| persona-distill    | `sa-persona-distill`     | `demos/persona-distill-py/` | `docs/persona-distill/`|
| (status)           | `sa-status`              | `status-aggregator/`        | —                      |

Each Fly app is reachable at `https://<app>.fly.dev`.

### Prerequisites

- [`flyctl`](https://fly.io/docs/flyctl/install/) installed and `flyctl auth login` done.
- A Vercel project linked to this repo (auto-deploys `docs/` on push to `main`).
- For `persona-distill` submit-PR feature: `GITHUB_TOKEN` set as a Fly secret (never printed):
  ```bash
  gh auth token | flyctl secrets import --app sa-persona-distill
  # then in the editor: GITHUB_TOKEN=<paste>
  ```

### Deploy a demo to Fly.io

All demos share `Dockerfile.demo` (build arg `DEMO_NAME` selects the folder). Use the helper script:

```bash
# one demo
./scripts/deploy-demo.sh industrial-ai

# everything (serial — parallel deploys race on Fly lock files)
./scripts/deploy-demo.sh --all
```

The script creates the app if missing, then runs:

```bash
env -u HTTP_PROXY -u HTTPS_PROXY flyctl deploy \
  --app sa-<name> \
  --config demos/<name>-py/fly.toml \
  --dockerfile Dockerfile.demo \
  --build-arg DEMO_NAME=<name> \
  --remote-only --depot=false --wait-timeout 600
```

### Deploy the status aggregator

```bash
env -u HTTP_PROXY -u HTTPS_PROXY flyctl deploy --config status-aggregator/fly.toml --remote-only --depot=false
```

### Deploy the Vercel landing page

Push to `main` — Vercel auto-builds from `docs/`. Routing lives in `vercel.json`:
- `/` → `/docs/index.html`
- `/status`, `/demo-results.html`, `/_snapshots/*` → corresponding `/docs/*` paths (308 redirects).

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `flyctl deploy` hangs / depot timeout | Local proxy (e.g. Clash `127.0.0.1:7890`) returns fake IP `198.18.x` | `env -u HTTP_PROXY -u HTTPS_PROXY -u DOCKER_HOST flyctl deploy --remote-only --depot=false` (the script already does this) |
| Vercel build fails: "12 Serverless Functions" | Hobby plan limit; stray `api/`, `server/` got picked up | Keep them in `.vercelignore`; no `functions` block in `vercel.json` |
| `/demo-results.html` 404 | landing links it relatively but file lives at `/docs/...` | 308 redirects in `vercel.json` (already added) |
| `git status`/`commit`/`push` hangs (iCloud `.git`) | iCloud sync stalls the repo | `git update-index --refresh`, then commit via plumbing: `git write-tree` → `git commit-tree -p HEAD -F msg` → `git update-ref HEAD <sha>` |
| Demo shows `undefined` in UI | front/back JSON shape mismatch | align `server.py` response keys with what the frontend reads (see `demos/*-py/server.py` comments) |

---

## 中文

### 整体架构

```
                         ┌─────────────────────────────┐
   用户 ──────────────▶ │  Vercel(静态汇总页)         │   sa-ai-toolkit.vercel.app
                         │  docs/index.html 汇总链接   │   • 纯落地/汇总页
                         │  + 快照查看器               │   • /demo-results.html
                         └──────────────┬──────────────┘
                                        │ 链接到各独立应用
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
   sa-industrial-ai.fly.dev   sa-karpathy-kb.fly.dev   …   sa-persona-distill.fly.dev
   (每个 demo 一个独立 Fly 应用,FastAPI + 静态前端,空闲时缩到 0)
            │                           │                           │
            └───────────────────────────┴───────────────────────────┘
                                        ▲ 每 15 秒轮询
                         ┌──────────────┴──────────────┐
                         │  sa-status.fly.dev          │   集中健康度聚合器
                         │  /api/status                │
                         └─────────────────────────────┘
```

两层:

1. **Vercel** 托管静态落地页(`docs/`)——纯汇总页,不含 serverless 函数(Hobby 套餐 12 函数上限,`api/`、`server/` 已在 `.vercelignore` 中排除)。
2. **Fly.io** 每个 demo 一个独立应用。每个 demo 是一个 FastAPI 后端(`demos/<name>-py/server.py`)+ 其静态前端(`docs/<name>/`)打进同一个容器。应用**空闲时缩到 0 台机器**(`min_machines_running = 0`、`auto_stop_machines = "stop"`)→ **空闲零成本**。
3. **状态聚合器**(`status-aggregator/`,部署为 `sa-status`)每 15 秒轮询各 demo 的 `/health` 与关键 API,暴露 `/api/status`。

应用与目录对应关系见上方英文表格(应用地址为 `https://<app>.fly.dev`)。

### 前置条件

- 安装 [`flyctl`](https://fly.io/docs/flyctl/install/) 并完成 `flyctl auth login`。
- Vercel 项目已关联本仓库(push 到 `main` 自动部署 `docs/`)。
- `persona-distill` 的提交 PR 功能需把 `GITHUB_TOKEN` 设为 Fly secret(切勿打印):
  ```bash
  gh auth token | flyctl secrets import --app sa-persona-distill
  ```

### 部署单个 demo 到 Fly.io

所有 demo 共用 `Dockerfile.demo`(用 build arg `DEMO_NAME` 选目录)。用脚本:

```bash
# 单个
./scripts/deploy-demo.sh industrial-ai

# 全部(串行——并行部署会争抢 Fly 锁文件)
./scripts/deploy-demo.sh --all
```

### 部署状态聚合器

```bash
env -u HTTP_PROXY -u HTTPS_PROXY flyctl deploy --config status-aggregator/fly.toml --remote-only --depot=false
```

### 部署 Vercel 落地页

push 到 `main` 即可,Vercel 从 `docs/` 自动构建。路由见 `vercel.json`。

### 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `flyctl deploy` 卡住 / depot 超时 | 本地代理(如 Clash `127.0.0.1:7890`)返回假 IP `198.18.x` | `env -u HTTP_PROXY -u HTTPS_PROXY -u DOCKER_HOST flyctl deploy --remote-only --depot=false`(脚本已内置) |
| Vercel 报 "12 Serverless Functions" | Hobby 上限;`api/`、`server/` 被打包进去 | 保留 `.vercelignore`,`vercel.json` 不要 `functions` 块 |
| `/demo-results.html` 404 | 落地页相对引用,文件实际在 `/docs/...` | `vercel.json` 已加 308 重定向 |
| iCloud 下 `git` 命令卡死 | iCloud 同步阻塞仓库 | 先 `git update-index --refresh`,再用底层命令提交:`git write-tree` → `git commit-tree -p HEAD -F msg` → `git update-ref HEAD <sha>` |
| 页面显示 `undefined` | 前后端 JSON 字段不一致 | 对齐 `server.py` 返回字段与前端读取(见各 `server.py` 注释) |
