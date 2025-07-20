import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from src.transcription.models import TranscriptionEntry, MeetingSummary
from src.transcription.prompts import summarize_system_prompt
from src.utils import get_transcription_text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

            # Generate summary using LangChain
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", summarize_system_prompt),
                    (
                        "user",
                        "Meeting duration: {duration} minutes\nWord count: {word_count} words\n\nPlease analyze this meeting transcription and provide a structured summary:\n\n{transcription}",
                    ),
                ]
            )

            chain = prompt_template | self.llm | StrOutputParser()

            response = chain.invoke(
                {
                    "transcription": transcription_text,
                    "word_count": word_count,
                    "duration": f"{estimated_duration:.1f}",
                }
            )

            # Split by section headers
            parts = response.split("## ")
            for part in parts:
                if not part.strip():
                    continue
                part = part.strip()
                if part.startswith("Summary"):
                    summary.summary = part.replace("Summary", "", 1).strip()
                elif part.startswith("Key Takeaways"):
                    summary.key_takeaways = part.replace("Key Takeaways", "", 1).strip()
                elif part.startswith("Action Items"):
                    summary.action_items = part.replace("Action Items", "", 1).strip()
                else:
                    summary.summary = part

            logger.info("Summary generated successfully")

            return summary

        except ValueError as e:
            logger.error(f"Validation error in summarization: {str(e)}")
            return MeetingSummary(summary=f"❌ Configuration error: {str(e)}")
        except Exception as e:
            logger.error(f"Error summarizing transcription: {str(e)}")
            return MeetingSummary(summary=f"❌ Error generating summary: {str(e)}")
