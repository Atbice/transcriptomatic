# MVP/backend/agno_agents/red_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context


description = """
"Du är Agent Röd, en segmentbaserad skämtgenerator som specialiserar sig på galen humor och pappaskämt. "
"Din uppgift är att analysera mötesprotokoll, identifiera tydliga diskussionssegment och generera två typer av skämt för varje segment."
        """

instructions = """
"Skämten måste direkt relatera till innehållet, personerna eller situationen i det specifika segmentet.\n"
"För varje segment, generera två skämt: ett galet skämt och ett pappaskämt.\n"
"Galet skämtet ska vara absurt och oväntat.\n"
"Pappaskämten Ska vara enkelt, gärna en ordvits. Helt harmlösa\n"
"Presentera allt i markdown format.\n"
"Presentera resultatet tydligt med varje segment namngivet och skämten märkta som \"Galet:\" och \"Pappaskämt:\"."
        """


class RedHatAgent:
    """
    Agent Röd: Generates edgy/absurd jokes and dad jokes based on meeting transcript segments.
    Specializes in analyzing meeting protocols, identifying discussion segments,
    and generating two types of jokes for each segment.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the RedHatAgent with predefined description and instructions,
        using the provided LLM configuration and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """


        model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."
        self._agent = Agent(model=model, goal=description, instructions=instructions, additional_context=context,
            markdown=True  )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the RedHatAgent with the given user input and optionally saves the output to the database.
        
        Args:
            user_input: The input string for the agent.
            meeting_id: Optional. The ID of the meeting to associate the output with. If provided, the output will be saved to the database.

        Returns:
            The response content as a string from the internal Agno Agent.
        """
        response = self._agent.run(user_input=user_input)
        # Extract content from RunResponse object if it has a content attribute
        if hasattr(response, 'content'):
            output_text = response.content
        else:
            output_text = response
        
        if meeting_id is not None:
            # Assuming agent_id for RedHatAgent is 2 (needs to be defined consistently)
            # Agent names should also be consistent.
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=2, agent_name="Red Hat", output_text=output_text)
            
        return output_text
