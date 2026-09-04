from chains import (
    confirmation_chain,
    extract_fields,
    model,
)
from memory import SmartMemory
from pydantic import ValidationError
from schema import IntakeRecord
from storage import (
    contains_sensitive_data,
    log_safe_debug,
    save_record,
)

from tools import (
    compliance_checker,
    sensitive_data_checker,
)


COMPLIANCE_WORDS = [
    "aml", "kyc", "sanction", "ofac", "fraud", "sar", "str",
    "fincen", "fca", "rbi", "mas", "pep", "suspicious",
    "transaction", "regulatory", "chargeback", "dispute",
    "pmla", "bsa", "compliance",
]

REQUIRED_FIELDS = [
    "query_type",
    "regulation_ref",
    "jurisdiction",
    "urgency",
    "submitting_team",
]



def ask_for_missing_field(field):
    questions = {
        "query_type": (
            "What is the query type: SAR/STR filing, KYC exception, "
            "transaction dispute, sanctions match, regulatory examination, "
            "fraud investigation, or general enquiry?"
        ),
        "regulation_ref": (
            "Which regulation applies: FATF R20, BSA AML, FCA SYSC, "
            "RBI PMLA, MAS AML, PCI DSS, OFAC SDN, or other?"
        ),
        "jurisdiction": (
            "Which jurisdiction applies: India, UK, Singapore, USA, EU, "
            "multi-jurisdictional, or general?"
        ),
        "urgency": (
            "What is the filing or response deadline? Please classify it as "
            "routine, standard, urgent, or critical."
        ),
        "submitting_team": (
            "Which team or business unit is submitting this? "
            "Do not provide a person's name or customer information."
        ),
    }

    return questions[field]


def main():
    print("\nSmartIntake - AML Compliance Assistant")
    print("Type 'exit' to close.\n")

    memory = SmartMemory(model)

    collected_fields = {}
    intake_turns = 0
    pending_record = None

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ["exit", "quit"]:
            print("SmartIntake closed.")
            break

        if not user_message:
            print("SmartIntake: Please enter a compliance query.")
            continue

        # Confirmation flow
        if pending_record:
            if user_message.lower() in ["confirm", "yes", "y"]:
                saved_path = save_record(
                    pending_record,
                    intake_turns,
                )

                print(f"\nSmartIntake: Record safely saved in {saved_path}\n")

                collected_fields = {}
                intake_turns = 0
                pending_record = None
                continue

            # User gave a correction; keep previous values and process it.
            pending_record = None

        # Block IDs before sending text to model or memory.
        if sensitive_data_checker.invoke({"text": user_message}):
            print(
                "\nSmartIntake: Please remove customer IDs, account numbers, "
                "transaction IDs, and case references before continuing.\n"
            )
            continue

        

        # Avoid unrelated messages.
        
        if (
            not compliance_checker.invoke({"text": user_message})
            and not collected_fields
        ):
            print(
                "\nSmartIntake: I handle AML and financial-compliance intake "
                "only. Please describe a compliance query.\n"
            )
            continue

        intake_turns += 1

        partial_record, usage = extract_fields(
            user_message,
            collected_fields,
        )

        if partial_record is None:
            print(
                "\nSmartIntake: I could not extract the details. Please give "
                "the query type, regulation, jurisdiction, urgency, and "
                "submitting team without customer data.\n"
            )
            continue

        new_fields = partial_record.model_dump(exclude_none=True)
        collected_fields.update(new_fields)

        log_safe_debug(usage, new_fields)

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if not collected_fields.get(field)
        ]

        # Ask only one missing question at a time.
        if missing_fields:
            response = ask_for_missing_field(missing_fields[0])
            print(f"\nSmartIntake: {response}\n")

            memory.save_turn(user_message, response)
            continue

        try:
            pending_record = IntakeRecord(**collected_fields)

            response = confirmation_chain.invoke(pending_record)

            print(f"\nSmartIntake: {response}\n")

            memory.save_turn(user_message, response)

        except ValidationError as error:
            invalid_fields = [item["loc"][0] for item in error.errors()]

            print(
                "\nSmartIntake: Invalid field(s): "
                + ", ".join(invalid_fields)
                + ". Please correct them.\n"
            )
            


if __name__ == "__main__":
    main()