"""check_citations.py - STUDENT IMPLEMENTS `check`.   Runs INSIDE the sandbox (standard library only).

research.py uploads this file to the sandbox and the lead agent runs it with the `execute` tool:
    python3 /tmp/work/research/check_citations.py [report.md] [sources.json]
It must exit 0 and print "OK: ..." when the report is consistent, else print each problem and exit 1.
"""
import json
import re
import sys
from collections import Counter
from urllib.parse import urlsplit

REPORT = "/tmp/work/report/report.md"
SOURCES = "/tmp/work/research/sources.json"


def check(report_text, sources):
    """Return a list of problem strings (empty list = OK).

    PSEUDO-CODE:
      problems = []
      if sources is empty: return ["no sources in sources.json"]
      for each source entry:
          n must be an int                       -> problem if not
          url must start with http:// or https://-> problem if not
          the same url must not appear twice     -> problem if duplicated
      split report_text at the heading "## References":
          body = text before it; if the heading is missing -> problem
      cited = set of numbers found as [n] in the BODY only (not in the reference list; use a regex)
      every number in `cited` must exist in sources -> problem "[n] cited but missing from sources.json"
      every source number must be in `cited`        -> problem "source [n] never cited"
      the lines of the References section that start with "[n]" (regex) are the reference lines:
          every source needs exactly ONE reference line (none missing, no number twice, no number that is not a source)
          each reference line holds exactly ONE http(s) URL and it must equal that source's url
          (a line bundling several sources under one number is a problem)
      return problems
    """
    if not isinstance(sources, list) or not sources:
        return ["sources.json must be a nonempty JSON list"]
    problems, by_n, urls = [], {}, set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            problems.append(f"source {index + 1} must be an object")
            continue
        n, url = source.get("n"), source.get("url")
        if type(n) is not int or n < 1:
            problems.append(f"source {index + 1}: n must be a positive integer")
        elif n in by_n:
            problems.append(f"duplicate source number [{n}]")
        else:
            by_n[n] = source
        if not isinstance(url, str) or not valid_url(url):
            problems.append(f"source {index + 1}: invalid http(s) URL")
        elif url in urls:
            problems.append(f"duplicate source URL: {url}")
        else:
            urls.add(url)
    text = re.sub(r"```.*?```|~~~.*?~~~|`[^`\n]*`", "", report_text, flags=re.S)
    headings = list(re.finditer(r"(?m)^##[ \t]+References[ \t]*\r?$", text))
    if len(headings) != 1:
        problems.append("report must have exactly one ## References heading")
    body = text[:headings[0].start()] if headings else text
    references = text[headings[0].end():] if headings else ""
    cited = set()
    for match in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\s*\()", body):
        for part in match.group(1).split(","):
            span = re.fullmatch(r"\s*(\d+)\s*[–-]\s*(\d+)\s*", part)
            if span:
                first, last = map(int, span.groups())
                if last < first or last - first > 200:
                    problems.append(f"invalid citation range [{part}]")
                else:
                    cited.update(range(first, last + 1))
            else:
                cited.add(int(part.strip()))
    for n in sorted(cited - by_n.keys()):
        problems.append(f"[{n}] cited but missing from sources.json")
    for n in sorted(by_n.keys() - cited):
        problems.append(f"source [{n}] never cited in the body")
    counts = Counter()
    for line in references.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^\[(\d+)\]\s+", line)
        if not match:
            problems.append("References must contain only one [n] source per line")
            continue
        n = int(match.group(1))
        counts[n] += 1
        found = re.findall(r"https?://[^\s<>]+", line)
        if len(found) != 1:
            problems.append(f"reference [{n}] must contain exactly one URL")
        elif n in by_n and found[0] != by_n[n].get("url"):
            problems.append(f"reference [{n}] URL differs from sources.json")
        if n not in by_n:
            problems.append(f"reference [{n}] is not a source")
    for n in sorted(by_n):
        if counts[n] != 1:
            problems.append(f"source [{n}] needs exactly one reference line (found {counts[n]})")
    return problems


def valid_url(url):
    """Validate an absolute HTTP URL without making network requests."""
    try:
        parsed = urlsplit(url)
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and not re.search(r"\s", url))
    except ValueError:
        return False


def main(argv):
    report_path = argv[1] if len(argv) > 1 else REPORT
    sources_path = argv[2] if len(argv) > 2 else SOURCES
    try:
        with open(report_path, encoding="utf-8") as f:
            report = f.read()
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read inputs: {exc}")
        return 1
    problems = check(report, sources)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(sources)} sources, all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
