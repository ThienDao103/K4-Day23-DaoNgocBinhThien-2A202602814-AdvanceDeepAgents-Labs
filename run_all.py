"""Generate the five preset topics sequentially, optionally resuming valid results."""
import sys

from check_citations import check
from research import REPORTS, main as research
from self_check import check_topic, load_topics, main as self_check


def main(argv):
    if any(arg != "--resume" for arg in argv):
        print("Usage: python run_all.py [--resume]", file=sys.stderr)
        return 2
    topics = load_topics()
    for index, topic in enumerate(topics, 1):
        if "--resume" in argv and not check_topic(topic, REPORTS, check):
            print(f"[{index}/{len(topics)}] Already validated: {topic}", flush=True)
            continue
        print(f"[{index}/{len(topics)}] Researching: {topic}", flush=True)
        code = research(topic)
        if code:
            print("Stopped after failed topic. Fix the cause, then use --resume.", file=sys.stderr)
            return code
    return self_check([])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
