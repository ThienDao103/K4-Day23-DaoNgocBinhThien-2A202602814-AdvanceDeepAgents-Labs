# Review feedback for an efficient-inference / SLM revision

Audit EVERY body citation against the current numbered sources.json entry. In an
earlier draft the source table was reordered while the body still used the old
numbers: MobileLLM and pruning/distillation were swapped, and several survey,
hardware and speculative-decoding claims pointed to different papers. Correct
the association inside the sandbox before running finalizer; matching numbers
syntactically is insufficient. Give the checker the actual cited number, its
JSON title/URL and the exact claim.

Verify the standard speculative-decoding description using
https://aclanthology.org/2026.eacl-long.255.pdf and
https://aclanthology.org/2024.findings-acl.456.pdf. The target verifies draft tokens
in parallel in a forward pass. The earlier draft incorrectly described general
speculative decoding as parallel drafting followed by sequential verification.
Distinguish parallel verification computation from sequential acceptance rules
and distinguish classic autoregressive drafting from newer parallel draft methods.

Verify these existing core results with their original papers:

- MiniLLM reverse-KLD/on-policy distillation: https://arxiv.org/abs/2306.08543.
- Minitron's up-to-40x token saving in its particular model-family experiments:
  https://arxiv.org/abs/2407.14679.
- MobileLLM deep/thin architecture, GQA and immediate weight sharing:
  https://arxiv.org/abs/2402.14905. The page gives 22 February 2024 for submission,
  and 27 June 2024 for revision; the earlier 14 February date is unsupported.
- HW-GPT-Bench's 13-device study and surrogate/NAS approach:
  https://arxiv.org/abs/2405.10299. Check the actual hardware scope before calling
  the devices edge NPUs or edge accelerators.
- Drafting-overhead bottlenecks for small models:
  https://aclanthology.org/2026.eacl-long.255/.

Read full text for exact speedups, milliseconds and tree configurations. Omit
unverified precision. Check the official NVIDIA blog for the exact configuration
and comparison behind the 6.28x result before retaining it. Do not add generic
domain-safety or generalization limitations unless retrieved text supports them.
When an ACL page supplies only month/year, do not invent the first day; use n.d.
for the required exact-date field if no day is retrieved.

Three independent researcher audits, three discovery families and a checker
audit remain mandatory. Preserve supported synthesis while fixing these issues.
