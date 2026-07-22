# Provider Intelligence

modelbroker should not route only from static provider names. Frontier model quality changes when a
lab shifts research direction, releases a new model, changes quota policy, or proves a capability in
real workloads. Public news can be useful, but only after it is converted into technical routing
signals.

## Signal: Frontier Lab Research Depth

Example signal:

> A frontier lab hires or highlights a senior theoretical-algorithm researcher.

Do not treat this as celebrity or hiring news. The useful technical interpretation is:

- the provider may be investing in deeper reasoning, search, optimization, or agent planning;
- benchmark claims for that provider should be tracked separately from coding-CLI reliability;
- routing policy should not auto-promote the provider until local evals confirm the relevant task
  class improved;
- cost optimization should keep high-reasoning tasks distinct from mechanical work, because a
  technically stronger model is only worth the premium where it actually wins.

## How to Use This in Routing

When a provider strategy signal appears:

1. Add or update a model evidence record with the source and claimed capability.
2. Require a local verification command before enabling auto-route.
3. Map the signal to a task class, such as `reasoning`, `architecture`, `coding`, `review`,
   `agent-planning`, or `tool-use`.
4. Keep cost policy separate: a provider can be technically stronger while still being wrong for
   mechanical tasks like search, scan, summarization, boilerplate, or counting.

The routing decision should be evidence-based:

```text
public signal -> model evidence record -> local eval -> task-specific routing policy
```

No public article should directly change the active route order by itself.

