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
