# SA AI Toolkit

> Input a company name. Get a full AI training package — customized to their industry, products, and pain points.

**3 commands. 20 demos. Any industry. Any company.**

```
/gen 宁德时代              → 23 files, battery manufacturing demos
/gen China Merchants Bank  → 21 files, banking/finance demos
/customize add 5 roleplay levels  → deep-customize one demo
/present export PPT               → branded PowerPoint deck
```

---

## What Is This?

A **Claude Code plugin** for AI Solution Architects (SAs) who deliver enterprise AI training.

Instead of building demo content from scratch for each client, you type one command and get:

| Output | Content |
|--------|---------|
| **Company Profile** | Industry, revenue, employees, AI status, competitors, pain points |
| **Demo Scoring** | 20 demos ranked by relevance (auto-skips inapplicable ones) |
| **Schedule** | 120-min and 60-min presentation agendas |
| **Opening Lines** | One opening script per demo, using the company's real terminology |
| **Action Plan** | This-week / this-month / this-quarter roadmap with KPIs |
| **16-20 Demo Files** | Each demo fully customized to the company |

## The 20 Demos

### Strategy
| Demo | What It Does | Tools |
|------|-------------|-------|
| CEO Board | Multi-agent board simulation for resource allocation | Paperclip |
| MiroFish | Swarm intelligence for competitor analysis | MiroFish |
| FinRobot | AI equity research with 3-agent Chain-of-Thought | FinRobot |

### Knowledge & Training
| Karpathy KB | 3-folder knowledge base (raw→wiki→outputs) | Claude Code |
| Hypothesis | AI-powered reading annotation | Hypothesis.is |
| Roleplay | Scenario training with emotional AI characters | OpenClaw |

### AI R&D
| GStack | One-person company workflow | GStack |
| Cognitive-YOLO | LLM-driven detection architecture synthesis | Cognitive-YOLO |
| **SAM3 + TimesFM + LLM** | **Industrial AI pipeline: Perceive → Predict → Diagnose** | SAM3/TimesFM/LLM |
| Circuit-Synth | Natural language → PCB design | Circuit-Synth + KiCad |
| AutoResearch | 15-stage automated research pipeline | AutoResearchClaw |
| Kaggle Pipeline | Auto-discover competitions → deep research → compete → publish | AutoKaggle/AIDE |

### Delivery & Quality
| PPT Gen | Branded presentation in 30 seconds | Claude Skills |
| Ontology | Knowledge graph for manufacturing/finance | Neo4j |
| Maestro | Mobile app E2E testing | Maestro |
| Playwright | Browser automation testing | Playwright |

### Experience
| AI Tools | 7-tool comparison showcase | Multi-tool |
| **Org-Uplift Game** | **METR-based productivity simulation (Web app)** | Custom Web App |
| Autonomous Agent | Agent that works 24/7 with boundaries | Scheduled Tasks |
| Skill Governance | Deduplication, scoring, workflow orchestration | Catalog |

## Live Demos

### Org-Uplift Game (Web App)
An interactive browser game simulating "what if your team had 200-hour AI agents?"

