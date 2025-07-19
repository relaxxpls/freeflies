import logging
from typing import Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Summarizer:
    """
    Summarizer class for summarizing transcription using LangChain and OpenAI
    """

    def summarize_transcription(
        self, transcription: list[dict]
    ) -> Optional[Dict[str, str]]:
        """
        Summarize transcription using LangChain and OpenAI

        Args:
            transcription: List of transcription dictionaries with timestamps and text

        Returns:
            Dict containing summary, key_takeaways, and action_items, or None if error
        """
        try:
            if not transcription or len(transcription) == 0:
                return {
                    "summary": "No transcription available to summarize.",
                    "key_takeaways": "",
                    "action_items": "",
                }

            # Extract text from transcription
            transcription_text = ""
            for entry in transcription:
                if isinstance(entry, dict) and "text" in entry:
                    transcription_text += f"{entry.get('text', '')} "
                elif isinstance(entry, str):
                    transcription_text += f"{entry} "

            transcription_text = transcription_text.strip()

            if not transcription_text:
                return {
                    "summary": "No text content found in transcription.",
                    "key_takeaways": "",
                    "action_items": "",
                }

            # Initialize LangChain components
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

            # Create prompt template for summarization
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert meeting assistant that analyzes transcriptions and provides structured summaries.

Your task is to analyze the provided meeting transcription and generate:
1. A comprehensive summary of the discussion
2. Key takeaways and important points discussed
3. Specific action items and next steps

Format your response EXACTLY as follows:

## Summary
[Write a clear, comprehensive summary of the meeting discussion]

## Key Takeaways
• [Key point 1]
• [Key point 2]
• [Additional key points as bullet points]

## Action Items
• [Action item 1 with responsible party if mentioned]
• [Action item 2 with responsible party if mentioned]
• [Additional action items as bullet points]

Important guidelines:
- Be concise but comprehensive
- Focus on actionable insights
- Use bullet points for takeaways and action items
- If no clear action items are mentioned, state "No specific action items identified"
- If the transcription is unclear or incomplete, note this in your response""",
                    ),
                    (
                        "user",
                        "Please analyze this meeting transcription and provide a structured summary:\n\n{transcription}",
                    ),
                ]
            )

            # Create chain
            chain = prompt_template | llm | StrOutputParser()

            logger.info("Generating summary using LangChain...")

            # Generate summary
            result = chain.invoke({"transcription": transcription_text})

            # Parse the structured response
            summary_parts = result.split("## ")
            parsed_result = {"summary": "", "key_takeaways": "", "action_items": ""}

            for part in summary_parts:
                if part.strip():
                    if part.startswith("Summary"):
                        parsed_result["summary"] = part.replace("Summary\n", "").strip()
                    elif part.startswith("Key Takeaways"):
                        parsed_result["key_takeaways"] = part.replace(
                            "Key Takeaways\n", ""
                        ).strip()
                    elif part.startswith("Action Items"):
                        parsed_result["action_items"] = part.replace(
                            "Action Items\n", ""
                        ).strip()

            # If parsing failed, use the raw result as summary
            if not any(parsed_result.values()):
                parsed_result["summary"] = result

            logger.info("Summary generated successfully")
            return parsed_result

        except Exception as e:
            logger.error(f"Error summarizing transcription: {str(e)}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_takeaways": "",
                "action_items": "",
            }
