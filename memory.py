from langchain_classic.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
)


class SmartMemory:
    def __init__(self, llm):
        self.llm = llm
        self.turns = 0

        self.buffer_memory = ConversationBufferMemory(
            return_messages=True
        )

        self.summary_memory = None

    def save_turn(self, user_message, assistant_message):
        self.turns += 1

        try:
            # Normal memory for the first 10 turns.
            if self.turns <= 10:
                self.buffer_memory.save_context(
                    {"input": user_message},
                    {"output": assistant_message},
                )

            # Summary memory after 10 turns.
            else:
                if self.summary_memory is None:
                    self.summary_memory = ConversationSummaryMemory(
                        llm=self.llm,
                        return_messages=True,
                    )

                self.summary_memory.save_context(
                    {"input": user_message},
                    {"output": assistant_message},
                )

        except Exception:
            pass