
#!/usr/bin/env python3
"""Reconcile payment events using the latest attempt per transaction."""

import json
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def parse_timestamp(value):
    """Convert a UTC timestamp to a comparable datetime."""
    if not isinstance(value, str):
        return None

    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


latest = {}

with (BASE_DIR / "payments.jsonl").open(encoding="utf-8") as file:
    for line in file:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if txn_id is None or txn_id == "":
            continue

        timestamp = parse_timestamp(event.get("ts"))
        if timestamp is None:
            continue

        previous = latest.get(txn_id)
        if previous is None or timestamp > previous[0]:
            latest[txn_id] = (timestamp, event)

total = Decimal("0")
count = 0

for _, event in latest.values():
    if event.get("status") == "success":
        amount = str(event["amount"]).replace(",", "")
        total += Decimal(amount)
        count += 1

with (BASE_DIR / "expected.txt").open(encoding="utf-8") as file:
    expected = int(file.read().strip())

if count != expected:
    print(
        f"Check failed: counted {count} successful payments, "
        f"expected {expected}."
    )
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
