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

## Intake: 2026-07-22-083000 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **谷歌连发三款Gemini模型 Gemini 3.6 Flash就位，主攻AI Agent赛道**
  Source: https://t.cj.sina.com.cn/articles/view/1899684203/713ae16b001017hl2
  Signal: Daily Sina collector selected this with score=13, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:安全, +4:token. Intro: 在代码相关基准测试中，新模型减少无效代码迭代，同时升级 CBRN、网络攻击相关安全防护，抵御越狱能力进一步增强。面向高并发场景，谷歌带来轻量化 Gemini 3.5 Flash-Lite，主打极致吞吐量，输出速度可达每秒 350 Token，适配文档批量处理、智能检索等高频调用业务...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **2026/07/22 彭博社：美国加码审查中国AI模型，低成本优势正在改变全球开发者选择**
  Source: https://video.sina.com.cn/p/finance/2026-07-22/detail-iniispna7979447.d.html
  Signal: Daily Sina collector selected this with score=9, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +3:开发者, +2:视频. Intro: 1、视频来源：Bloomberg Television，主要讨论：美国拟加强对中国AI模型知识产权与蒸馏问题的审查，以及低成本中国模型对全球开发者选择的影响；2、更多宏观资讯和投资方向，...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **降低“AI成本”大势所趋！Meta要做“模型路由”，复刻OpenRouter**
  Source: https://finance.sina.com.cn/roll/2026-07-22/doc-iniirshq4759195.shtml
  Signal: Daily Sina collector selected this with score=7, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +3:路由. Intro: 据报道，为降低AI推理成本，Meta正复刻OpenRouter，开发模型路由工具Switchboard。该工具不仅用于内部降本，未来或对外发布，成为Meta开辟新收入来源的尝试...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **AI眼镜有望成为AI Agent关键入口，消费电子ETF易方达（562950）催化不断**
  Source: https://cj.sina.com.cn/articles/view/1704103183/65928d0f0200b3q0g
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: 7月22日，截至13:34，消费电子指数下跌1.2%。个股方面，澜起科技涨超2%，工业富联上涨。热门ETF方面，消费电子ETF易方达（562950）当前成交额9976.97万元，换手率6.00%...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **大厂AI入口大战升级，谁是最能干活的桌面Agent？**
  Source: https://k.sina.com.cn/article_5952915720_162d2490806704hvxc.html
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: （来源：钛媒体APP）互联网大厂间的AI入口大战打到了桌面端。据《财经》7月21日报道，阿里即将推出千问办公，把QoderWork、悟空、MuleRun三款Agent产品合并成，交给钉钉新任CEO陈宇森负责...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-22-203000 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **百度文心助手任务 Agent 登顶国际权威榜单，超越 Claude、GPT 拿下全球智能体冠军**
  Source: https://k.sina.com.cn/article_5952915720_162d2490806704hzvc.html
  Signal: Daily Sina collector selected this with score=14, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +4:评测. Intro: （来源：雷峰网）2026 年 7 月 17 日，百度文心助手任务 Agent，以最高分 94.6%、平均分 94.4% 的成绩，登顶全球工程向 AI 智能体评测榜单 PinchBench v2...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **12关通关看懂AI新闻，token与agent概念解析**
  Source: https://k.sina.com.cn/article_7879996919_m1d5af35f7033023asy.html
  Signal: Daily Sina collector selected this with score=9, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:token. Intro: “财”访一线丨什么是token、agent，token怎么出海。12关通关后，你就能看懂大部分AI新闻（新华财经）#两个AI演员比内娱待爆艺人都火#...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **美联储预警Anthropic的Mythos模型风险，自身却长达数月无法获取该模型权限**
  Source: https://finance.sina.com.cn/stock/usstock/c/2026-07-22/doc-iniistua4695594.shtml
  Signal: Daily Sina collector selected this with score=7, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:安全, +3:anthropic. Intro: 今年4月，美联储联合美国财政部召集全美各大头部银行CEO召开特别紧急会议。官方发出警示：一款全新的高阶人工智能模型，或将对美国顶级金融机构构成前所未有的网络安全威胁...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **别让你的 AI Agent 学会掩盖错误**
  Source: https://k.sina.com.cn/article_5952915705_162d248f906703flhk.html
  Signal: Daily Sina collector selected this with score=5, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent. Intro: 一条是较少的出厂内置价值观和更多的信任，模型的售出后训练是开放态度的，更依赖于使用者不断的协作调教，是支持原生进化的；另一条是更多的出厂内置价值观和有限度的信任，不支持模型售出后的原生进化...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **17th AOC｜光庭信息吕楠：利用AI Agent简化AUTOSAR系统配置的工程实践**
  Source: https://k.sina.com.cn/article_5953190046_162d6789e06703kqra.html
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: 在经典平台（CP）和自适应平台（AP）开发中，AUTOSAR基础软件（BSW）的配置由于涉及数百个参数以及复杂的跨模块依赖，历来是一项高度依赖专家经验、耗时且极易出错的系统工程...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-23-083000 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **SemiAnalysis最新对谈：OpenAI与Anthropic双雄争霸、谷歌掉队，编程吃下近半Token**
  Source: https://k.sina.com.cn/article_5953190046_162d6789e06703l1oq.html
  Signal: Daily Sina collector selected this with score=16, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:编程, +4:token, +3:anthropic, +3:openai, +2:api. Intro: （来源：网易科技）生成式 AI 产业正迎来极其关键的商业化拐点——行业重心正从粗放式的“预训练算力堆叠”，全面转向“企业级 ROI 兑现与高毛利 API 战”...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **原来 Kimi K3 叠 Claude Code 还能这么玩**
  Source: https://finance.sina.com.cn/tech/roll/2026-07-23/doc-iniiufve8336749.shtml
  Signal: Daily Sina collector selected this with score=14, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:claude code, +4:编程, +2:kimi, +3:开发者. Intro: AI 编程的竞争，正在从模型能力转向组织能力。简单来说，开发者依然使用 Claude Code 提供的开发体验，让它负责理解项目结构、读取代码文件、修改程序、执行测试以及管理整个编程流程，但真正负责推理和生成代码的模型换成了 Kimi K3...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **Claude Code集成iOS模拟器：AI直接驱动App开发与测试**
  Source: https://t.cj.sina.com.cn/articles/view/1278485542/4c34242602002b3wk
  Signal: Daily Sina collector selected this with score=11, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:claude code, +3:anthropic, +3:开发者. Intro: Anthropic于7月22日宣布，Mac桌面版Claude Code已正式集成iOS模拟器支持，该功能以公测版形式上线。开发者现在可以通过Claude Code直接构建、运行和测试iOS应用，无需依赖屏幕录制或辅助功能权限...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **极光旗下 GPTBots.ai升级客服解决方案：Audio Agent 打通企业通信线路，LINE 客服插件 2.0 同步上线**
  Source: https://finance.sina.com.cn/stock/bxjj/2026-07-23/doc-iniiusme4600645.shtml
  Signal: Daily Sina collector selected this with score=9, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:成本. Intro: 通过此次升级，企业无需改造现有IT 架构，即可将 AI Agent 能力延伸至语音与即时通讯两大核心客服渠道——更快响应、更广覆盖、更低单次服务成本...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **科大讯飞发布星火Token Factory，打造企业级AI模型智能路由与治理新底座**
  Source: https://k.sina.com.cn/article_5952915720_162d2490806704id2u.html
  Signal: Daily Sina collector selected this with score=7, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:token, +3:路由. Intro: （来源：iFLYTEK 科大讯飞集团）AI产业澎湃，越来越多企业开始将人工智能深度融入研发、生产、客服、营销等核心业务场景...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-23-100304 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **AI PPT一改就崩？MemSlides登顶抱抱脸，让Agent记住你的改稿习惯**
  Source: https://k.sina.com.cn/article_5952915720_162d2490806704i9xo.html
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: 第一版只是草稿，改稿才是主战场。很多系统已经可以从论文、产品说明或一句主题出发，生成结构完整、视觉上也不算粗糙的初稿。同一篇Transformer论文，可以被讲成基础教学课，也可以被组织成组会汇报、论文精读或技术培训...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **Claude Agent突然大更新！狂塞500个技能，网友直呼疯狂**
  Source: https://t.cj.sina.com.cn/articles/view/5703921756/153faf05c01904i9ve
  Signal: Daily Sina collector selected this with score=5, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent. Intro: 再加上监管差异和AB测试版本，直接撞上天花板。甚至，还可以直接把整套代码库规范、CI流水线配置、部署目标全塞进一个会话，让agent从写代码到上线一条龙全知道...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **对话FutureTech张梦钊：从“一个人+一群Agent”到超级个体，AI正在重塑创业范式**
  Source: https://k.sina.com.cn/article_5952915705_162d248f906703fubk.html
  Signal: Daily Sina collector selected this with score=5, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent. Intro: 随着人工智能产业进入应用深化阶段，行业关注点正在从模型能力竞争逐步转向应用价值创造。在这一趋势下，AI创业竞争的核心也正在从单纯的技术能力比拼，转向对行业认知、场景理解和商业价值创造能力的考验...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-23-182641 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **最新安全评估报告：GPT、Claude五款模型集体作弊，GPT-5.4比例最高**
  Source: https://t.cj.sina.com.cn/articles/view/5213469505/136bf3b410200164km
  Signal: Daily Sina collector selected this with score=11, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:安全, +4:评测, +3:作弊. Intro: ▲测试模型在网络安全评测中的作弊尝试频次AISI将一类行为定义为“作弊”：模型超出任务范围，或违反测试规则来达成目标。例如，通过联网搜索已有答案、攻击非目标系统、或探测评估软件漏洞来绕过任务规则等...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-24-083001 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **超 GPT-5.6 Sol：月之暗面 Kimi K3 模型 AI 智能体知识工作跑分仅次于 Claude Fable 5**
  Source: https://finance.sina.com.cn/tech/digi/2026-07-24/doc-iniiwvki4883077.shtml
  Signal: Daily Sina collector selected this with score=16, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +4:评测, +2:kimi. Intro: IT之家注：AA-Briefcase 是独立 AI 评测机构 Artificial Analysis 于 2026 年 6 月推出的全新前沿 AI 智能体（Agent）知识工作基准测试...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **把千亿大模型搬回本地，迈向Token自由**
  Source: https://t.cj.sina.com.cn/articles/view/5703921756/153faf05c01904iupi
  Signal: Daily Sina collector selected this with score=13, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:成本, +4:token. Intro: 让一台设备在本地跑起大模型，已经不算最难的部分。更难的是，当Agent要持续读取文件、保留记忆、调用工具，并在后台长期运行时，芯片能否在功耗、延迟和成本的约束下保持稳定...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **如何评估绿色算力？AI与能源双向赋能既看能效，也要看碳效**
  Source: https://finance.sina.com.cn/jjxw/2026-07-24/doc-iniiwvkm1744106.shtml
  Signal: Daily Sina collector selected this with score=12, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +2:视频. Intro: 国际能源署（IEA）相关报告指出，随着视频生成、复杂推理和AI智能体（Agent）等新一代高能耗人工智能应用加速落地，AI的能源需求正快速攀升...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **当Agent背上KPI，容联云AI商业化的破局之道**
  Source: https://t.cj.sina.com.cn/articles/view/5787529871/158f6b28f00101hxlu
  Signal: Daily Sina collector selected this with score=9, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +5:agent, +4:token. Intro: “AI的价值，不在于消耗多少Token，而在于创造多少业务结果不久前落幕的2026世界人工智能大会（WAIC）上，Agent依然是最热门的话题之一...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **AI Agent来了：大模型进入“动手时代”**
  Source: https://finance.sina.com.cn/jjxw/2026-07-24/doc-iniiwzsm1566809.shtml
  Signal: Daily Sina collector selected this with score=7, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +2:kimi. Intro: 转自：大众新闻-大众日报在过去的几年里，人工智能始终处在一个大爆发的时代。全世界的科技头部企业，都直接或间接地加入了这场“无人的战争”，从美国的GPT、Gemini、Grok，到中国的Deep Seek、豆包、千问、Kimi……算力提升幅度越来越大，模型更迭速度越来越快...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **DeepSeek将AI大模型部署成本从10万美元降至6000美元**
  Source: https://t.cj.sina.com.cn/articles/view/7879924060/m1d5ae195c03301x5zy
  Signal: Daily Sina collector selected this with score=7, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +3:deepseek. Intro: 部署一套离线AI大模型要花多少钱。过去可能是10万美元，而DeepSeek让成本降到了6000美元。这种降维打击，真正推动了技术的民主化，让无数有想法的“车库男孩”和初创企业也能触及顶尖AI，创新的火花即将迸发...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **英国金融时报：新加坡政府投资公司表示中国人工智能模型将大幅降低成本**
  Source: https://k.sina.com.cn/article_7295052889_1b2d1ac5902001uuzy.html
  Signal: Daily Sina collector selected this with score=7, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +3:anthropic. Intro: 来源：邸钞主权财富基金预期中国人工智能公司将强劲增长，但对初创企业持谨慎态度。今年2月，新加坡政府投资公司（GIC）领投了Anthropic公司300亿美元的融资...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.

