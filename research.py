"""Run one topic: python research.py "survey about world model"."""
import argparse
import hashlib
import json
import os
import re
import shlex
import sys
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from agents import FINALIZER_PATH, NOTES_DIR, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH, WORKDIR, build_lead_agent
from check_citations import check
from model import make_model
from sandbox import download, open_sandbox, sandbox_kind, upload
from tools import redact
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.callbacks import BaseCallbackHandler

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
VALIDATOR_SOURCE = ROOT / "check_citations.py"
FINALIZER_SOURCE = ROOT / "finalize_citations.py"
FAMILIES = {"arxiv", "hf-daily", "hf-search", "web"}


class Progress(BaseCallbackHandler):
    """Report tool names only; do not expose source text, arguments or credentials."""

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"[tool] {serialized.get('name', 'tool')}", flush=True)


def slugify(topic):
    """Safe basename, <=60 characters, including on Windows."""
    slug = re.sub(r"[^\w]+", "-", topic.lower(), flags=re.UNICODE).strip("-_")[:60].rstrip("-_") or "topic"
    if re.fullmatch(r"con|prn|aux|nul|com[1-9]|lpt[1-9]", slug, re.I):
        slug = "topic-" + slug
    return slug


def build_prompt(topic, review_notes=""):
    """Supply the topic as data with an explicit retrieval cutoff."""
    today = datetime.now(timezone.utc).date().isoformat()
    return (f"Research topic (JSON string): {json.dumps(topic, ensure_ascii=False)}\n"
            f"Today is {today}. Include foundational work and evidence within the last two years. "
            "Plan, delegate at least three researchers in parallel, synthesize and verify the final survey in the sandbox. "
            "Do not finish until validation passes and at least three discovery families remain."
            + ("\nOperator review notes for this fresh run:\n" + review_notes if review_notes else ""))


def summarize(messages, elapsed, model_name):
    """Count lead messages only; token totals exclude researcher/checker usage."""
    calls, tokens = Counter(), Counter(input=0, output=0)
    for message in messages:
        get = message.get if isinstance(message, dict) else lambda key, default=None: getattr(message, key, default)
        for call in get("tool_calls", []) or []:
            calls[call["name"]] += 1
        usage = get("usage_metadata", {}) or {}
        tokens["input"] += usage.get("input_tokens", 0) or 0
        tokens["output"] += usage.get("output_tokens", 0) or 0
    return {"model": model_name, "elapsed_s": round(elapsed, 1), "subagent_calls": calls["task"],
            "tool_calls": dict(calls), "tokens": dict(tokens)}


def _source_problems(sources, validate_dates=True):
    problems = []
    for source in sources:
        family, url = source.get("source"), source.get("url", "")
        if family not in FAMILIES:
            problems.append(f"invalid family {family!r}")
        elif family == "arxiv" and not url.startswith("https://arxiv.org/abs/"):
            problems.append("arxiv source must use https://arxiv.org/abs/")
        elif family in {"hf-daily", "hf-search"} and not url.startswith("https://huggingface.co/papers/"):
            problems.append("HF source must use https://huggingface.co/papers/")
        if not source.get("title") or not source.get("id") or not source.get("date"):
            problems.append("source needs id, title and date (n.d. if unavailable)")
        date = source.get("date")
        if validate_dates and date and date != "n.d.":
            try:
                if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                    raise ValueError("invalid date format")
                datetime.strptime(date, "%Y-%m-%d")
            except (TypeError, ValueError):
                problems.append("source date must be YYYY-MM-DD or exactly n.d. when a day is unavailable")
    if len({s.get("source") for s in sources} & FAMILIES) < 3:
        problems.append("final sources must represent at least three discovery families")
    return problems


