"""Local test harness for Google Chat webhook integration.

Usage:
    1. Start the server:  python main.py  (with MOCK_MODE=true in env)
    2. Run this script:   python test_gchat_local.py

Tests the full request→handler→response pipeline with mock Google Chat payloads.
Delete this file once real Google Chat integration is verified.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

# ─── Test Payloads (mirrors Google Chat webhook format) ──────────────────────

PAYLOADS = [
    {
        "name": "Health Check",
        "method": "GET",
        "path": "/health",
        "body": None,
    },
    {
        "name": "Bot Added to Space",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "ADDED_TO_SPACE",
            "space": {"name": "spaces/AAAA"},
            "message": {"sender": {"displayName": "Admin"}},
        },
    },
    {
        "name": "CrashLoopBackOff Query",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "MESSAGE",
            "space": {"name": "spaces/AAAA"},
            "message": {
                "text": "My pod is in CrashLoopBackOff, what should I check?",
                "sender": {"displayName": "DevOps Engineer"},
                "thread": {"name": "spaces/AAAA/threads/001"},
            },
        },
    },
    {
        "name": "OOMKilled Query",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "MESSAGE",
            "space": {"name": "spaces/AAAA"},
            "message": {
                "text": "Container keeps getting OOMKilled in production",
                "sender": {"displayName": "SRE"},
                "thread": {"name": "spaces/AAAA/threads/002"},
            },
        },
    },
    {
        "name": "ImagePullBackOff Query",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "MESSAGE",
            "space": {"name": "spaces/AAAA"},
            "message": {
                "text": "Deployment stuck with ImagePullBackOff error",
                "sender": {"displayName": "Developer"},
                "thread": {"name": "spaces/AAAA/threads/003"},
            },
        },
    },
    {
        "name": "Generic K8s Question",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "MESSAGE",
            "space": {"name": "spaces/AAAA"},
            "message": {
                "text": "How do I check the health of my EKS cluster nodes?",
                "sender": {"displayName": "Platform Eng"},
                "thread": {"name": "spaces/AAAA/threads/004"},
            },
        },
    },
    {
        "name": "Empty Message",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "MESSAGE",
            "space": {"name": "spaces/AAAA"},
            "message": {
                "text": "",
                "sender": {"displayName": "User"},
                "thread": {"name": ""},
            },
        },
    },
    {
        "name": "Unknown Event Type (should return 200)",
        "method": "POST",
        "path": "/webhook",
        "body": {
            "type": "REMOVED_FROM_SPACE",
            "space": {"name": "spaces/AAAA"},
        },
    },
]


def run_tests():
    print(f"\n{'='*60}")
    print(f"  Google Chat Webhook Test Harness")
    print(f"  Target: {BASE_URL}")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    for test in PAYLOADS:
        name = test["name"]
        try:
            if test["method"] == "GET":
                resp = requests.get(f"{BASE_URL}{test['path']}", timeout=10)
            else:
                resp = requests.post(
                    f"{BASE_URL}{test['path']}",
                    json=test["body"],
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

            status_ok = resp.status_code == 200
            symbol = "✓" if status_ok else "✗"
            print(f"  {symbol} [{resp.status_code}] {name}")

            if status_ok and resp.headers.get("content-type", "").startswith("application/json"):
                body = resp.json()
                # Show card text or plain text
                if "cardsV2" in body:
                    text = body["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
                    print(f"    Response: {text[:100]}...")
                elif "text" in body:
                    print(f"    Response: {body['text'][:100]}...")
                print()

            if status_ok:
                passed += 1
            else:
                failed += 1
                print(f"    Body: {resp.text[:200]}\n")

        except requests.ConnectionError:
            print(f"  ✗ {name} — Connection refused. Is the server running?")
            failed += 1
        except Exception as e:
            print(f"  ✗ {name} — Error: {e}")
            failed += 1

    print(f"\n{'─'*60}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'─'*60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
