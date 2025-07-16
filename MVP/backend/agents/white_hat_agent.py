# MVP/backend/agno_agents/white_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context
import logging

DESCRIPTION = """Du är Agent White, en strikt objektiv datainsamlare. Din uppgift är att extrahera
 och strukturera verifierbara fakta från mötestranskriptioner utan tolkning, åsikter eller känslor.
   Rapportera endast vad som explicit sagts eller dokumenterats."""

INSTRUCTIONS = """Läs transkriptionen noggrant.
Extrahera och lista explicit nämnda:
    Viktiga fakta
    Datapunkter (siffror, datum, statistik)
    Beslut
    Åtgärder (med ansvarig och deadline om angivet)
    Mål eller problem
    Frågor (notera om besvarade)
    Saknad information eller behov av undersökning
Presentera i markdown under rubrikerna:
    Fakta
    Data
    Beslut
    Åtgärder
    Mål/Problem
    Frågor
    Informationsluckor
Formulera två neutrala frågor baserat på extraherad information (t.ex. åtgärder utan deadline, obesvarade frågor, informationsluckor) för att belysa nästa steg eller förtydliganden.
Inkludera inga slutsatser, bedömningar eller förklaringar."""


class WhiteHatAgent:
    """
    Agent White: Extracts and structures verifiable facts from meeting transcripts
    objectively, without interpretation or opinion. Reports only explicitly
    stated information based on the white_hat.xml prompt.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the WhiteHatAgent with predefined description and instructions,
        using the provided LLM configuration and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """
        model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."
        context_snippet = (context[:200] + '...') if len(context) > 200 else context
        logging.info(f"WhiteHatAgent __init__: meeting_id={meeting_id}, fetch_mode='{fetch_mode}', interval_seconds={interval_seconds}. additional_context snippet: {context_snippet}")
        self._agent = Agent(
            model=model,
            goal=DESCRIPTION.strip(),
            instructions=INSTRUCTIONS.strip(),
            additional_context=context,
            markdown=True  
        )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the WhiteHatAgent with the given user input and optionally saves the output to the database.
        
        Args:
            user_input: The input string for the agent.
            meeting_id: Optional. The ID of the meeting to associate the output with. If provided, the output will be saved to the database.
        
        Returns:
            The response content as a string from the internal Agno Agent.
        """
        user_input_snippet = (user_input[:200] + '...') if len(user_input) > 200 else user_input
        logging.info(f"WhiteHatAgent run: meeting_id={meeting_id}. user_input snippet: {user_input_snippet}")
        response = self._agent.run(user_input=user_input)
        # Extract content from RunResponse object if it has a content attribute
        if hasattr(response, 'content'):
            output_text = response.content
        else:
            output_text = response
        
        if meeting_id is not None:
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=1, agent_name="White Hat", output_text=output_text)
        
        return output_text

