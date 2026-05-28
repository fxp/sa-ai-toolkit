#!/usr/bin/env python3
"""
九洲电器 AI 培训 — 多 Agent 辩论 Demo
========================================
演示场景：九洲电器是否应该投入 500 万上线 AI 预测性维护系统？
三位 Agent：乐观派总经理 / CFO / CTO

用法：
  python3 demo_多Agent辩论.py                # 交互式运行（推荐培训现场使用）
  python3 demo_多Agent辩论.py --auto          # 全自动运行（适合预演）
  python3 demo_多Agent辩论.py --event A       # 注入突发事件A后运行
  python3 demo_多Agent辩论.py --rounds 3      # 只辩论3轮
"""

import os
import sys
import time
import argparse
from typing import Optional

# ── 依赖检测 ──────────────────────────────────────────────────────────────────
try:
    from zhipuai import ZhipuAI
    LLM_BACKEND = "zhipuai"
except ImportError:
    try:
        from anthropic import Anthropic
        LLM_BACKEND = "anthropic"
    except ImportError:
        print("❌ 请安装依赖：pip install zhipuai 或 pip install anthropic")
        sys.exit(1)

# ── API 配置 ──────────────────────────────────────────────────────────────────
ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── 辩论配置 ──────────────────────────────────────────────────────────────────
TOPIC = (
    "九洲电器应不应该投入 500 万元，上线一套覆盖变压器/箱变/开关柜全产品线的 "
    "AI 预测性维护系统？目标是将计划外停机率降低 40%，维保成本降低 25%。"
)

SUDDEN_EVENTS = {
    "A": "【突发！刚刚收到消息】同行竞争对手已正式宣布其 AI 预测性维护系统上线，"
         "首批覆盖变压器和开关柜，客户停机损失减少超过 2000 万元，"
         "两家原本与九洲签有意向的大客户（港口、冶金厂）已转而询价。",
    "B": "【突发！财务通报】2025 年前三季度净利润率较预算低 18%，董事会要求"
         "年内所有超过 200 万的新项目重新审批，并优先考虑削减非核心支出。"
         "公司2024年全年营收14.81亿元，增速良好，但利润未达预期。",
    "C": "【突发！政策利好】工信部刚刚发布《制造业智能化升级补贴政策》，"
         "对符合条件的 AI 工业应用项目给予最高 40% 的政府补贴，"
         "九洲子公司已获评黑龙江省数字化车间，预计直接符合申报条件，"
         "申报截止日期为三个月后。",
}

