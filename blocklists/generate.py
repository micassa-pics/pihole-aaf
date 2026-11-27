"""Generate Pi-hole adlists and companion regexes from the Logstalgia catalog."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOMAIN = re.compile(r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)*", re.ASCII)
GLOB = re.compile(r"[a-z0-9_.*?-]+", re.ASCII)


def export_rule(rule):
    if rule.startswith("/") and rule.endswith("/") and len(rule) > 2:
        expression = rule[1:-1].replace("(?:", "(")
        if "(?" in expression or re.search(r"\\[A-Za-z1-9]", expression):
            raise ValueError(f"translate this regex to Pi-hole syntax: {rule}")
        return None, expression

    rule = rule.lower().rstrip(".")
    if rule.startswith("=") and DOMAIN.fullmatch(rule[1:]):
        return rule[1:], None
    if DOMAIN.fullmatch(rule):
        return f"||{rule}^", None
    if GLOB.fullmatch(rule) and ("*" in rule or "?" in rule):
        pieces = {"*": ".*", "?": "."}
        return None, "^" + "".join(pieces.get(char, re.escape(char)) for char in rule) + "$"
    raise ValueError(f"invalid domain rule: {rule}")


def outputs():
    catalog = json.loads((ROOT / "service-domains.json").read_text(encoding="utf-8"))
    for service, rules in catalog.items():
        if not re.fullmatch(r"[a-z0-9_]+", service):
            raise ValueError(f"invalid service ID: {service}")
        domains, expressions = set(), set()
        for rule in rules:
            domain, regex = export_rule(rule)
            if domain:
                domains.add(domain)
            if regex:
                expressions.add(regex)
        header = "# Generated from ../service-domains.json. See ../README.md for sources and license.\n"
        yield ROOT / "lists" / f"{service}.txt", header + "\n".join(sorted(domains)) + "\n"
        if expressions:
            yield ROOT / "regex" / f"{service}.txt", header + "\n".join(sorted(expressions)) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if any generated file differs")
    args = parser.parse_args()
    expected = dict(outputs())
    existing = {path for folder in ("lists", "regex") for path in (ROOT / folder).glob("*.txt")}
    obsolete = existing - expected.keys()
    if args.check:
        stale = [path for path, contents in expected.items()
                 if not path.is_file() or path.read_text(encoding="utf-8") != contents]
        if stale or obsolete:
            parser.error("files differ: " + ", ".join(str(path.relative_to(ROOT)) for path in sorted([*stale, *obsolete])))
        return
    for path, contents in expected.items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(contents, encoding="utf-8", newline="\n")
    for path in sorted(obsolete):
        path.unlink()


if __name__ == "__main__":
    main()