## Intake: 2026-07-21-181222 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **AI黑客真的来了，Hugging Face遭遇Agent自主攻击，靠自建GLM 5.2击退**
  Source: https://t.cj.sina.com.cn/articles/view/7879924061/1d5ae195d02001ghwk
  Signal: Daily Sina collector selected this with score=12, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:安全, +3:glm. Intro: 「AI 黑客」这个词，前两年一直被安全圈拿来预警，偶尔也被当成制造焦虑的标题。7 月 16 日，全球最大的 AI 模型托管平台 Hugging Face 发布了一份安全事件披露...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **OpenAI董事会主席布雷特·泰勒预测：企业将不再担心Token成本**
  Source: https://t.cj.sina.com.cn/articles/view/1826017320/6cd6d02802001tjiy
  Signal: Daily Sina collector selected this with score=11, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token, +3:openai. Intro: 围绕 Token 计费和管理产生的许多问题，主要因 AI 市场仍处于早期阶段，且商业模式尚未成熟而生。“我认为，未来的收费方式将以实际成果为依据...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **三步部署、30分钟跑通Agent：英伟达(NVDA.US)将AI智能体装进了桌面工作站**
  Source: https://finance.sina.com.cn/stock/hkstock/hkstocknews/2026-07-21/doc-iniiphzm2661460.shtml
  Signal: Daily Sina collector selected this with score=10, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体. Intro: 英伟达(NVDA.US)正在将其Agentic AI生态从云端数据中心向桌面端延伸。公司近日宣布，为搭载GB300 Blackwell Ultra GPU的旗舰工作站DGX Station推出Agent Toolkit软件工具包，用户仅需三步、约30分钟即可在本地部署并运行AI代理...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-21-203000 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **微软拟在Copilot中用月之暗面Kimi K3替换OpenAI和Anthropic的模型**
  Source: https://t.cj.sina.com.cn/articles/view/6560531064/18709c27800101cs4q
  Signal: Daily Sina collector selected this with score=16, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token, +2:kimi, +3:anthropic, +3:openai. Intro: （AI云资讯消息）自微软将Copilot Cowork切换到按Token消耗量计费的定价模式以来，成本控制便成为重中之重。而中国开源模型的推理成本要低得多，这自然引起了微软的注意...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **光电融合芯片有望让Token成本降50%，光芯片相关企业多成立于近三年**
  Source: https://cj.sina.com.cn/articles/view/7935425109/1d8fcfa5502001h60m
  Signal: Daily Sina collector selected this with score=13, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:智能体, +4:成本, +4:token. Intro: 据央视财经，当前，随着AI智能体在各行业的应用深入，Token的调用量一直保持着高速增长态势。未来三五年内，光芯片等更前沿的新技术落地，有望成为降低算力成本的探索方向...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **还在计算token成本？OpenAI董事长：AI将转向“按结果付费”**
  Source: https://finance.sina.com.cn/jjxw/2026-07-21/doc-iniiqknx2437304.shtml
  Signal: Daily Sina collector selected this with score=11, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token, +3:openai. Intro: 财联社7月21日讯（编辑 李莹）AI token的计费问题正困扰着许多企业的CFO。但OpenAI董事长Bret Taylor表示，一年之后，这个问题将不复存在...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **WAIC大咖说 | PPIO联合创始人姚欣：通过软件降低token成本的空间极大**
  Source: https://finance.sina.com.cn/roll/2026-07-21/doc-iniiqvay4877866.shtml
  Signal: Daily Sina collector selected this with score=8, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token. Intro: 对于token（词元）消耗，姚欣表示:“今年二三月的时候，token消耗的增长曲线非常陡峭，因为存在大量的尝鲜式应用。此前，token成本的下降很大程度上依靠硬件性能的提升，比如从英伟达A100、H100到B100，每一代更新性能都能大幅提升...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **威洞察 | AI Agent来了，信息化的建设思路会发生什么变化？**
  Source: https://k.sina.com.cn/article_5953740931_162dee08306703oynm.html
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: （来源：威士顿智造） 导读很多制造企业已经拥有MES、ERP、WMS、QMS等各类信息化系统。这些系统各司其职，支撑着企业生产、采购、仓储、质量等不同业务...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-22-004625 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **设计Agent Skill需权衡模型调用与用户触发成本**
  Source: https://t.cj.sina.com.cn/articles/view/2194035935/m82c654df03301gaxq
  Signal: Daily Sina collector selected this with score=16, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +3:skill, +4:成本, +4:token. Intro: 设计Agent Skill时，选模型自动调用还是用户手动触发。这背后是核心权衡。模型调用会增加Agent的上下文负载和token成本；用户调用则对使用者的认知要求更高...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **GitHub 通过每日审计与 MCP 精简，将 Agent 工作流 Token 成本最高降低 62%**
  Source: https://finance.sina.com.cn/wm/2026-06-05/doc-iniaiqkv1820658.shtml
  Signal: Daily Sina collector selected this with score=16, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +3:mcp, +4:成本, +4:token. Intro: 为了能够跨不同模型进行成本比较，团队设计了一项名为“等效 Token（ET）”的指标。整个优化闭环由两个 Agent 工作流驱动...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **光电融合芯片有望让Token成本降50%国产算力集群或成降本关键**
  Source: https://t.cj.sina.com.cn/articles/view/2258727970/m86a1742203302gzb8
  Signal: Daily Sina collector selected this with score=13, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:智能体, +4:成本, +4:token. Intro: 【#光电融合芯片有望让Token成本降50%##国产算力集群或成降本关键#】当前，随着AI智能体在各行业的应用深入，Token的调用量一直保持着高速增长态势...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **千问AI眼镜将升级为智能体眼镜：能灵活调用Skill和Agent，能全天候感知**
  Source: https://t.cj.sina.com.cn/articles/view/2118746300/7e4980bc02001n8ys
  Signal: Daily Sina collector selected this with score=13, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +3:skill. Intro: 7月17日，2026年世界人工智能大会首日，千问宣布将AI眼镜升级为智能体眼镜。升级后，眼镜可通过智能体强化服务与决策能力，并能按需调用第三方Skill和Agent...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **AI 视频杀入「Agent 时代」！一句话直出 30 秒大片，100+ Skill 随便挑**
  Source: https://k.sina.com.cn/article_5952915705_162d248f906703c7p6.html
  Signal: Daily Sina collector selected this with score=13, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +3:skill, +3:提示词, +2:视频. Intro: 搭建节点、写提示词、逐镜头生成视频、手动拼接。导演语言、分镜设计、配乐策划、画面风格，都打包成了一个可以直接调用的技能。LibTV Agent 先自动生成了两个角色的三视图，接着是一组四宫格的沙漠小镇场景资产，龟裂地面、SALOON 招牌、风化木楼...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **AI云厂商向上延伸，GMI Cloud加码Agent生产化**
  Source: https://finance.sina.com.cn/roll/2026-07-20/doc-iniinmvw9681727.shtml
  Signal: Daily Sina collector selected this with score=12, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +2:api. Intro: 7月17日至20日的2026世界人工智能大会上，AI云服务商GMI Cloud展示AI Cloud、Cluster Engine等产品，覆盖GPU资源、算力调度等环节。过去企业采购AI云服务重GPU，如今还需处理算力调度等问题。AI Cloud提供英伟达多种GPU资源用于模型训练等。Cluster Engine是算力管理平台，解决GPU有效使用问题。AgentBox是AI Agent部署平台，内置MaaS模型库，可通过单一API密钥调用170+全球顶尖大模型。这反映AI云厂商正从资源供应商向模型和应用层延伸，未来竞争重点或在助企业稳定部署模型和智能体。 (AI生成)
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
