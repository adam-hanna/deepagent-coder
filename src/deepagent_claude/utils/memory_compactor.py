"""
Memory Compactor - Manages conversation memory through intelligent summarization.

This module provides memory management capabilities for long-running conversations
by detecting when memory usage exceeds thresholds and compacting older messages
into concise summaries.

Key features:
- Token-based threshold detection
- Async LLM-based summarization
- Preservation of recent context
- Conversation structure maintenance

Example:
    selector = ModelSelector()
    compactor = MemoryCompactor(selector, threshold=6000)

    if compactor.should_compact(messages):
        summary = await compactor.compact_conversation(messages)
        # Replace old messages with summary
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemoryCompactor:
    """
    Compacts conversation memory by summarizing old messages.

    Monitors conversation length and provides intelligent summarization
    when token thresholds are exceeded. Uses LLM to generate concise
    summaries while preserving key context.

    Attributes:
        model_selector: ModelSelector instance for accessing summarizer model
        threshold: Token count threshold for triggering compaction (default: 6000)
    """

    def __init__(self, model_selector, threshold: int = 6000):
        """
        Initialize MemoryCompactor with model selector and threshold.

        Args:
            model_selector: ModelSelector instance for model access
            threshold: Token count threshold for compaction (default: 6000)
        """
        self.model_selector = model_selector
        self.threshold = threshold
        logger.debug(f"MemoryCompactor initialized with threshold={threshold}")

    def should_compact(self, messages: list[dict[str, Any]]) -> bool:
        """
        Check if conversation should be compacted based on token count.

        Args:
            messages: List of conversation messages with 'role' and 'content'

        Returns:
            bool: True if compaction is needed, False otherwise
        """
        # Estimate token count (rough approximation: ~4 chars per token)
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars // 4

        should_compact = estimated_tokens > self.threshold
        logger.debug(
            f"Token estimate: {estimated_tokens}, threshold: {self.threshold}, "
            f"should_compact: {should_compact}"
        )
        return should_compact

    async def compact_conversation(
        self, messages: list[dict[str, Any]], keep_recent: int = 5
    ) -> str:
        """
        Compact conversation by summarizing older messages.

        Takes conversation history and generates a concise summary of older
        messages while preserving recent context. Uses the summarizer model
        for intelligent compression.

        Args:
            messages: List of conversation messages to compact
            keep_recent: Number of recent messages to exclude from summary (default: 5)

        Returns:
            str: Concise summary of the conversation history

        Example:
            summary = await compactor.compact_conversation(messages)
            # Returns: "User discussed project setup and API design..."
        """
        if len(messages) <= keep_recent:
            # Not enough messages to compact
            logger.debug("Too few messages to compact, returning empty summary")
            return ""

        # Split messages: older ones to summarize, recent ones to keep
        messages_to_summarize = messages[:-keep_recent]

        # Build conversation text for summarization
        conversation_text = self._format_messages_for_summary(messages_to_summarize)

        # Get summarizer model
        summarizer = self.model_selector.get_model("summarizer")

        # Create summarization prompt
        prompt = self._create_summary_prompt(conversation_text)

        # Generate summary
        logger.info(f"Compacting {len(messages_to_summarize)} messages into summary")
        try:
            response = await summarizer.ainvoke(prompt)
            summary = response.content if hasattr(response, "content") else str(response)
            logger.debug(f"Generated summary of length {len(summary)}")
            return summary
        except Exception as e:
            logger.error(f"Error during conversation compaction: {e}")
            # Fallback to simple truncation if summarization fails
            return self._create_fallback_summary(messages_to_summarize)

    def _format_messages_for_summary(self, messages: list[dict[str, Any]]) -> str:
        """
        Format messages into readable text for summarization.

        Args:
            messages: List of messages to format

        Returns:
            str: Formatted conversation text
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n\n".join(lines)

    def _create_summary_prompt(self, conversation_text: str) -> str:
        """
        Create prompt for LLM summarization.

        Args:
            conversation_text: Formatted conversation to summarize

        Returns:
            str: Prompt for summarization
        """
        return f"""You are a conversation summarizer. Your task is to create a concise but comprehensive summary of the following conversation.

Focus on:
- Key decisions made
- Important context established
- Main topics discussed
- Any unresolved issues or pending tasks

Keep the summary focused and relevant. Aim for 3-5 sentences that capture the essential information.

CONVERSATION:
{conversation_text}

SUMMARY:"""

    def _create_fallback_summary(self, messages: list[dict[str, Any]]) -> str:
        """
        Create simple fallback summary when LLM summarization fails.

        Args:
            messages: Messages to summarize

        Returns:
            str: Basic fallback summary
        """
        msg_count = len(messages)
        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")

        summary = (
            f"Previous conversation context: {msg_count} messages exchanged "
            f"({user_msgs} user, {assistant_msgs} assistant). "
            f"Full context available in conversation history."
        )
        logger.warning(f"Using fallback summary: {summary}")
        return summary

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for given text.

        Uses rough approximation of 4 characters per token.
        For more accurate counting, integrate tiktoken or similar.

        Args:
            text: Text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        return len(text) // 4

    def compact_with_summary(
        self, messages: list[dict[str, Any]], summary: str, keep_recent: int = 5
    ) -> list[dict[str, Any]]:
        """
        Replace old messages with summary message.

        Args:
            messages: Original message list
            summary: Generated summary text
            keep_recent: Number of recent messages to keep

        Returns:
            List[Dict[str, Any]]: New message list with summary + recent messages
        """
        if len(messages) <= keep_recent:
            return messages

        # Create summary message
        summary_message = {"role": "system", "content": f"[Conversation Summary]\n\n{summary}"}

        # Keep recent messages
        recent_messages = messages[-keep_recent:]

        # Combine: summary + recent
        compacted = [summary_message] + recent_messages

        logger.info(
            f"Compacted {len(messages)} messages to {len(compacted)} "
            f"(1 summary + {keep_recent} recent)"
        )
        return compacted
