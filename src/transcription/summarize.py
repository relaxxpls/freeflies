import logging
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from .models import DiarizationResult, MeetingSummary
from src.utils import transcription_to_markdown

load_dotenv()

logger = logging.getLogger(__name__)

summarize_system_prompt = """The following text is a diarized transcription of a meeting conversation with identified speakers and timestamps.
The format shows each speaker's contributions grouped together with timestamps in markdown format.

From this speaker-attributed transcript, please extract a comprehensive summary and action items.

Guidelines:
- Use speaker information to understand conversation flow and attribute statements correctly
- Transcription errors to closely pronounced words should be corrected, and fillers should be ignored
- The summary should capture key discussion points, decisions made, and who was involved
- When relevant, include speaker attribution for important statements or decisions (e.g., "Speaker 01 agreed to...")
- Action items should only include items explicitly mentioned by participants with clear ownership when stated
- Do not add speculation or general knowledge beyond what was discussed
- Pay attention to speaker interactions, agreements, disagreements, and conversation dynamics

Return your response as a JSON object with the following structure:
{{
  "summary": "Write a clear summary that captures the main discussion points, decisions, and speaker interactions. Include speaker attribution for key statements when relevant.",
  "action_items": ["Action item with owner if mentioned (e.g., 'Speaker 01: Review the proposal')", "Second action item if any"]
}}

If there is no meaningful content, return:
{{
  "summary": "No meaningful content found.",
  "action_items": []
}}

Example action item formats:
- "Speaker 01: Complete the project report by Friday"
- "Review budget proposal (discussed by Speaker 02)"
- "Schedule follow-up meeting"

Focus on extracting value from the speaker-separated conversation structure."""


class Summarizer:
    """
    Summarize and generate actionable insights from meeting transcriptions.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini", temperature=0.3, max_completion_tokens=1000
        )

    def summarize_transcription(
        self, transcription: List[DiarizationResult]
    ) -> MeetingSummary:
        try:
            # Extract text and calculate metrics
            transcription_text = transcription_to_markdown(transcription)
            word_count = len(transcription_text.split())

            summary = MeetingSummary(
                summary="No meaningful content found.", word_count=word_count
            )

            if not transcription_text:
                return summary

            # Estimate duration (rough approximation: 150 words per minute average speaking rate)
            estimated_duration = max(1, word_count / 150)

            logger.info(
                f"Generating summary for {word_count} words (~{estimated_duration:.1f} min)"
            )

            # Generate summary
            json_parser = JsonOutputParser(pydantic_object=MeetingSummary)
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", summarize_system_prompt),
                    ("user", "Meeting transcript:\n\n{transcription}"),
                ]
            )

            chain = prompt_template | self.llm | json_parser

            response = chain.invoke({"transcription": transcription_text})

            # Parse JSON response
            if not isinstance(response, dict):
                raise ValueError("Response is not a valid JSON object")

            summary.summary = response.get("summary", "No meaningful content found.")
            summary.action_items = response.get("action_items", [])
            logger.info("Summary generated successfully")
        except ValueError as e:
            logger.error(f"Validation error in summarization: {str(e)}")
            summary.summary = f"❌ Configuration error: {str(e)}"
        except Exception as e:
            logger.error(f"Error summarizing transcription: {str(e)}")
            summary.summary = f"❌ Error generating summary: {str(e)}"
        finally:
            return summary
