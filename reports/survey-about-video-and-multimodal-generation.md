# A Comprehensive Survey on Video and Multimodal Generation: Foundations, Architectures, and Efficiency

## TL;DR
- Video generation has evolved from early 2D/3D U-Net diffusion models into scalable Diffusion Transformers (DiTs) and continuous-token autoregressive architectures capable of high-fidelity spatial-temporal synthesis [1][2][3].
- Unified multimodal frameworks integrate MLLMs with Multimodal DiTs (MMDiTs) to support joint understanding, text/image-to-video generation, editing, and audio-visual synchronization [4][5].
- Controllable generation paradigms extend text prompts with non-textual conditioning signals such as camera motion, depth maps, and human poses to fulfill fine-grained user requirements [6].
- Efficiency optimizations, including step distillation, parameter pruning, token compression, and information-theoretic tokenizers, are crucial for mitigating high inference costs and computational bottlenecks [7][8][9].

## Background
Video and multimodal generation represents a cornerstone of modern generative artificial intelligence, bridging static image synthesis, natural language processing, and temporal dynamics. Historically, video generation relied on Generative Adversarial Networks (GANs) and Variational Autoencoders (VAEs), which struggled with long-range temporal consistency and complex scene dynamics [10]. The introduction of video diffusion models established robust foundational principles by iteratively denoising temporal pixel or latent arrays [1]. Over recent years (2024–2026), the field has undergone a profound architectural shift toward scalable Diffusion Transformers (DiTs), autoregressive continuous token models, and unified multimodal foundation models that jointly process text, images, video, and audio [2][3][4][5]. Understanding these developments is critical as video generation transitions into world models for embodied AI and interactive simulation.

## Architectural Foundations of Video Generation
The architectural landscape of video generation spans diffusion-based models and autoregressive formulations [1][3]. Early video diffusion models adapted 2D image generators using pseudo-3D convolutions or factorized spatial-temporal attention layers, which later transitioned to native 3D U-Nets and scalable Diffusion Transformers (DiTs) [1]. For instance, Wan exemplifies open, large-scale video generative models built on the DiT paradigm, featuring dedicated high-compression video VAEs and scalable pre-training strategies that enhance text-to-video alignment and temporal smoothness [2]. 

Concurrently, autoregressive video generation has advanced beyond discrete token quantization. VideoMAR introduces an efficient decoder-only autoregressive model utilizing continuous tokens, temporal causality, spatial bi-directionality, and 3D rotary positional embeddings, achieving superior performance with fewer computational resources [3]. Furthermore, large-scale empirical studies on autoregressive video pre-training demonstrate robust scaling behaviors analogous to large language models, validating that transformer-based architectures can effectively capture complex temporal distributions when trained on massive video-image corpora [11].

## Multimodal Conditioning and Unified Architectures
While early video generators relied solely on text prompts, text descriptions alone are frequently insufficient to express complex, fine-grained user intent [6]. Consequently, controllable video generation research integrates non-textual conditioning signals—such as camera motion trajectories, depth maps, and human poses—into pretrained diffusion denoising processes [6]. 

To bridge understanding and generation, recent paradigms adopt unified architectures. UniVideo employs a dual-stream design combining a Multimodal Large Language Model (MLLM) for visual comprehension with a Multimodal DiT (MMDiT) for visual generation, unifying video comprehension, text/image-to-video generation, and editing under a single multimodal instruction framework [4]. Similarly, Audio-Visual Intelligence (AVI) frameworks integrate auditory and visual modalities within large foundation models, enabling joint understanding, audio-driven video synthesis, and synchronized interaction [5]. Multimodal video generation models jointly model audio and video to achieve enhanced immersion and semantic coherence, addressing the inherent limitations of silent visual generation [12].

## Spatiotemporal Consistency and Efficiency Optimizations
A central challenge in video synthesis is maintaining spatiotemporal consistency across long durations and high resolutions [10]. Research in this area addresses feature representation through five primary directions: compression representation, long sequence representation, feature discretization, feature decoupling, and diffusion timestep-based representations [13]. 

To overcome the heavy computational overhead of iterative diffusion denoising and large spatial-temporal token grids, efficiency optimizations are categorized into step distillation, efficient attention, model compression, and cache/trajectory optimization [7]. For example, FastLightGen combines step distillation and model parameter pruning into a unified co-distillation framework, demonstrating that 4-step sampling combined with 30% parameter pruning achieves optimal visual quality under constrained inference budgets [8]. Additionally, token compression techniques such as InfoTok employ adaptive information-theoretic compression inspired by Shannon's information theory to allocate tokens dynamically according to informational richness [9].

## Trends and open problems
Recent developments over the past two years highlight a clear trajectory toward real-time generation, interactive multi-modal world modeling, and unified audio-visual simulation [5][12][7]. However, several fundamental challenges remain unresolved. Semantic alignment between text prompts and generated video content remains difficult in action-rich or multi-object scenes [10]. Ensuring smooth temporal consistency without visually jarring transitions or composite acceleration drift is an active area of research [10][7]. Furthermore, high computational costs, limited availability of large-scale curated multimodal datasets, and the absence of standardized infrastructure for benchmarking real-time long-horizon video generation continue to constrain widespread deployment [10][7].

## References
[1] Video Diffusion Models: A Survey. arxiv. https://arxiv.org/abs/2405.03150 (2024-05-06)
[2] Wan: Open and Advanced Large-Scale Video Generative Models. hf-search. https://huggingface.co/papers/2503.20314 (2025-03-26)
[3] VideoMAR: Autoregressive Video Generation with Continuous Tokens. hf-search. https://huggingface.co/papers/2506.14168 (2025-06-17)
[4] UniVideo: Unified Understanding, Generation, and Editing for Videos. arxiv. https://arxiv.org/abs/2510.08377 (2026-01-07)
[5] Audio-Visual Intelligence in Large Foundation Models. arxiv. https://arxiv.org/abs/2605.04045 (2026-05-05)
[6] Controllable Video Generation: A Survey. arxiv. https://arxiv.org/abs/2507.16869 (2026-01-19)
[7] Efficient Video Diffusion Models: Advancements and Challenges. arxiv. https://arxiv.org/abs/2604.15911 (2026-04-17)
[8] FastLightGen: Fast and Light Video Generation with Fewer Steps and Parameters. arxiv. https://arxiv.org/abs/2603.01685 (2026-03-12)
[9] InfoTok: Adaptive Discrete Video Tokenizer via Information-Theoretic Compression. hf-search. https://huggingface.co/papers/2512.16975 (2025-12-18)
[10] Bridging Text and Video Generation: A Survey. arxiv. https://arxiv.org/abs/2510.04999 (2025-10-04)
[11] An Empirical Study of Autoregressive Pre-training from Videos. hf-search. https://huggingface.co/papers/2501.05453 (2025-01-09)
[12] Multimodal Video Generation Models with Audio: Present and Future. web. https://openreview.net/forum?id=8i5vInabkm (2026-02-18)
[13] A Survey: Spatiotemporal Consistency across Video Generation. web. https://dl.acm.org/doi/10.1145/3802588 (2026-05-18)
