from typing import Dict
import logging
from src.config import Config
from src.llm_providers.llm_factory import LLMFactory
from src.core.conversation_manager import ConversationManager
from src.utils.error_handler import handle_errors
from textstat import flesch_reading_ease
import json

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM provider interactions and conversation management."""

    def __init__(self, config: Config, llm_provider=None, conversation_manager=None):
        """Initializes LLMHandler with config, LLM provider, and conversation manager."""
        self.config = config
        self.llm_provider = llm_provider or LLMFactory.get_provider(config)
        self.conversation_manager = conversation_manager or ConversationManager()

    @handle_errors
    def generate_response(
        self, session_id: str, context: str, question: str
    ) -> Dict[str, str]:
        """Generates a response from the LLM based on context, question, and conversation history."""
        try:
            context_data = json.loads(context)
            formatted_context = self._format_context(context_data)

            conversation_history = self.conversation_manager.get_conversation_summary(
                session_id
            )

            # Create the initial prompt
            prompt = self._create_prompt(
                formatted_context, question, conversation_history
            )

            # If Chain of Thoughts is enabled, modify the prompt
            if self.config.CHAIN_OF_THOUGHTS_ENABLED:
                prompt = self._add_chain_of_thoughts(prompt)

            # If example prompts are provided, add them to the prompt
            if self.config.EXAMPLE_PROMPTS:
                prompt += "\n\nExamples:\n"
                prompt += "\n".join(self.config.EXAMPLE_PROMPTS)

            try:
                response = self.llm_provider.generate_response(prompt)
            except Exception as e:
                logger.error(
                    f"Failed to generate response from provider {self.llm_provider.get_provider_name()}: {e}"
                )
                return {"error": f"Failed to generate response: {e}"}

            self.conversation_manager.add_message(session_id, "user", question)
            self.conversation_manager.add_message(session_id, "assistant", response)

            quality_score = self._evaluate_answer_quality(response)

            return {
                "answer": response,
                "source": self.llm_provider.__class__.__name__,
                "quality_score": quality_score,
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse context JSON: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in generate_response: {str(e)}")
            raise

    def _create_prompt(
        self, context: str, question: str, conversation_history: str
    ) -> str:
        """Creates a prompt using context, question, and conversation history."""

        return f"""
        Context: {context}

        Conversation History:
        {conversation_history}

        Human: {question}

        Assistant: Let me analyze the context and conversation history to provide an accurate answer.
        """

    def _add_chain_of_thoughts(self, prompt: str) -> str:
        """
        Adds a chain of thoughts to the prompt to guide the model's reasoning.
        """
        chain_of_thoughts_text = "\n".join(self.config.CHAIN_OF_THOUGHTS_PROMPT)

        return f"""
        {prompt}

        Let's approach this step by step:

        {chain_of_thoughts_text}
        """

    def _format_context(self, context_data):
        """Formats context data into readable sections of text."""
        formatted_context = ""
        for item in context_data:
            if item["type"] == "text":
                formatted_context += (
                    f"Header: {item['header']}\nContent: {item['content']}\n\n"
                )
            elif item["type"] == "table":
                formatted_context += f"Table:\nHeaders: {', '.join(item['headers'])}\n"
                for row in item["data"]:
                    formatted_context += f"{', '.join(map(str, row))}\n"
                formatted_context += "\n"
        return formatted_context

    def _evaluate_answer_quality(self, answer: str, context: str = None) -> int:
        """Evaluates the quality of the generated answer based on multiple factors."""
        quality_score = 0

        # Factor 1: Length of the answer
        length_score = min(len(answer.split()) // 10, 5)  # Max 5 points for length
        quality_score += length_score

        # Factor 2: Keyword relevance
        keywords = ["MONEYME", "financial", "loan", "income", "assets", "strategy"]
        keyword_score = sum(keyword.lower() in answer.lower() for keyword in keywords)
        keyword_score = min(keyword_score, 3)  # Max 3 points for keywords
        quality_score += keyword_score

        # Factor 3: Readability score
        readability_score = flesch_reading_ease(answer)
        if readability_score > 60:
            quality_score += 2  # Max 2 points for readability

        # Factor 4: Context relevance (if context is provided)
        if context:
            relevance_score = sum(
                1 for word in answer.split() if word.lower() in context.lower()
            )
            relevance_score = min(
                relevance_score // 5, 3
            )  # Max 3 points for context relevance
            quality_score += relevance_score

        # Cap the total score at 10
        return min(quality_score, 10)

    @handle_errors
    def clear_conversation(self, session_id: str):
        """Clears the conversation history for the given session ID. -> not really used for now good to have for scalability"""
        self.conversation_manager.clear_conversation(session_id)
        logger.info(f"Cleared conversation history for session {session_id}")
