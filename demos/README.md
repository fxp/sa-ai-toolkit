# 🎬 OpenClaw 全公司赋能 — Demo 部署指南

> 配合「技术·组织·工作的未来-2026-v2.pptx」Act 4 现场演示使用

---

## 快速状态

| Demo | 目录 | 状态 | 依赖 |
|------|------|------|------|
| ① CEO多Agent辩论 | `demo1-paperclip/` | ✅ 已克隆 | Docker / Node.js |
| ② Karpathy知识库 | `demo2-karpathy-kb/` | ✅ 已就绪 | Claude Code |
| ③ GStack一人军团 | `demo3-gstack/` | 📋 需安装Skill | Claude Code (Max) |
| ④ Hypothes.is标注 | `demo4-hypothesis/` | ✅ 脚本就绪 | Python + API Token |
| ⑤ 现场做PPT | `demo5-ppt-skills/` | ✅ Skill就绪 | Claude Code |
| 🎁 AutoResearch | `bonus-autoresearch/` | ✅ 已克隆 | Python + GPU |
| 🎁 Maestro测试 | `bonus-maestro/` | ✅ YAML就绪 | Maestro CLI + 模拟器 |
| 🎁 MiroFish分析 | `bonus-mirofish/` | ✅ 已克隆 | Docker + LLM API |
| 🎁 Playwright测试 | `bonus-playwright/` | ✅ 脚本就绪 | Python + Chromium |

---

## Demo ① — CEO多Agent辩论 (Paperclip)

### 部署
```bash
cd demo1-paperclip/

# 方法A: Docker（推荐）
docker compose up -d

# 方法B: 本地开发
npm install
npm run dev
```

### 访问
浏览器打开 `http://localhost:3100`

### 演示步骤
1. 创建新的"公司" → 命名为 "NewCo"
2. 添加Agent: CEO Agent / CFO Agent / CTO Agent
3. 输入议题: "是否投入500万开发SmartPet AI宠物助手？"
4. 观察Agent自主对话
5. 互动：让观众投票注入突发事件

### 配置
需要在 `.env` 中设置 LLM API Key:
```env
ANTHROPIC_API_KEY=sk-ant-xxx
# 或
OPENAI_API_KEY=sk-xxx
```

---

## Demo ② — Karpathy知识库

### 无需部署，直接使用Claude Code

```bash
cd demo2-karpathy-kb/

# 启动Claude Code
claude

# 然后对话:
> 编译知识库
> 布偶猫肾脏病的早期饮食干预方案是什么？
> 体检
```

### 文件结构
```
demo2-karpathy-kb/
├── CLAUDE.md          ← Agent行为指南（已配置好）
├── raw/               ← 原始资料（已放入示例）
│   ├── ai-customer-service-trends-2026.md
│   └── pet-nutrition-basics.md
├── wiki/              ← LLM自动编译（空，等待编译）
└── outputs/           ← AI生成的报告（空）
```

### 演示步骤
1. 展示文件结构和CLAUDE.md
2. 说"编译知识库"，观察AI自动生成wiki
3. 提一个专业问题，展示精准回答
4. 说"体检"，展示AI发现知识盲区

---

## Demo ③ — GStack一人军团

### 安装
```bash
# 在Claude Code中运行:
/install-github-skill garrytan/gstack
```

### 演示步骤
见 `demo3-gstack/SETUP.md`

核心流程: `/office-hours` → `/autoplan` → `/qa` → `/ship`

---

## Demo ④ — Agent + Hypothes.is 智能标注

### 安装依赖
```bash
cd demo4-hypothesis/
pip3 install requests anthropic
```

### 配置
```bash
export HYPOTHESIS_API_TOKEN="your_token"  # 从 https://hypothes.is/account/developer 获取
export ANTHROPIC_API_KEY="sk-ant-xxx"     # 可选，无则使用模拟数据
```

### 运行
```bash
python3 annotate-agent.py "https://example.com/article-url"
```

### 演示步骤
1. 准备5-8篇行业文章URL
2. 运行脚本，展示AI分析+自动标注
3. 打开 hypothes.is 网页端，展示标注效果
4. 展示4种标注类型: 🔴关键数据 🟡非共识 🟢策略 💬AI评论

---

## Demo ⑤ — 现场做PPT（压轴）

### 准备
`demo5-ppt-skills/SKILL.md` 已配置好公司品牌规范。

### 演示步骤
1. 在Claude Code中加载Skill:
   ```
   # 把SKILL.md放到项目目录
   cp demo5-ppt-skills/SKILL.md ./
   ```
2. 给指令:
   ```
   帮我制作一个12页的董事会汇报PPT:
   - SmartPet项目概述
   - 市场分析
   - 用户洞察
   - 技术架构
   - 下一步计划和预算
   风格：按SKILL.md中的品牌规范
   ```
3. 现场生成 → 打开展示 → 观众提修改需求 → AI实时修改

---

## 🎁 Bonus: AutoResearch

```bash
cd bonus-autoresearch/
pip3 install -e .

# 配置
export ANTHROPIC_API_KEY=sk-ant-xxx

# 启动
python3 -m autoresearchclaw "Research: 如何优化多轮对话中的意图识别准确率"
```

详细文档: `bonus-autoresearch/README.md`

---

## 🎁 Bonus: Maestro 移动端测试

```bash
# 安装 Maestro
curl -Ls "https://get.maestro.mobile.dev" | bash

# 启动Android模拟器后运行
cd bonus-maestro/
maestro test test_login.yaml
maestro test test_search_hospital.yaml
```

---

## 🎁 Bonus: MiroFish 群体智能

```bash
cd bonus-mirofish/
docker compose up -d

# 或使用在线Demo:
# https://666ghj.github.io/mirofish-demo/
```

详细文档: `bonus-mirofish/README.md`

---

## 🎁 Bonus: Playwright 前端测试

```bash
cd bonus-playwright/

# 安装
pip3 install playwright
python3 -m playwright install chromium

# 运行演示（会打开浏览器）
python3 demo-test.py

# 测试自定义网站
python3 demo-test.py https://your-demo-site.com
```

---

## 演示前检查清单

- [ ] Paperclip Docker运行正常，Dashboard可访问
- [ ] Claude Code 已登录，CLAUDE.md已加载
- [ ] Hypothes.is API Token 已配置
- [ ] Anthropic API Key 有足够余额
- [ ] GStack Skills 已安装到Claude Code
- [ ] PPT品牌Skill已就位
- [ ] 网络稳定（建议手机热点备份）
- [ ] 每个Demo提前跑过一次
- [ ] 备用方案：每个Demo准备录屏视频

## API Key 需求汇总

| 环境变量 | 用途 | 获取方式 |
|---------|------|---------|
| `ANTHROPIC_API_KEY` | Claude API | console.anthropic.com |
| `HYPOTHESIS_API_TOKEN` | Hypothes.is标注 | hypothes.is/account/developer |
| `OPENAI_API_KEY` | 备选LLM | platform.openai.com |
