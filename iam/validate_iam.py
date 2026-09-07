#!/usr/bin/env python3
"""
Validate iam-policy.json against a least-privilege policy:
  - no binding may use roles/owner or roles/editor

Standard-library only (json module).
"""
import json
import sys

DISALLOWED_ROLES = {"roles/owner", "roles/editor"}


def main():
    if len(sys.argv) != 2:
        print("usage: validate_iam.py <iam-policy.json>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    with open(path) as f:
        policy = json.load(f)

    errors = []
    for binding in policy.get("bindings", []):
        role = binding.get("role", "")
        if role in DISALLOWED_ROLES:
            members = ", ".join(binding.get("members", []))
            errors.append(f"binding uses disallowed role '{role}' for members: {members}")

    if errors:
        print("iam validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("iam validation passed: no binding grants roles/owner or roles/editor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
