import json
import logging
import re
from datetime import datetime
from pathlib import Path


OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(exist_ok=True)

logging.basicConfig(
    filename="debug.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)

SENSITIVE_PATTERNS = [
    r"\b\d{6,}\b",
    r"\b(customer|account|acct)\s*(id|number|no\.?|#)\s*[:#-]?\s*\w+",
    r"\b(transaction|txn|case|reference)\s*(id|number|no\.?|#)\s*[:#-]?\s*\w+",
]


def contains_sensitive_data(text):
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False


def log_safe_debug(token_usage, fields):
    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)

    # No raw user message is logged.
    logging.info(
        "input_tokens=%s output_tokens=%s fields=%s",
        input_tokens,
        output_tokens,
        json.dumps(fields),
    )


def save_record(record, turns_taken):
    timestamp = datetime.now()
    filename = f"intake_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

    data = record.model_dump()
    data["timestamp"] = timestamp.isoformat(timespec="seconds")
    data["turns_taken"] = turns_taken
    data["log_safe"] = True

    output_path = OUTPUT_FOLDER / filename

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    # Log only the validated structured record.
    logging.info("saved_record=%s", json.dumps(record.model_dump()))

    return output_path