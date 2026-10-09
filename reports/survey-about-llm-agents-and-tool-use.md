# A Comprehensive Survey on LLM Agents and Tool Use: Architectures, Benchmarks, Security, and Emerging Trends

## TL;DR
- LLM agents synergize reasoning and acting through interleaved paradigms like ReAct [1], self-supervised tool integration via Toolformer [2], and retriever-aware API writing models such as Gorilla [3].
- Realistic interactive environments (e.g., WebArena [4], AgentBench [5], FinToolBench [6]) reveal major capability gaps in long-horizon reasoning, active exploration, and failure recovery [4][5].
- Recent unified evaluation frameworks demonstrate that benchmark outcomes are heavily influenced by hidden framework scaffolding and environment volatility rather than base capabilities alone [7].
- Security analyses show that recursive agentic loops and external tool interactions introduce severe threat surfaces, most notably indirect prompt injection and tool-mediated control-flow hijacking [8][9].
- Emerging trends focus on self-evolving tool learning from zero data [10], agentic skill encapsulation [11], and balancing the exponential resource consumption and latency of recursive workflows [12].

## Background
Large Language Model (LLM) agents represent a paradigm shift from static, single-turn query-response models to autonomous systems capable of planning, memory management, and executing external tool calls [12]. Grounded in foundational frameworks like ReAct—which interleaves verbal reasoning traces with executable actions—agents can dynamically interact with knowledge bases and environments to mitigate hallucination and error propagation [1]. Early foundational work also established self-supervised tool integration (Toolformer) [2] and retriever-augmented API generation (Gorilla) [3]. As LLMs evolve into autonomous agents capable of operating across web applications, code interpreters, financial platforms, and multi-agent workflows, understanding their architectures, evaluation methodologies, and security threat surfaces has become critical [13][14][8].

## Architectures and Paradigms for Tool Integration
The transition from static text generation to interactive tool use requires architectures that bridge natural language understanding with precise programmatic execution. The ReAct framework addresses this by prompting LLMs to generate alternating reasoning traces and task-specific actions. On interactive decision-making benchmarks like ALFWorld and WebShop, ReAct outperforms conventional imitation and reinforcement learning baselines with minimal in-context examples [1].

To reduce reliance on extensive human-annotated API data, Toolformer demonstrated that LLMs can teach themselves to use tools in a self-supervised manner by deciding which APIs to call, formulating arguments, and integrating API responses into future token prediction [2]. Similarly, to address the challenge of massive and constantly updating API repositories, Gorilla integrates document retrieval with fine-tuned LLaMA architectures to write accurate API calls and mitigate hallucination compared to prompting base models directly [3]. Beyond standard tool calls, recent work has formalized agentic skills as reusable procedural capabilities that package procedural knowledge with applicability conditions and execution policies across diverse operational environments [11].

## Interactive Environments and Multi-Dimensional Benchmarking
Evaluating LLM agents requires shifting from static datasets to interactive, closed-loop environments that measure end-to-end task completion [14]. WebArena introduced a realistic, self-hostable web environment spanning e-commerce, social forums, and collaborative software development, utilizing outcome-based programmatic verification rather than string matching [4]. Results showed that top models like GPT-4 achieved an end-to-end task success rate of 14.41%, compared to 78.24% for humans. The authors hypothesize that limitations in active exploration and failure recovery may contribute to the performance gap, as current LLMs often struggle with long-horizon reasoning and complex state tracking in realistic environments [4].

Similarly, AgentBench evaluated 29 models across 8 distinct environments, revealing that persistent failures in long-term reasoning, decision-making, and instruction-following are the primary limiting factors for current LLM-based agents [5]. More recent benchmarks extend into specialized domains, such as FinToolBench, which evaluates financial tool learning agents across 760 specialized APIs [6]. Comprehensive surveys on agent benchmarking highlight a structural transition toward realistic simulation environments, while identifying persistent challenges in task coverage, evaluation metric fragmentation, and high reproduction costs [14].

## Unified Evaluation and Methodological Challenges
A major challenge in agent evaluation is decoupling intrinsic LLM capabilities from framework-induced artifacts. A recent unified framework analyzing 400K rollouts across 7 agent benchmarks demonstrated that benchmark outcomes are materially shifted by hidden scaffold choices and environment volatility [7]. This highlights that reported scores often conflate base model capabilities with benchmark-specific implementation choices, parsers, and execution environments [7].