# ── Agent 角色定义 ────────────────────────────────────────────────────────────
AGENTS = {
    "总经理": {
        "emoji": "👔",
        "color": "\033[94m",  # 蓝色
        "system": """你是九洲电器的总经理张伟，风格：务实乐观的战略决策者。

你的背景：
- 在电气设备行业从业 20 年，从销售做到总经理
- 亲历了公司从手工作坊到信息化的转型，有切身体会
- 公司 2024 年营收 14.81 亿元，同比增长 22%，主力产品涵盖变压器（S11/S13/组合变）、
  美式箱变（ZNBOX）、SVG、充电桩、储能 PCS，客户覆盖电力/冶金/港口/数据中心
- 你的考核指标：营收增长、市场占有率、客户满意度

你在这个议题上的立场：
- 强烈支持上线 AI 预测性维护系统
- 核心逻辑：九洲覆盖变压器/箱变/开关柜全线，现场装机量大，数据资产天然丰富
- 你关注：这套系统能让客户（港口、冶金厂）黏性更强，打出差异化服务壁垒
- 你的顾虑：实施周期拖长会让竞争对手先跑

发言风格：
- 用商业语言，说数字和案例，不用技术术语
- 每次发言 100-150 字，言简意赅
- 偶尔反问对方来推进辩论
- 直接表达立场，不要模棱两可""",
    },
    "CFO": {
        "emoji": "💰",
        "color": "\033[93m",  # 黄色
        "system": """你是九洲电器的 CFO 李雪梅，风格：严谨务实的财务守门人。

你的背景：
- 注册会计师出身，在制造业财务做了 15 年
- 经历过公司 2019 年一次错误的 ERP 系统升级，损失 300 万，此后对大型 IT 项目格外审慎
- 公司 2024 年营收 14.81 亿，但前三季度净利润率低于预算，全年利润承压
- 你的考核指标：净利润率、现金流、投资回报率

你在这个议题上的立场：
- 不反对技术投资，但需要清晰的 ROI 论证
- 核心问题：500 万什么时候能回本？如果系统上线后误报率高，维保成本反而会增加
- 你的底线：3 年内必须看到正向现金流；可接受先做 50 台变压器的小规模试点

发言风格：
- 用财务语言：ROI、IRR、回收期、机会成本
- 喜欢提出"如果……那么……"的假设分析
- 每次发言 100-150 字
- 不要情绪化，用数据说话
- 可以提出折中方案（如小规模试点）""",
    },
    "CTO": {
        "emoji": "🔧",
        "color": "\033[92m",  # 绿色
        "system": """你是九洲电器的 CTO 王磊，风格：技术严谨但开明的工程师。

你的背景：
- 工控和嵌入式系统专家，带队开发过公司的 SCADA 系统和远程监控平台
- 公司子公司已获评黑龙江省数字化车间，有一定数据基础，但传感器覆盖率不均
- 变压器产线传感器覆盖率约 70%，箱变（ZNBOX）约 40%，GGD2 开关柜约 20%
- 你的考核指标：系统稳定性、技术债务、团队能力建设

你在这个议题上的立场：
- 技术上可行，但有明确前提条件
- 核心问题：传感器补点需要先行投入；AI 模型需要 6-12 个月历史故障数据训练
- 你的担忧：箱变和开关柜的传感器覆盖率太低，先上这两条产品线效果会很差

发言风格：
- 用技术语言：传感器覆盖率、模型精度、误报率、数字化车间
- 喜欢提出"如果数据基础不到位，再好的AI也是空话"
- 每次发言 100-150 字
- 会提出具体的技术前提条件（建议从变压器产线切入，数据最完整）
- 满足前提条件后，你是支持上线的""",
    },
}

# ── 主持人 Agent ──────────────────────────────────────────────────────────────
MODERATOR_SYSTEM = """你是一个专业的会议主持人。
你的任务是推进辩论，在3个参会者发完一轮后，
用1-2句话总结本轮的核心分歧，并提出下一轮的焦点问题。
总结要简洁，不超过 60 字。"""

# ── LLM 调用封装 ──────────────────────────────────────────────────────────────
def call_llm(system_prompt: str, messages: list, max_tokens: int = 300) -> str:
    """统一的 LLM 调用接口，支持 ZhipuAI 和 Anthropic"""

    if LLM_BACKEND == "zhipuai":
        client = ZhipuAI(api_key=ZHIPU_API_KEY)
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.85,
        )
        return response.choices[0].message.content.strip()

    elif LLM_BACKEND == "anthropic":
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text.strip()

    return "[LLM调用失败]"


def stream_print(text: str, delay: float = 0.02):
    """逐字打印，模拟打字效果"""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_separator(char: str = "─", width: int = 60):
    print(char * width)


def print_agent_header(name: str):
    agent = AGENTS[name]
    color = agent["color"]
    emoji = agent["emoji"]
    reset = "\033[0m"
    print(f"\n{color}{emoji} {name}{reset}")
    print_separator("·", 40)


