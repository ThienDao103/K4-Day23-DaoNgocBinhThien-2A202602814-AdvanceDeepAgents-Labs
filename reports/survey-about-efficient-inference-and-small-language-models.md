# Efficient Inference and Small Language Models: A Survey

## TL;DR
- Small Language Models (SLMs) achieve improved reasoning capacity through architectural design choices such as "deep and thin" configurations [1].
- Efficient inference relies on speculative decoding [2], which uses parallel verification to mitigate memory-bandwidth constraints, and distillation-based compression like MiniLLM [3].
- Recent studies indicate that drafting overhead is a primary bottleneck for speculative decoding in small models [4].
- Hardware-aware optimization is increasingly crucial, as evidenced by benchmarks like HW-GPT-Bench [5], which capture performance metrics across diverse CPU/GPU architectures.

## Background
The demand for efficient on-device language models has surged as LLM deployment expands to resource-constrained environments, leading to developments such as MobileLLM [1] and MobiLlama [6]. Foundationally, efficiency is addressed through architectural design (SLMs) and algorithmic inference acceleration. The primary challenge lies in achieving performance competitive with larger models under strict latency and memory constraints.

## Architectural Innovations for SLMs
Recent advancements in SLM design demonstrate that depth is often more critical than width for sub-billion parameter models. The "deep and thin" architecture paradigm, exemplified by MobileLLM [1], focuses on representation capacity to achieve SoTA results for sub-billion parameter models.

## Parameter-Sharing and Efficient Attention
Complementing architectural depth, parameter-sharing strategies—such as those utilized in MobiLlama [6]—allow models to maintain architectural depth by sharing parameters across specific layers, effectively increasing reasoning depth without inflating the overall memory footprint. MobileLLM [1] integrates GQA (Grouped Query Attention) to optimize further for on-device deployment, reducing key-value cache memory usage.

## Speculative Decoding and Parallel Verification
Inference acceleration aims to maximize compute utilization while minimizing data movement. Speculative decoding addresses memory-bandwidth limitations by using a fast drafting model to propose potential continuations, which the larger target model then verifies in a single parallel forward pass [2]. The target model's acceptance rules guarantee the output distribution matches standard autoregressive decoding. However, a 2026 empirical study [4] finds that for small language models (1–2B parameters), drafting overhead, rather than draft quality, is the primary bottleneck limiting speedup.

## Advanced Model Compression
For model compression, distillation has evolved significantly. MiniLLM employs on-policy distillation using reverse-KLD [3], which prevents the student from overestimating the teacher's lower-probability regions, leading to more robust compression. Minitron provides a practical framework that combines structural pruning with distillation to create efficient model families [7], balancing model footprint with downstream performance.

## Trends and open problems
The field is shifting toward specialized, hardware-aware optimization. Benchmarks like HW-GPT-Bench [5] (published at NeurIPS 2024) provide a systematic approach for evaluating how architectural choices interact with diverse hardware environments, using surrogate models to predict latency and energy. Despite these advances, the integration of these techniques onto specialized edge hardware (e.g., NPUs) remains a complex challenge, with most current benchmarking limited to standard GPU and CPU configurations as measured by HW-GPT-Bench [5]. The primary remaining limitation for inference is drafting-overhead, which for small models (1–2B parameters) has been shown to be the primary bottleneck limiting speedup [4]. The performance trade-offs of deep-thin architectures on non-standard accelerators are not yet fully established in the literature.

## References
[1] MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases. hf-search. https://huggingface.co/papers/2402.14905 (2024-02-22)
[2] Speculative Decoding: Draft Models, Medusa, EAGLE & Lookahead — The LLM Stack. web. https://prakashkagitha.github.io/llm-stack-book/07-inference-serving/06-speculative-decoding.html (n.d.)
[3] MiniLLM: On-Policy Distillation of Large Language Models. arxiv. https://arxiv.org/abs/2306.08543 (2026-01-31)
[4] An Empirical Study of Speculative Decoding for Small Language Models. web. https://aclanthology.org/2026.eacl-long.255/ (n.d.)
[5] HW-GPT-Bench: Hardware-Aware Architecture Benchmark for Language Models. web. https://proceedings.neurips.cc/paper_files/paper/2024/file/6ffdbf064df51857eb802a904aaaba63-Paper-Datasets_and_Benchmarks_Track.pdf (n.d.)
[6] MobiLlama: Towards Accurate and Lightweight Fully Transparent GPT. hf-search. https://huggingface.co/papers/2402.16840 (2024-02-26)
[7] NVlabs/Minitron. web. https://github.com/NVlabs/Minitron (2024-07-17)
