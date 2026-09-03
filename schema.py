from typing import Literal, Optional

from pydantic import BaseModel, field_validator


QueryType = Literal[
    "sar_str_filing",
    "kyc_exception",
    "transaction_dispute",
    "sanctions_match",
    "regulatory_examination",
    "fraud_investigation",
    "general_enquiry",
]

RegulationRef = Literal[
    "FATF_R20",
    "BSA_AML",
    "FCA_SYSC",
    "RBI_PMLA",
    "MAS_AML",
    "PCI_DSS",
    "OFAC_SDN",
    "other",
]

Jurisdiction = Literal[
    "india",
    "uk",
    "singapore",
    "usa",
    "eu",
    "multi_jurisdictional",
    "general",
]

Urgency = Literal[
    "routine",
    "standard",
    "urgent",
    "critical",
]


class IntakeRecord(BaseModel):
    query_type: QueryType
    regulation_ref: RegulationRef
    jurisdiction: Jurisdiction
    urgency: Urgency
    submitting_team: str

    @field_validator("submitting_team")
    @classmethod
    def validate_team(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Submitting team cannot be empty.")

        if any(char.isdigit() for char in value):
            raise ValueError("Submitting team cannot contain numeric identifiers.")

        forbidden_words = ["customer", "account", "transaction", "case"]
        if any(word in value.lower() for word in forbidden_words):
            raise ValueError("Submitting team must be a business team.")

        allowed_short_names = ["KYC", "AML", "TM"]
        if (
            len(value.split()) == 1
            and value.isalpha()
            and value.upper() not in allowed_short_names
        ):
            raise ValueError("Please provide a team name, not a person name.")

        return value.title()


class PartialIntake(BaseModel):
    query_type: Optional[QueryType] = None
    regulation_ref: Optional[RegulationRef] = None
    jurisdiction: Optional[Jurisdiction] = None
    urgency: Optional[Urgency] = None
    submitting_team: Optional[str] = None