def _completion_problems(backend, messages, required_researchers=3):
    """Read-only postflight; return actionable issues for a bounded in-sandbox repair."""
    files = download(backend, [REPORT_PATH, SOURCES_PATH, f"{NOTES_DIR}/citation-audit.md"])
    problems = []
    try:
        report = (files.get(REPORT_PATH) or b"").decode("utf-8")
        sources = json.loads((files.get(SOURCES_PATH) or b"").decode("utf-8"))
        problems.extend(check(report, sources))
        if not problems:
            problems.extend(_source_problems(sources))
        headings = re.findall(r"(?m)^##[ \t]+(.+?)\s*$", report)
        required = {"TL;DR", "Background", "Trends and open problems", "References"}
        for heading in sorted(required - set(headings)):
            old = next((h for h in headings if h.casefold() == heading.casefold()), None)
            if old:
                problems.append(f"use edit_file on {REPORT_PATH}: replace old_string '## {old}' with new_string '## {heading}' (case-sensitive)")
            else:
                problems.append(f"use exact heading: ## {heading}")
        themes = [h for h in headings if h.lower() not in {v.lower() for v in required}]
        if not 3 <= len(themes) <= 6:
            problems.append("report needs 3-6 thematic sections in addition to required sections")
    except (ValueError, UnicodeError, TypeError):
        problems.append(f"write nonempty UTF-8 report to {REPORT_PATH} and valid JSON sources to {SOURCES_PATH}")
    if not files.get(f"{NOTES_DIR}/citation-audit.md"):
        problems.append("citation-checker must persist citation-audit.md in the notes directory")
    calls = [call for message in messages for call in
             ((message.get("tool_calls", []) if isinstance(message, dict) else getattr(message, "tool_calls", None)) or [])]
    researchers = sum(call["name"] == "task" and call.get("args", {}).get("subagent_type") == "researcher" for call in calls)
    checkers = sum(call["name"] == "task" and call.get("args", {}).get("subagent_type") == "citation-checker" for call in calls)
    if researchers < required_researchers:
        problems.append("delegate at least three researcher tasks")
    if not checkers:
        problems.append("delegate source verification to citation-checker")
    executed = set()
    for call in calls:
        if call["name"] == "execute":
            try:
                executed.add(tuple(shlex.split(call.get("args", {}).get("command", ""))))
            except ValueError:
                pass
    for path in (FINALIZER_PATH, VALIDATOR_PATH):
        if not executed & {("python3", path), ("python3", path, REPORT_PATH, SOURCES_PATH)}:
            problems.append(f"run python3 {path} using execute")
    return problems


def _publish_files(directory, payloads):
    """Stage all bytes before replacement; restore previous files on a write failure."""
    directory.mkdir(parents=True, exist_ok=True)
    previous = {name: (directory / name).read_bytes() if (directory / name).exists() else None for name in payloads}
    replaced = []
    # Normal mkdir inherits the destination ACL on Windows. TemporaryDirectory
    # uses a private ACL that would follow the files when they are moved out.
    stage = directory / (".research-" + uuid.uuid4().hex)
    stage.mkdir()
    try:
        for name, content in payloads.items():
            (stage / name).write_bytes(content)
        try:
            for name in payloads:
                os.replace(stage / name, directory / name)
                replaced.append(name)
        except OSError:
            for name in reversed(replaced):
                if previous[name] is None:
                    (directory / name).unlink()
                else:
                    (stage / name).write_bytes(previous[name])
                    os.replace(stage / name, directory / name)
            raise
    finally:
        for path in stage.iterdir():
            path.unlink()
        stage.rmdir()


