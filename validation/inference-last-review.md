# Final focused corrections: preserve all other text

Make only the corrections below, inside the sandbox. Do not rewrite unrelated
claims, add numerical results, change sources or broaden the survey.

1. In sources.json replace the malformed date values `2026-n.d.` and
   `2024-n.d.` with exactly `n.d.`. Neither original publication supplies an
   exact day. Keep year information in the existing body text.
2. The paragraph currently says MobileLLM and MobiLlama BOTH integrate grouped
   query attention. Verify MobileLLM's GQA in its primary page. For MobiLlama,
   fetch https://arxiv.org/html/2402.16840v1 and read the method section: it
   describes shared FFNs. Its GQA mention is a VISUAL QUESTION ANSWERING
   BENCHMARK, not evidence of grouped-query attention. Remove MobiLlama from
   the grouped-query-attention assertion unless the actual architecture text
   establishes it. Retain MobiLlama's already supported shared-FFN description.
3. Remove the unsupported claim that NPUs are largely an open research area
   across the literature. Describe only HW-GPT-Bench's measured CPU/GPU scope,
   and use the supported 2026 drafting-overhead result as the concrete remaining
   inference limitation. Do not infer that an entire field lacks research from
   one benchmark's device list.
4. Add suitable existing citations to the background paragraph's statements
   about resource-constrained on-device deployment, using MobileLLM/MobiLlama.

Delegate one checker for five current claims: MobileLLM grouped-query attention,
MobiLlama shared FFNs, MiniLLM reverse-KLD/on-policy distillation, Minitron pruning
plus distillation, and the 2026 small-model drafting-overhead bottleneck. Supply
the actual current citation numbers and JSON URLs, and explicitly require the
MobiLlama full-text method section above in addition to its discovery HF page.
The full-text fetch URL does not replace its original discovery URL.
After the edits, run the original finalizer and validator. This is a focused
follow-up retaining the genuine original generation history, not a new survey.
