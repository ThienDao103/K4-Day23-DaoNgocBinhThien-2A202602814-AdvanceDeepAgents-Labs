# Focused review of the generated efficient-inference survey

Retrieve the primary MobileLLM and MobiLlama papers. Do not claim that all SLMs
have superior reasoning merely because these architecture choices improve the
reported evaluations. Verify precisely which parameters MobiLlama shares;
do not call this recycling whole transformer blocks if only feed-forward
parameters are shared. Verify GQA attribution separately for each model.

Check the exact date of HW-GPT-Bench from primary publication metadata. The
NeurIPS source establishes 2024, not necessarily 1 January; use n.d. if no
exact day is retrieved. MiniLLM's current arXiv page really has the title
"MiniLLM: On-Policy Distillation of Large Language Models" and a 31 January
2026 revision, so verify those before changing them.

Improve the recent-evidence comparison by discovering and reading the primary
2026 paper "An Empirical Study of Speculative Decoding for Small Language
Models", https://aclanthology.org/2026.eacl-long.255/. It compares five method
categories across three model families and finds drafting overhead limiting
small-model speedup; verify these details with retrieval and contrast them
with general speculative decoding. The ACL page supplies March 2026 but no
day, so use n.d. in the exact-date field. This feedback explicitly authorizes
adding this one relevant recent source using genuine web discovery.

Retain three thematic sections, three discovery families, citations for
background claims, and comparisons between architecture, distillation,
speculation and hardware constraints. Have the checker audit five exact
claims, including MobiLlama sharing and the recent small-model limitation.
Repair and finalize only inside the sandbox; preserve the remaining evidence.