# ── 辩论引擎 ─────────────────────────────────────────────────────────────────
class MultiAgentDebate:
    def __init__(self):
        self.history: list[dict] = []  # 完整辩论历史
        self.round_num: int = 0
        self.event_injected: Optional[str] = None

    def build_context(self, agent_name: str) -> list[dict]:
        """为某个Agent构建其视角的对话历史"""
        context = []

        # 添加议题背景
        context.append({
            "role": "user",
            "content": f"""【辩论议题】{TOPIC}

【公司背景】九洲电器，2024年营收14.81亿元，主力产品：变压器/美式箱变/SVG/充电桩/储能PCS，
客户覆盖电力/冶金/港口/轨道交通/数据中心，子公司已获评黑龙江省数字化车间。

【参会者】
- 总经理张伟（战略导向，倾向支持）
- CFO李雪梅（ROI导向，需要财务论证）
- CTO王磊（技术审慎，关注数据基础）

请以 {agent_name} 的身份参与辩论。每次发言保持100-150字，
直接表达你的观点，可以回应其他人的发言。"""
        })

        # 添加历史发言
        if self.history:
            history_text = "\n\n".join([
                f"【{h['speaker']}】{h['content']}"
                for h in self.history
            ])
            context.append({
                "role": "assistant",
                "content": "我已了解之前的讨论。"
            })
            context.append({
                "role": "user",
                "content": f"之前的辩论记录：\n{history_text}\n\n现在请你发言。"
            })
        else:
            context.append({
                "role": "user",
                "content": "请你首先发言，开始辩论。"
            })

        # 注入突发事件
        if self.event_injected:
            event_text = SUDDEN_EVENTS.get(self.event_injected, "")
            context[-1]["content"] += f"\n\n⚡ {event_text}\n\n请考虑这个新情况，重新评估你的立场。"

        return context

    def agent_speak(self, agent_name: str) -> str:
        """让某个Agent发言"""
        context = self.build_context(agent_name)
        system = AGENTS[agent_name]["system"]
        response = call_llm(system, context, max_tokens=250)

        self.history.append({
            "round": self.round_num,
            "speaker": agent_name,
            "content": response
        })
        return response

    def moderator_summarize(self) -> str:
        """主持人总结本轮"""
        round_speeches = [h for h in self.history if h["round"] == self.round_num]
        summary_input = "\n".join([
            f"{h['speaker']}：{h['content']}" for h in round_speeches
        ])

        messages = [{
            "role": "user",
            "content": f"第{self.round_num}轮辩论内容：\n{summary_input}\n\n请总结本轮核心分歧，并提出第{self.round_num+1}轮的焦点问题。"
        }]
        return call_llm(MODERATOR_SYSTEM, messages, max_tokens=120)

    def run_round(self, agents_order=None):
        """运行一轮辩论"""
        self.round_num += 1

        reset = "\033[0m"
        print(f"\n\n{'═' * 60}")
        print(f"  第 {self.round_num} 轮辩论")
        print(f"{'═' * 60}")

        if self.event_injected and self.round_num == 4:
            event_text = SUDDEN_EVENTS.get(self.event_injected, "")
            print(f"\n⚡ \033[91m突发事件注入：\033[0m")
            print(f"  {event_text}\n")
            time.sleep(1)

        order = agents_order or list(AGENTS.keys())

        for agent_name in order:
            print_agent_header(agent_name)
            speech = self.agent_speak(agent_name)
            stream_print(speech, delay=0.015)
            time.sleep(0.5)

        # 主持人总结
        if self.round_num < 5:  # 最后一轮不总结
            print(f"\n\n{'─' * 60}")
            print(f"🎙️  \033[95m主持人总结\033[0m")
            print_separator("·", 40)
            summary = self.moderator_summarize()
            stream_print(summary, delay=0.02)

    def generate_decision_summary(self) -> str:
        """生成最终决策摘要"""
        all_speeches = "\n".join([
            f"[第{h['round']}轮·{h['speaker']}]：{h['content']}"
            for h in self.history
        ])

        messages = [{
            "role": "user",
            "content": f"""以下是完整的辩论记录：

{all_speeches}

请生成一份结构化的决策摘要，包括：
1. 三方最终立场（各1句话）
2. 三个核心争议点
3. 一个可能的折中方案
4. 建议下一步行动（2-3条具体行动）

格式清晰，总字数控制在 250 字以内。"""
        }]

        summary_system = "你是一个专业的商业决策顾问，擅长总结多方讨论并给出可行建议。"
        return call_llm(summary_system, messages, max_tokens=400)


