/**
 * Preset scenarios for the Org-Uplift Game
 */
const Scenarios = {
  metr: {
    id: 'metr',
    name: 'METR原始场景',
    description: 'AI安全研究团队评估2026模型能力',
    players: [
      { name: 'Alice', role: '研究经理', project: '模型能力评估框架设计', color: '#3B82F6' },
      { name: 'Bob', role: '研究员', project: 'Agent自主性基准测试', color: '#10B981' },
      { name: 'Carol', role: '研究员', project: '安全对齐评估工具开发', color: '#F59E0B' },
    ],
    context: '你们是METR（Model Evaluation & Threat Research）的研究团队。当前任务是评估2026年最新的AI模型在自主任务执行方面的能力边界。你们拥有200小时时间窗口的AI Agent辅助工作。',
    aiParams: {
      timeHorizon: 200,
      speedMultiplier: 2,
    },
  },

  newco: {
    id: 'newco',
    name: 'NewCo客服产品',
    description: '创业团队从0到MVP，构建AI客服产品',
    players: [
      { name: '张伟', role: '产品经理', project: '客服产品PRD和原型设计', color: '#3B82F6' },
      { name: '李娜', role: '全栈工程师', project: 'MVP后端API和前端开发', color: '#10B981' },
      { name: '王鹏', role: 'AI工程师', project: '客服对话模型微调和集成', color: '#F59E0B' },
    ],
    context: '你们是NewCo的核心创始团队，正在构建一款面向中小企业的AI智能客服产品。目标是在2天内完成从概念到可演示MVP的全流程。你们拥有200小时时间窗口的AI Agent辅助。',
    aiParams: {
      timeHorizon: 200,
      speedMultiplier: 2,
    },
  },

  enterprise: {
    id: 'enterprise',
    name: '企业数字化转型',
    description: '大型制造企业的AI赋能POC',
    players: [
      { name: '刘总', role: '数字化负责人', project: '制定AI落地路线图和ROI评估', color: '#3B82F6' },
      { name: '赵工', role: '数据工程师', project: '产线数据接入和知识图谱构建', color: '#10B981' },
      { name: '孙莉', role: '业务分析师', project: '缺陷检测模型POC和业务对接', color: '#F59E0B' },
      { name: '周强', role: '安全工程师', project: 'AI系统安全评估和合规方案', color: '#EF4444' },
    ],
    context: '你们是一家大型制造企业的数字化转型团队。管理层要求在2天内拿出AI赋能产线的POC方案和初步成果。重点方向：缺陷检测、知识图谱、智能运维。你们拥有200小时时间窗口的AI Agent。',
    aiParams: {
      timeHorizon: 200,
      speedMultiplier: 2,
    },
  },

  // ── Simulation scripts: pre-scripted content for auto-play ──
  _simScripts: {
    newco: {
      // standups[round][playerIdx] = { done, plan, blockers }
      standups: [
        [ // Round 1
          { done: '', plan: '完成PRD初稿，定义核心用户场景和功能优先级', blockers: '需要竞品数据支撑决策' },
          { done: '', plan: '搭建项目脚手架，配置CI/CD，设计API schema', blockers: '等PM确定功能范围' },
          { done: '', plan: '选定基础模型，准备微调数据集，搭建训练环境', blockers: '需要客服对话样本数据' },
        ],
        [ // Round 2
          { done: 'PRD初稿完成，竞品分析报告已生成', plan: '设计原型图，准备用户测试脚本', blockers: '需要工程确认技术可行性' },
          { done: '项目脚手架搭建完成，API schema v1就绪', plan: '实现核心API：对话管理、工单创建、用户认证', blockers: 'AI模型API接口规格未定' },
          { done: '基础模型选定(GLM-5)，微调数据集准备中', plan: '完成模型微调，部署推理服务，编写API适配层', blockers: '训练数据质量待验证' },
        ],
        [ // Round 3
          { done: '原型图v1完成，收到团队反馈', plan: '根据反馈修订原型，编写演示脚本，准备投资人pitch', blockers: '需要真实demo环境' },
          { done: '核心API已实现，认证和对话管理可用', plan: '集成AI模型API，实现前端聊天界面，对接工单系统', blockers: 'AI模型推理延迟需优化' },
          { done: '模型微调完成，推理服务部署中', plan: '优化推理延迟(<2s)，实现多轮对话记忆，测试边界情况', blockers: '某些客服场景模型幻觉较多' },
        ],
        [ // Round 4
          { done: '演示脚本就绪，pitch deck初稿完成', plan: '录制演示视频，最终review所有交付物，准备发布', blockers: '前端还有几个UI bug' },
          { done: '前端聊天界面可用，AI集成完成', plan: '修复UI bug，性能优化，部署到演示环境，端到端测试', blockers: '部署环境SSL证书问题' },
          { done: '推理延迟优化到1.5s，多轮对话正常', plan: '压测并发场景，修复幻觉问题的guardrails，写技术文档', blockers: '并发超过50路时推理变慢' },
        ],
      ],
      // actions[round][playerIdx][hour] = { playerAction, agentTask }
      actions: [
        [ // Round 1
          [ // 张伟 (PM)
            { playerAction: '梳理用户需求，定义核心场景', agentTask: '调研AI客服行业Top5竞品，整理技术架构和定价策略对比表' },
            { playerAction: '审查Agent竞品分析报告', agentTask: '基于竞品分析，生成NewCo AI客服的差异化定位文档' },
            { playerAction: '和团队讨论技术方案', agentTask: '撰写PRD初稿：包含用户画像、功能列表、优先级排序' },
            { playerAction: '审查PRD，标注需修改的部分', agentTask: '' },
            { playerAction: '确定MVP功能范围，通知团队', agentTask: '生成项目时间线甘特图（2天倒排）' },
          ],
          [ // 李娜 (工程师)
            { playerAction: '选择技术栈：Next.js + FastAPI + PostgreSQL', agentTask: '搭建Next.js + FastAPI + PostgreSQL项目脚手架，配置Docker开发环境' },
            { playerAction: '审查脚手架代码，调整目录结构', agentTask: '设计RESTful API schema：对话管理、工单CRUD、用户认证端点' },
            { playerAction: '讨论API设计，确认与AI模型的接口', agentTask: '实现用户认证API（JWT + 注册/登录/刷新token）' },
            { playerAction: '测试认证API，发现一个bug', agentTask: '修复认证API的token刷新bug，并编写单元测试' },
            { playerAction: '配置CI流水线', agentTask: '配置GitHub Actions CI：lint + test + build' },
          ],
          [ // 王鹏 (AI工程师)
            { playerAction: '评估可选基础模型：GLM-5/DeepSeek/Qwen', agentTask: '对比GLM-5、DeepSeek-V3、Qwen-3在客服对话场景的benchmark表现' },
            { playerAction: '审查benchmark结果，决定使用GLM-5', agentTask: '收集客服对话训练数据：从公开数据集筛选中文客服对话样本5000条' },
            { playerAction: '审查数据质量，标注需要清洗的部分', agentTask: '清洗训练数据：去重、格式化、质量过滤，生成训练/验证集' },
            { playerAction: '配置训练环境参数', agentTask: '编写GLM-5微调脚本：LoRA配置、数据加载、训练循环' },
            { playerAction: '启动训练（Agent夜间运行）', agentTask: '启动模型微调训练（预计6小时），设置checkpoint和早停策略' },
          ],
        ],
        [ // Round 2
          [
            { playerAction: '审查PRD反馈，开始设计原型', agentTask: '用Figma设计客服聊天界面原型：对话窗口、工单面板、管理后台' },
            { playerAction: '审查原型，标注修改意见', agentTask: '根据修改意见调整原型，补充错误状态和空状态设计' },
            { playerAction: '和工程师对齐技术实现细节', agentTask: '' },
            { playerAction: '编写用户测试脚本（5个核心场景）', agentTask: '生成用户测试问卷模板，覆盖首次使用、创建工单、多轮对话等场景' },
            { playerAction: '准备投资人pitch的核心数据', agentTask: '整理AI客服市场规模数据和TAM/SAM/SOM分析' },
          ],
          [
            { playerAction: '实现对话管理API', agentTask: '实现对话管理API：创建对话、发送消息、获取历史记录，含WebSocket实时推送' },
            { playerAction: '审查对话API代码，处理边界情况', agentTask: '实现工单管理API：创建、分配、状态流转、评论功能' },
            { playerAction: '和AI工程师对接模型API接口', agentTask: '编写AI模型调用适配层：请求封装、超时处理、降级策略' },
            { playerAction: '联调测试，修复接口不一致问题', agentTask: '实现前端聊天组件：消息列表、输入框、打字指示器、消息状态' },
            { playerAction: '审查前端组件，调整样式细节', agentTask: '' },
          ],
          [
            { playerAction: '检查训练结果，分析loss曲线', agentTask: '评估微调后模型效果：计算BLEU/ROUGE分数，人工抽检20条回复质量' },
            { playerAction: '分析评估结果，确认模型可用', agentTask: '部署模型推理服务：FastAPI + vLLM，配置GPU资源和并发控制' },
            { playerAction: '和后端对接API接口规格', agentTask: '编写推理API适配层：流式输出、对话历史管理、安全过滤' },
            { playerAction: '联调测试，发现延迟过高(3.5s)', agentTask: '优化推理延迟：启用KV-cache、调整batch size、量化模型至INT8' },
            { playerAction: '验证优化效果，延迟降到1.8s', agentTask: '' },
          ],
        ],
        [ // Round 3
          [
            { playerAction: '根据团队反馈修订原型', agentTask: '生成产品演示脚本：3个核心场景的话术和操作步骤' },
            { playerAction: '审查演示脚本，调整节奏', agentTask: '制作投资人pitch deck：12页PPT，含市场数据和技术架构图' },
            { playerAction: '审查pitch deck内容', agentTask: '' },
            { playerAction: '和团队排练演示流程', agentTask: '撰写产品landing page文案：标题、卖点、CTA' },
            { playerAction: '最终确认演示环境可用', agentTask: '' },
          ],
          [
            { playerAction: '集成AI推理API到后端', agentTask: '实现后端-AI模型完整集成：消息路由、上下文管理、错误处理' },
            { playerAction: '端到端测试对话流程', agentTask: '实现前端管理后台：对话列表、工单看板、数据仪表盘' },
            { playerAction: '审查管理后台，修复排版问题', agentTask: '编写端到端测试：Playwright自动化覆盖5个核心用户流程' },
            { playerAction: '运行E2E测试，修复2个失败用例', agentTask: '部署到Vercel(前端) + Railway(后端)演示环境' },
            { playerAction: '验证演示环境，确认SSL和域名', agentTask: '' },
          ],
          [
            { playerAction: '添加模型输出的安全guardrails', agentTask: '实现内容安全过滤：敏感词检测、输出格式校验、幻觉检测规则' },
            { playerAction: '审查安全规则，补充边界情况', agentTask: '实现多轮对话记忆管理：对话摘要、长程依赖保持、上下文窗口控制' },
            { playerAction: '测试复杂多轮对话场景', agentTask: '压测推理服务：模拟50/100并发，记录延迟和错误率' },
            { playerAction: '分析压测结果，确认50并发稳定', agentTask: '编写AI模型技术文档：架构图、API说明、性能指标、已知限制' },
            { playerAction: '审查技术文档', agentTask: '' },
          ],
        ],
        [ // Round 4
          [
            { playerAction: '最终审查所有交付物清单', agentTask: '录制3分钟产品演示视频脚本（旁白+操作步骤）' },
            { playerAction: '按脚本录制演示视频', agentTask: '' },
            { playerAction: '审查视频，确认质量', agentTask: '生成项目总结报告：完成了什么、技术架构、性能指标、下一步计划' },
            { playerAction: '审查总结报告，添加管理层关心的ROI数据', agentTask: '' },
            { playerAction: '发布交付物，通知stakeholders', agentTask: '生成2天工作复盘：完成任务清单、AI Agent贡献度分析、瓶颈归因' },
          ],
          [
            { playerAction: '修复前端3个UI bug', agentTask: '修复聊天界面消息顺序错乱bug，添加消息发送失败重试机制' },
            { playerAction: '验证bug修复，继续下一个', agentTask: '优化首屏加载性能：代码分割、图片懒加载、API请求合并' },
            { playerAction: '性能测试，确认首屏<2s', agentTask: '部署最终版本到演示环境，配置监控和告警' },
            { playerAction: '端到端回归测试', agentTask: '生成API文档：Swagger/OpenAPI规格，含请求示例和错误码说明' },
            { playerAction: '最终确认一切就绪', agentTask: '' },
          ],
          [
            { playerAction: '修复幻觉guardrails的误拦截问题', agentTask: '调优内容过滤规则：降低误拦截率，分析被拦截的正常回复模式' },
            { playerAction: '验证过滤调优效果', agentTask: '添加A/B测试框架：支持不同prompt策略的对比实验' },
            { playerAction: '设置baseline实验', agentTask: '编写模型运维手册：部署流程、监控指标、常见问题排查' },
            { playerAction: '审查运维手册', agentTask: '生成最终性能报告：延迟P50/P95/P99、吞吐量、错误率、成本估算' },
            { playerAction: '归档所有文档和代码', agentTask: '' },
          ],
        ],
      ],
    },
  },

  custom: {
    id: 'custom',
    name: '自定义场景',
    description: '空白模板，自行配置',
    players: [
      { name: '玩家1', role: '角色', project: '项目描述', color: '#3B82F6' },
    ],
    context: '',
    aiParams: {
      timeHorizon: 200,
      speedMultiplier: 2,
    },
  },
};
