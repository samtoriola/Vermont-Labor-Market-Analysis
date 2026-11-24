"""The report may measure. It may not grade.

The report is the one output that leaves the dashboard. Nobody holding it can
check a claim against the tab it came from, so every sentence in it has to be a
figure or a comparison between figures -- something the reader can verify from
the numbers printed beside it.

That rules out a class of word, not a list of sentences. "Vermont does not have
a hiring problem" is indefensible in a document that travels: it is a judgement
wearing a finding's clothes, and the person who has to defend it in a meeting
will not have the room's definition of "problem" to hand. The same goes for
best, worst, healthy, failing, underpaid. Each asserts a standard the data does
not carry.

So the words are banned here rather than left to whoever edits next, because
this is exactly the constraint that erodes one well-meant adjective at a time.

WHAT IS STILL ALLOWED
  - superlatives of a measured quantity ("the highest replacement rate"), which
    name a row in a sorted column with the sort shown beside them
  - direction and size ("6.4% fewer jobs than in 2021", "12.2 points above")
  - "most", "largest", "ranges from", "differs most" -- all countable

Comments are skipped, so the modules can explain the rule using the words it
bans. Only what a reader could see is scanned.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    os.path.join(HERE, "..", "lib", "report.js"),
    os.path.join(HERE, "..", "components", "views", "Report.js"),
]

# Words that assert a standard the data does not carry.
BANNED = [
    # grading
    "best", "worst", "poor", "poorly", "bad", "badly", "terrible", "excellent",
    "impressive", "promising", "healthy", "unhealthy", "robust", "weak",
    "strong", "stark", "dire", "bleak",
    # diagnosis
    "problem", "crisis", "failing", "failure", "fails", "struggling",
    "thriving", "lagging", "underpaid", "overpaid", "mismatch", "shortfall",
    "inadequate", "unsustainable",
    # editorialising
    "alarming", "troubling", "concerning", "worrying", "worryingly",
    "surprisingly", "unfortunately", "sadly", "encouragingly", "notably",
    "strikingly", "dramatically", "dramatic", "staggering", "shocking",
    "simply", "clearly", "obviously", "of course", "needless to say",
    # prescription -- the report reports; the reader decides
    "should", "must", "ought", "need to", "needs to", "recommend",
    "recommended", "priority", "actionable", "imperative",
    # unearned framing
    "exposure", "vulnerable", "at risk", "opportunity cost", "merely", "only just",
]

# A phrase that denies something in the reader's head rather than stating a
# figure. "Vermont does not have a hiring problem" is the pattern.
BANNED_PHRASES = [
    "does not have a",
    "is not a",
    "rather than a",
]


def strip_comments(src):
    """Drop // and /* */ so the modules can name the words they ban."""
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


fails = []
scanned = 0

for path in FILES:
    if not os.path.exists(path):
        fails.append("missing: %s" % os.path.relpath(path, HERE))
        continue
    name = os.path.basename(path)
    body = strip_comments(io.open(path, encoding="utf-8").read())
    scanned += 1
    low = body.lower()

    for w in BANNED:
        for m in re.finditer(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            line = body[: m.start()].count("\n") + 1
            ctx = body.split("\n")[line - 1].strip()
            fails.append("%s:%d  grades rather than measures: %r\n        %s"
                         % (name, line, w, ctx[:110]))

    for p in BANNED_PHRASES:
        for m in re.finditer(re.escape(p), low):
            line = body[: m.start()].count("\n") + 1
            ctx = body.split("\n")[line - 1].strip()
            fails.append("%s:%d  denies rather than states: %r\n        %s"
                         % (name, line, p, ctx[:110]))

print("scanned %d file(s), %d banned terms" % (scanned, len(BANNED) + len(BANNED_PHRASES)))

if fails:
    print()
    for f in fails:
        print("FAIL  %s" % f)
    print("\nSay it with a number instead, or add the word to the allowed list "
          "above with a reason.")
    sys.exit(1)

print("OK  the report states figures, not judgements")