# ── 交互式注入事件 ───────────────────────────────────────────────────────────
def ask_for_event() -> Optional[str]:
    """提示用户选择注入的突发事件"""
    print(f"\n\n{'═' * 60}")
    print("  ⚡ 观众互动环节 — 注入突发事件！")
    print(f"{'═' * 60}")
    print("\n请现场观众投票，选择要注入的突发事件：")
    print()
    for key, event in SUDDEN_EVENTS.items():
        print(f"  [{key}] {event[:50]}...")
    print(f"  [S] 跳过，继续辩论")
    print()

    try:
        choice = input("请输入选项 (A/B/C/S): ").strip().upper()
    except EOFError:
        choice = "S"
    if choice in SUDDEN_EVENTS:
        return choice
    return None


# ── 主程序 ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="九洲电器多Agent辩论Demo")
    parser.add_argument("--auto", action="store_true", help="全自动运行（不等待用户输入）")
    parser.add_argument("--event", choices=["A", "B", "C"], help="指定注入的突发事件")
    parser.add_argument("--rounds", type=int, default=5, help="辩论轮数（默认5）")
    args = parser.parse_args()

    # 检查 API Key
    if LLM_BACKEND == "zhipuai" and not ZHIPU_API_KEY:
        print("❌ 请设置 BIGMODEL_API_KEY 环境变量")
        print("   export BIGMODEL_API_KEY='你的API Key'")
        sys.exit(1)

    # 打印标题
    print("\n" + "█" * 60)
    print("  🤖 多 Agent 辩论演示")
    print("  主题：AI 预测性维护系统投资决策")
    print("  场景：九洲电器 × 500万元 × 3位高管")
    print("█" * 60)
    print(f"\n议题：{TOPIC}\n")
    print(f"后端：{LLM_BACKEND} | 轮数：{args.rounds}")

    if not args.auto:
        try:
            input("\n按 Enter 开始辩论...")
        except EOFError:
            pass

    debate = MultiAgentDebate()

    # 第1-3轮：正常辩论
    initial_rounds = min(3, args.rounds)
    for i in range(initial_rounds):
        debate.run_round()

        if not args.auto and i < initial_rounds - 1:
            time.sleep(0.5)

    # 第4轮前：注入突发事件
    if args.rounds >= 4:
        if args.event:
            debate.event_injected = args.event
        elif not args.auto:
            event = ask_for_event()
            debate.event_injected = event
        else:
            debate.event_injected = "A"  # 自动模式默认选A

        if debate.event_injected:
            print(f"\n✅ 已注入突发事件 [{debate.event_injected}]")

        # 继续剩余轮次
        remaining = args.rounds - initial_rounds
        for _ in range(remaining):
            debate.run_round()

    # 生成决策摘要
    print(f"\n\n{'═' * 60}")
    print("  📋 AI 自动生成决策摘要")
    print(f"{'═' * 60}\n")

    summary = debate.generate_decision_summary()
    stream_print(summary, delay=0.02)

    # 技术揭秘
    print(f"\n\n{'─' * 60}")
    print("🔍 技术揭秘（30秒）")
    print("─" * 40)
    print("• 每个Agent：独立System Prompt + 独立角色设定")
    print("• 协调机制：按顺序调用，共享辩论历史")
    print("• 突发事件：注入到每个Agent的下一轮上下文中")
    print("• 决策摘要：独立的总结Agent汇总所有发言")
    print("\n→ 这不是'AI回答问题'，而是'AI替你开会'")
    print("─" * 60)

    print(f"\n✅ 演示完成！共 {debate.round_num} 轮辩论，{len(debate.history)} 次发言")


if __name__ == "__main__":
    main()