Based on [METR's research](https://metr.org/notes/2026-03-19-org-uplift-game/): 3-5x productivity uplift, bottleneck shift from execution to decision-making.

```bash
cd demos/demo-metr-org-uplift
python3 -m http.server 8765
# Open http://localhost:8765
```

Features:
- 4 rounds = 2 simulated days
- Standup → Work → Agent execution → Dice roll → Round summary
- Auto-simulation mode (one-click, runs all 4 rounds automatically)
- Bottleneck tracking and final report
- Powered by BigModel GLM-5 (or offline dice mode)

### Industrial AI Pipeline
A 4-layer pipeline: **Perceive → Predict → Diagnose**

```bash
cd demos/demo-industrial-ai-pipeline

# Generate test data
python3 pipeline.py generate-data

# Run full pipeline
python3 pipeline.py run

# Run with LLM root cause analysis
BIGMODEL_API_KEY=your_key python3 pipeline.py run --llm

# Start API server
python3 pipeline.py serve --port 8770
```

```
Layer 1: Perception (SAM3 visual + SAM-Audio acoustic)
   → Detected 2 defects: scratch, coating uneven

Layer 2: Prediction (TimesFM time-series forecast)
   → Yield trend: -0.05%/day, Equipment RUL: 175 hours

Layer 3: Correlation (Ontology knowledge graph)
   → Workstation#3 → Blade#7 (overdue replacement)

Layer 4: Diagnosis (LLM root cause analysis)
   → [90%] Blade#7 worn out (72h, exceeds 48h cycle)
   → [60%] Slurry viscosity at upper spec boundary
```

## Tested With Real Companies

### 招商银行 (China Merchants Bank)
- Industry: Banking/Finance, "King of Retail Banking"
- 12万 employees, ¥3,375B revenue, AI-First strategy
- Generated: 16 demos + 5 summary files
- Key demos: Roleplay (VIP complaint), FinRobot (vs Ping An Bank), Knowledge Base (credit approval)
- Skipped: Circuit-Synth, SAM3, Cognitive-YOLO (not applicable to banking)

### 宁德时代 (CATL)
- Industry: Battery Manufacturing, 39.2% global market share
- 13万 employees, ¥4,237B revenue, 661GWh shipped
- Generated: 18 demos + 5 summary files (ALL demos applicable!)
- Key demos: SAM3 (PPB-level cell inspection), TimesFM (battery degradation), Ontology (cell→module→pack→line)
- Real terminology: 麒麟电池, CTP3.0, 神行超充, 极限制造

## Installation

### Claude Code (Terminal)
```bash
# Clone and use directly
git clone https://github.com/fxp/sa-ai-toolkit.git
cd sa-ai-toolkit

# Or install as plugin
# Copy demos/sa-ai-toolkit/skills/{gen,customize,present} to ~/.claude/skills/
```

### Quick Start
```bash
# Generate demo package for any company
/gen {company name}

# Customize content
/customize {modification instruction}

# Export deliverables
/present export PPT
```

## Project Structure

```
sa-ai-toolkit/
├── README.md                          ← You are here
├── openclaw-enterprise-sharing-outline.md  ← Full course outline (Chinese)
├── demos/
│   ├── sa-ai-toolkit/                 ← Plugin package (3 skills)
│   │   └── skills/{gen,customize,present}/
│   ├── demo-metr-org-uplift/          ← Org-Uplift Game (Web app)
│   │   ├── index.html / app.js / engine.js / scenarios.js
│   │   ├── uplift_cli.py             ← CLI backend + API server
│   │   ├── test_cli.py               ← 27 tests, all pass
│   │   └── story.md                  ← "48 Hours" narrative
│   ├── demo-industrial-ai-pipeline/   ← SAM3+TimesFM+LLM pipeline
│   │   ├── pipeline.py               ← 4-layer pipeline + API server
│   │   └── test_data/                ← 6 simulation datasets (355KB)
│   ├── windows-test-scripts/          ← 24 Windows test scripts
│   ├── outputs/招商银行/              ← CMB demo package (21 files)
│   ├── outputs/宁德时代/              ← CATL demo package (23 files)
│   └── 培训师使用手册.md              ← Trainer's guide (Chinese)
└── docs/                              ← GitHub Pages site
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | BigModel GLM-5 / Claude / any OpenAI-compatible |
| Vision | SAM3 (Meta, ICLR 2026) |
| Audio | SAM-Audio (Meta) |
| Time Series | TimesFM 2.5 (Google Research, 200M params) |
| Video | Sa2VA (ByteDance, SAM2 + LLaVA) |
| Knowledge Graph | Neo4j / Dashjoin |
| Research | AutoResearchClaw / AutoKaggle / AIDE |
| Finance | FinRobot (AI4Finance) |
| Testing | Playwright / Maestro |
| Frontend | Tailwind CSS + Vanilla JS |

## License

MIT

## Credits

Built with Claude Code. Inspired by [METR's Org-Uplift Game research](https://metr.org/notes/2026-03-19-org-uplift-game/).