## Intake: 2026-07-24-203000 Sina Signals

These are public-news intake signals, not routing decisions. Each item must become an evidence
record and pass a local eval before it changes provider order, cost policy, or fallback behavior.

- **【AI Agent展】得助客服Agent——具备全栈能力的企业级客服Agent**
  Source: https://t.cj.sina.com.cn/articles/view/5787529871/158f6b28f00101hxmk
  Signal: Daily Sina collector selected this with score=13, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +5:智能体, +3:deepseek. Intro: 产品基于自研垂类大模型融合DeepSeek系列基座模型完成智能体重构，搭建语音、文本双类业务智能体，配套智能陪练、智能质检、智能工作台三大坐席赋能Agent，搭配覆盖20+渠道的全媒体统一联络底座...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **OpenAI将GPT-Live融入CodeX，用户可语音调用AI工作**
  Source: https://t.cj.sina.com.cn/articles/view/7879924061/m1d5ae195d03301gty4
  Signal: Daily Sina collector selected this with score=12, theme=tool_implementation, lane=local_skill_or_tool. Verify exact article before use. Signals: +5:agent, +4:codex, +3:openai. Intro: 现实版贾维斯来了。openAI凌晨将gpt-Live融入codeX,现在用户可以通过语音控制和使用自己的电脑，并且调用多个ai agents完成工作#歌手排名#...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **中国大模型手握成本王牌，但最大短板仍是算力供给**
  Source: https://finance.sina.com.cn/roll/2026-07-24/doc-iniixfyi1625146.shtml
  Signal: Daily Sina collector selected this with score=10, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token, +2:api. Intro: 7月24日，瑞银证券熊玮分享对中国AI、大模型行业看法。中国模型在训练和推理成本上优势明显，头部模型训练成本或为海外1/10，API定价达海外10% - 20%，API业务毛利20% - 40%。训练效率提升归因于算法创新、策略侧重平衡及开源生态活跃；推理效率体现在架构、工程调度和基建三方面。需求端，AI应用普及，中国厂商性价比优势凸显。展望下半年，关注模型性能、变现、Token ROI。此外，还回应了中美云厂商投入差异、模型厂商格局、市值变动等问题。 (AI生成)
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **拥抱Token经济浪潮，国产算力链正在拼效率、压成本**
  Source: https://t.cj.sina.com.cn/articles/view/1651428902/626ece2602001hn18
  Signal: Daily Sina collector selected this with score=8, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +4:token. Intro: 作为Token背后的核心底层支撑，算力产业链也正面临一次深刻考验。据IDC统计，2025年全球日均Token消耗量相比上一年增长近300倍，中国企业级Token年度消耗量增长近20倍，2025年中国生成式AI模型调用量占全球35%以上，且增长速度明显快于北美市场...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
- **中国AI模型的“成本革命”：瑞银分析师详解下半年竞争格局与Kimi K3效应**
  Source: https://finance.sina.com.cn/tech/roll/2026-07-24/doc-iniixnfw9243933.shtml
  Signal: Daily Sina collector selected this with score=6, theme=claim_diligence, lane=claim_gate. Verify exact article before use. Signals: +4:成本, +2:kimi. Intro: 【TechWeb】7月24日消息，“中国模型的训练成本仅为海外龙头的十分之一，推理定价则只有10%到20%，且仍能维持20%—40%的毛利水平...
  Routing use: track as provider/cost/capability pressure; do not auto-promote without a local benchmark.
