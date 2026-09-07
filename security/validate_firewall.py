#!/usr/bin/env python3
"""
Validate firewall.yaml against a simple least-exposure policy:
  - port 22 (SSH) must never be open to 0.0.0.0/0
  - the DB port (5432) must never be open to 0.0.0.0/0

Standard-library only. Rather than depend on PyYAML, this script uses a
tiny hand-rolled parser sufficient for the flat firewall.yaml schema used
in this repo (list of rules, each with name/direction/allowed/source_ranges).
See README.md for why this approach was chosen.
"""
import sys

DB_PORT = "5432"
DANGEROUS_CIDR = "0.0.0.0/0"


def parse_firewall_yaml(path):
    """Minimal parser for this repo's firewall.yaml shape."""
    rules = []
    current = None
    current_allowed = None
    with open(path) as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- name:"):
            current = {"name": stripped.split(":", 1)[1].strip(), "allowed": [], "source_ranges": []}
            rules.append(current)
            current_allowed = None
            continue

        if current is None:
            continue

        if stripped.startswith("direction:"):
            current["direction"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("allowed:"):
            current_allowed = {}
        elif stripped.startswith("- protocol:"):
            current_allowed = {"protocol": stripped.split(":", 1)[1].strip()}
            current["allowed"].append(current_allowed)
        elif stripped.startswith("ports:"):
            value = stripped.split(":", 1)[1].strip()
            ports = [p.strip().strip('"') for p in value.strip("[]").split(",") if p.strip()]
            if current_allowed is not None:
                current_allowed["ports"] = ports
        elif stripped.startswith("source_ranges:"):
            value = stripped.split(":", 1)[1].strip()
            ranges = [r.strip().strip('"') for r in value.strip("[]").split(",") if r.strip()]
            current["source_ranges"] = ranges

    return rules


def validate(rules):
    errors = []
    for rule in rules:
        name = rule.get("name", "<unnamed>")
        ranges = rule.get("source_ranges", [])
        if DANGEROUS_CIDR not in ranges:
            continue
        for allowed in rule.get("allowed", []):
            ports = allowed.get("ports", [])
            if "22" in ports:
                errors.append(f"rule '{name}' opens SSH (22) to {DANGEROUS_CIDR}")
            if DB_PORT in ports:
                errors.append(f"rule '{name}' opens DB port ({DB_PORT}) to {DANGEROUS_CIDR}")
    return errors


def main():
    if len(sys.argv) != 2:
        print("usage: validate_firewall.py <firewall.yaml>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    rules = parse_firewall_yaml(path)
    errors = validate(rules)

    if errors:
        print("firewall validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("firewall validation passed: no rule exposes SSH or DB port to 0.0.0.0/0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
