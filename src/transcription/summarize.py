import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from src.transcription.models import TranscriptionEntry, MeetingSummary
from src.utils import get_transcription_text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

summarize_system_prompt = """The following English text is a mechanical transcription of a conversation during a meeting.
From this transcript, please extract a summary and action items.
Transcription errors to closely pronounced words should be corrected, and fillers and rephrasing should be ignored.
The summary should include only proper nouns or the content of the discussion, and should not be supplemented with general knowledge or known facts.
Action items should only include items explicitly mentioned by participants, and should not include speculation.

Return your response as a JSON object with the following structure:
{
  "summary": "Write a clear summary in sentence form, not a list of words",
  "action_items": ["First action item if any", "Second action item if any"]
}

If there is no meaningful content, return:
{
  "summary": "No meaningful content found.",
  "action_items": []
}"""


class Summarizer:
    """
    Summarize and generate actionable insights from meeting transcriptions.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini", temperature=0.3, max_completion_tokens=1000
        )

    def summarize_transcription(
        self, transcription: List[TranscriptionEntry]
    ) -> MeetingSummary:
        try:
            # Extract text and calculate metrics
            transcription_text = get_transcription_text(transcription)
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

            return summary

        except ValueError as e:
            logger.error(f"Validation error in summarization: {str(e)}")
            return MeetingSummary(summary=f"❌ Configuration error: {str(e)}")
        except Exception as e:
            logger.error(f"Error summarizing transcription: {str(e)}")
            return MeetingSummary(summary=f"❌ Error generating summary: {str(e)}")