Furthermore, because LLM agents are inherently stochastic, measuring reliability requires executing identical tasks multiple times to observe outcome variance, introducing substantial evaluation overhead [15]. Evaluating multi-turn or long-horizon scenarios manually is costly and difficult to scale, whereas offline evaluations lack the open-ended nuance required for runtime agent responses [15]. Emerging self-evolving paradigms, such as the Tool-R0 framework, attempt to bypass data scarcity by enabling tool-learning agents to train via self-play reinforcement learning from zero data [10].

## Security Threat Surfaces and Efficiency Trade-offs
Recursive agentic loops and external tool integrations introduce significant security vulnerabilities and efficiency bottlenecks. A systematic survey of 247 papers categorized LLM agent security around information flow, delegated authority, and persistent state across inputs, planning, tool execution, and memory [8]. Prompt injection and indirect prompt injection were identified as the most visible and structurally influential threat families [8]. Furthermore, interaction with untrusted APIs and external content exposes agents to supply chain threats, where malicious web observations alter agent behavior and final outputs [9]. Many internal execution states remain implicit, making security issues difficult to detect in a timely manner [9].

Concurrently, agentic systems consume exponentially more resources than standard LLMs due to recursive memory management, iterative tool usage, and multi-step planning, resulting in prohibitive latency and context window saturation [12]. Recent efficiency analyses emphasize that memory evaluations often focus narrowly on retrieval relevance while neglecting marginal utility, lifecycle write costs, and update frequencies [12].

## Trends and open problems
Recent research highlights several open problems and evolving trajectories in LLM agent development. Key shifts include moving beyond isolated API calls toward agentic skill encapsulation [11] and self-evolving tool learning via reinforcement learning without initial datasets [10]. Unsolved challenges include developing compositional defenses against indirect prompt injection [8], establishing standardized evaluation frameworks that isolate environmental volatility from base model capabilities [7], and optimizing the cost-performance trade-off in long-horizon, stateful multi-agent workflows [12].

## References
[1] ReAct: Synergizing Reasoning and Acting in Language Models. arxiv. https://arxiv.org/abs/2210.03629 (2023-03-10)
[2] Toolformer: Language Models Can Teach Themselves to Use Tools. arxiv. https://arxiv.org/abs/2302.04761 (2023-02-09)
[3] Gorilla: Large Language Model Connected with Massive APIs. arxiv. https://arxiv.org/abs/2305.15334 (2023-05-25)
[4] WebArena: A Realistic Web Environment for Building Autonomous Agents. web. https://arxiv.org/abs/2307.13854 (2023-07-25)
[5] AgentBench: Evaluating LLMs as Agents. hf-search. https://huggingface.co/papers/2308.03688 (2023-08-07)
[6] FinToolBench: Evaluating LLM Agents for Real-World Financial Tool Use. hf-search. https://huggingface.co/papers/2603.08262 (2026-03-09)
[7] A Unified Framework for the Evaluation of LLM Agentic Capabilities. arxiv. https://arxiv.org/abs/2605.27898 (2026-05-27)
[8] Toward Secure LLM Agents: Threat Surfaces, Attacks, Defenses, and Evaluation. web. https://arxiv.org/abs/2606.10749 (2026-06-01)
[9] AI Agents Under Threat: A Survey of Key Security Challenges. web. https://arxiv.org/abs/2406.02630 (2024-06-01)
[10] Tool-R0: Self-Evolving LLM Agents for Tool-Learning from Zero Data. hf-search. https://huggingface.co/papers/2602.21320 (2026-02-24)
[11] SoK: Agentic Skills -- Beyond Tool Use in LLM Agents. hf-search. https://huggingface.co/papers/2602.20867 (2026-02-24)
[12] Toward Efficient Agents: A Survey of Memory, Tool Use, and Planning. web. https://arxiv.org/abs/2601.14192 (2026-07-03)
[13] A Survey on Evaluation of LLM-based Agents. web. https://aclanthology.org/2026.findings-acl.1330/ (2026-07-01)
[14] Survey of Emerging Trends in LLM Agent Benchmarking. web. https://dl.acm.org/doi/10.1145/3784013.3784018 (2025-01-01)
[15] Evaluation and Benchmarking of LLM Agents: A Survey. web. https://arxiv.org/abs/2507.21504 (2025-07-01)
