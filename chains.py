import json
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

from prompts import extraction_prompt
from schema import PartialIntake

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is missing from the .env file.")

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0,
    max_tokens=300,
)

# This uses OpenAI function calling through LangChain.
structured_model = model.with_structured_output(
    PartialIntake,
    method="function_calling",
    include_raw=True,
)

extraction_chain = extraction_prompt | structured_model


def extract_fields(user_message, collected_fields):
    """Try extraction twice. Return None if both attempts fail."""

    for _ in range(2):
        try:
            result = extraction_chain.invoke(
                {
                    "known_fields": json.dumps(collected_fields),
                    "user_message": user_message,
                }
            )

            if result["parsing_error"]:
                continue

            return result["parsed"], result["raw"].usage_metadata

        except Exception:
            # Do not log raw user text.
            continue

    return None, {}


def create_confirmation(record):
    return (
        f"\nIntake recorded: {record.regulation_ref.replace('_', ' ')} "
        f"{record.query_type.replace('_', ' ')} for "
        f"{record.jurisdiction.upper()} jurisdiction, classified as "
        f"{record.urgency} priority, submitted by "
        f"{record.submitting_team}.\n\n"
        "Type 'confirm' to save, or type a correction."
    )


confirmation_chain = RunnableLambda(create_confirmation)