from langchain.tools import tool
import re

COMPLIANCE_WORDS = [
    "aml", "kyc", "sanction", "ofac", "fraud", "sar", "str",
    "fincen", "fca", "rbi", "mas", "pep", "suspicious",
    "transaction", "regulatory", "chargeback", "dispute",
    "pmla", "bsa", "compliance",
]

SENSITIVE_PATTERNS = [
    r"\b\d{6,}\b",
    r"\b(customer|account|acct)\s*(id|number|no\.?|#)\s*[:#-]?\s*\w+",
    r"\b(transaction|txn|case|reference)\s*(id|number|no\.?|#)\s*[:#-]?\s*\w+",
]


@tool
def compliance_checker(text: str) -> bool:
    """
    Checks whether a message appears AML/compliance related.
    """
    text = text.lower()
    return any(word in text for word in COMPLIANCE_WORDS)


@tool
def sensitive_data_checker(text: str) -> bool:
    """
    Detects IDs, account numbers and transaction references.
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False