def save_outputs(backend, topic, messages, elapsed, model_name, reports_dir=REPORTS, revision_hash=None, prior_meta=None):
    """Validate downloaded content and metadata before publishing the exact sandbox bytes."""
    files = download(backend, [REPORT_PATH, SOURCES_PATH])
    report, source_bytes = files.get(REPORT_PATH), files.get(SOURCES_PATH)
    if not report or not report.strip() or not source_bytes:
        raise RuntimeError("sandbox report or sources missing/empty")
    try:
        report_text = report.decode("utf-8")
        sources = json.loads(source_bytes.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("sandbox output is not valid UTF-8/JSON") from exc
    problems = check(report_text, sources)
    if not problems:
        problems = _source_problems(sources)
    stats = summarize(messages, elapsed, model_name)
    runs = None
    if prior_meta is not None:
        previous = {key: prior_meta[key] for key in ("model", "elapsed_s", "subagent_calls", "tool_calls", "tokens")}
        runs = [*prior_meta.get("runs", [previous]), dict(stats)]
        stats["elapsed_s"] = round(previous["elapsed_s"] + stats["elapsed_s"], 1)
        stats["subagent_calls"] += previous["subagent_calls"]
        stats["tool_calls"] = dict(Counter(previous["tool_calls"]) + Counter(stats["tool_calls"]))
        stats["tokens"] = dict(Counter(previous["tokens"]) + Counter(stats["tokens"]))
    if stats["subagent_calls"] < 3:
        problems.append("lead must have at least three task calls")
    if problems:
        raise RuntimeError("; ".join(problems[:10]))
    slug = slugify(topic)
    meta = {"topic": topic, **stats, "n_sources": len(sources),
            "source_families": sorted({s["source"] for s in sources})}
    if revision_hash:
        meta.update(run_kind="revision", revision_of_sha256=revision_hash)
    if runs:
        meta.update(run_kind="focused_revision", runs=runs)
    _publish_files(Path(reports_dir), {f"{slug}.sources.json": source_bytes,
                                    f"{slug}.meta.json": json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"),
                                    f"{slug}.md": report})
    return Path(reports_dir) / f"{slug}.md"


@contextmanager
def _configured_sandbox():
    """Fall back only when Daytona creation fails, never when the agent itself fails."""
    manager = open_sandbox()
    try:
        backend = manager.__enter__()
    except Exception as exc:
        if sandbox_kind() != "daytona" or os.getenv("SANDBOX_FALLBACK", "").lower() != "docker":
            raise
        print(f"[sandbox] Daytona unavailable: {redact(exc)}; using Docker", file=sys.stderr)
        manager = open_sandbox("docker")
        backend = manager.__enter__()
    try:
        yield backend
    except BaseException:
        manager.__exit__(*sys.exc_info())
        raise
    else:
        manager.__exit__(None, None, None)


def main(topic, review_notes="", revise=False, focused_revision=False):
    """Return 0 success, 1 failed run, or 2 missing topic; always clean up the sandbox."""
    topic = topic.strip()
    if not topic:
        print('Usage: python research.py "<topic>"', file=sys.stderr)
        return 2
    try:
        model = make_model()
        rpm = float(os.getenv("LAB_MODEL_RPM", "10"))
        if rpm <= 0:
            raise ValueError("LAB_MODEL_RPM must be positive")
        model.rate_limiter = InMemoryRateLimiter(requests_per_second=rpm / 60, max_bucket_size=1)
        start = time.monotonic()
        revision_hash = None
        prior_meta = None
        initial_files = {}
        prompt = build_prompt(topic, review_notes)
        if focused_revision:
            revise = True
            prompt = (f"Focused revision of topic: {json.dumps(topic)}\n"
                      "Preserve verified content. Fix the feedback using primary retrieval and a five-claim checker audit.\n"
                      + review_notes)
        if review_notes and not revise:
            prompt += ("\nThis is a fresh sandbox: no previous report or sources are seeded. "
                       "Historical review notes identify issues to avoid. Retrieve the supplied original "
                       "URLs and create new files; do not search this sandbox for an earlier draft.")
        if revise:
            previous = REPORTS / slugify(topic)
            initial_files = {REPORT_PATH: previous.with_suffix(".md").read_bytes(),
                             SOURCES_PATH: previous.with_suffix(".sources.json").read_bytes()}
            revision_hash = hashlib.sha256(initial_files[REPORT_PATH]).hexdigest()
            if focused_revision:
                prior_meta = json.loads(previous.with_suffix(".meta.json").read_text(encoding="utf-8"))
                if prior_meta.get("topic") != topic or prior_meta.get("subagent_calls", 0) < 3:
                    raise ValueError("focused revision needs an existing genuine generation with >=3 delegations")
                existing_sources = json.loads(initial_files[SOURCES_PATH])
                if (check(initial_files[REPORT_PATH].decode("utf-8"), existing_sources)
                        or _source_problems(existing_sources, validate_dates=False)):
                    raise ValueError("focused revision requires a structurally valid prior generation")
                prompt += f"\nExisting draft: {REPORT_PATH}; existing sources: {SOURCES_PATH}."
            else:
                prompt += (f"\nAn earlier system-generated report and sources are seeded at {REPORT_PATH} and "
                           f"{SOURCES_PATH}. Treat them as a draft requiring verification, not evidence. "
                           "Delegate at least THREE researchers to independently audit foundations, methods, "
                           "and limitations, retrieving at least three discovery families and writing fresh notes. "
                           "Revise the existing report only from verified notes, retaining supported content and "
                           "keeping its scope focused on the feedback and issues found by the audits. "
                           "Correct unsupported claims and bibliographic details. Preserve genuine discovery "
                           "provenance. The citation-checker must audit the feedback points as well as five samples. "
                           "All edits and finalization occur inside this sandbox. Metadata measures this revision run only.")
        with _configured_sandbox() as backend:
            response = backend.execute(f"mkdir -p {NOTES_DIR} {WORKDIR}/report")
            if response.exit_code != 0:
                raise RuntimeError("sandbox workspace creation failed")
            upload(backend, {VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(), FINALIZER_PATH: FINALIZER_SOURCE.read_bytes()})
            if initial_files:
                upload(backend, initial_files)
            seeded = download(backend, [VALIDATOR_PATH, FINALIZER_PATH, *initial_files])
            if not all(seeded.get(path) for path in (VALIDATOR_PATH, FINALIZER_PATH)):
                raise RuntimeError("sandbox script upload failed")
            if any(seeded.get(path) != content for path, content in initial_files.items()):
                raise RuntimeError("sandbox revision draft upload failed")
            print(f"[research] Starting {topic!r} in {sandbox_kind()} sandbox", flush=True)
            agent = (build_lead_agent(backend, model, focused_revision=True) if focused_revision
                     else build_lead_agent(backend, model))
            state = {"messages": [{"role": "user", "content": prompt}]}
            # At most two repairs reuse the same sandbox and genuine lead history.
            for repair in range(3):
                result = agent.invoke(state, config={"recursion_limit": 1000, "callbacks": [Progress()]})
                scripts = download(backend, [VALIDATOR_PATH, FINALIZER_PATH])
                if (scripts.get(VALIDATOR_PATH) != VALIDATOR_SOURCE.read_bytes()
                        or scripts.get(FINALIZER_PATH) != FINALIZER_SOURCE.read_bytes()):
                    raise RuntimeError("agent modified an immutable sandbox script")
                response = backend.execute(f"python3 {VALIDATOR_PATH}")
                problems = (_completion_problems(backend, result["messages"], required_researchers=0) if focused_revision
                            else _completion_problems(backend, result["messages"]))
                if response.exit_code != 0 or not response.output.strip().startswith("OK:"):
                    problems.append(f"sandbox validator: {response.output[:2000]}")
                if not problems:
                    break
                if repair == 2:
                    raise RuntimeError("postflight failed: " + "; ".join(problems[:12]))
                print(f"[repair {repair + 1}/2] " + redact("; ".join(problems[:12])), flush=True)
                instruction = ("Postflight found these issues:\n" + "\n".join(problems[:12]) +
                               "\nRepair existing files INSIDE the sandbox. Preserve discovery provenance: "
                               "use the ORIGINAL arxiv/HF discovery URL, not a replacement HTML/PDF fetch URL. "
                               "Do not change immutable scripts or invent sources. Run finalizer then validator "
                               "again after every edit, recheck families, and complete missing source audits.")
                state = {**result, "messages": [*result["messages"], {"role": "user", "content": instruction}]}
            model_name = os.getenv("LAB_MODEL") or os.getenv("OPENAI_DEPLOYMENT_MODEL") or "unknown"
            extra = {"prior_meta": prior_meta} if focused_revision else {}
            path = save_outputs(backend, topic, result["messages"], time.monotonic() - start, model_name,
                                revision_hash=revision_hash, **extra)
        print(f"Saved: {path}")
        return 0
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {redact(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", nargs="+")
    parser.add_argument("--review-notes", type=Path, help="UTF-8 feedback to verify in a fresh sandbox run")
    parser.add_argument("--revise", action="store_true", help="Seed an existing generated report for an independently audited revision")
    parser.add_argument("--focused-revision", action="store_true", help="Repair a valid prior generation; retain measured original stats and record follow-up stats separately")
    args = parser.parse_args()
    try:
        notes = args.review_notes.read_text(encoding="utf-8") if args.review_notes else ""
    except (OSError, UnicodeError) as exc:
        print(f"FAILED: cannot read review notes: {redact(exc)}", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(" ".join(args.topic), notes, args.revise, args.focused_revision))
