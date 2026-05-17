from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

from .config import load_yaml


@dataclass(frozen=True)
class ApprovalDecision:
    required: bool
    reason: str


def requires_approval(tool_name: str, payload: dict[str, Any], policy: dict[str, Any]) -> ApprovalDecision:
    approval = policy.get("approval", {})
    always_required = set(approval.get("always_required", []))

    if tool_name in always_required:
        return ApprovalDecision(True, f"{tool_name} is listed in approval.always_required")

    status = str(payload.get("status", "")).lower()
    if status in {"publish", "future", "private"}:
        return ApprovalDecision(True, f"post status '{status}' changes public visibility")

    if payload.get("bulk") is True:
        return ApprovalDecision(True, "bulk operation requires approval")

    if payload.get("target") in {"homepage", "seo_settings", "robots", "sitemap"}:
        return ApprovalDecision(True, f"{payload['target']} is a protected target")

    return ApprovalDecision(False, "no approval rule matched")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: hermes-wp-policy-check <tool-name> [json-payload]", file=sys.stderr)
        raise SystemExit(2)

    tool_name = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    policy = load_yaml(os.getenv("POLICY_PATH", "config/policy.example.yaml"))
    decision = requires_approval(tool_name, payload, policy)
    print(json.dumps({"required": decision.required, "reason": decision.reason}, ensure_ascii=False))


if __name__ == "__main__":
    main()

