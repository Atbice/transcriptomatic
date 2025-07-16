# MVP/backend/agno_agents/black_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context

# Extracted from black_hat.xml
AGENT_GOAL = """Du är Agent Black, den Kritiska Analytikern, och specialiserar dig på att 
identifiera risker, svagheter och potentiella brister i planer och beslut baserat på mötesprotokoll. 
Din roll är att agera som riskbedömare och djävulens advokat, med fokus på vad som kan gå fel, 
varför idéer kanske inte fungerar, och hur man kan stärka planerna."""

AGENT_INSTRUCTIONS = """Läs det tillhandahållna mötesprotokollet noggrant.
Identifiera potentiella risker, hinder, barriärer eller negativa konsekvenser kopplade till de 
diskuterade besluten, planerna eller idéerna.
Peka ut logiska felslut, antaganden som saknar underlag, saknade steg eller resurskonflikter.
Ifrågasätt genomförbarheten eller praktiska aspekter av förslagen och belys vad som kan gå fel.
För de mest signifikanta riskerna eller svagheterna, föreslå kortfattat områden som behöver ytterligare 
diskussion eller potentiella mitigeringsstrategier.
Fokusera kritiken och förslagen på innehållet i diskussionen, inte på de inblandade personerna.
Baserat på din analys, formulera två specifika, öppna frågor som syftar till att förbättra nästa möte 
eller klargöra kritiska punkter från detta protokoll.
Presentera allt i markdown format.
Strukturera din analys enligt de definierade sektionerna, och inkludera en separat sektion för uppföljningsfrågorna."""

class BlackHatAgent:
    """
    Agent Black: The Critical Analyst. Specializes in identifying risks,
    weaknesses, and potential flaws in plans and decisions based on meeting minutes.
    Acts as a risk assessor and devil's advocate.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the BlackHatAgent with predefined description and instructions,
        using the provided LLM configuration and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """
        # Instantiate the model
        self._model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."

        # Instantiate the Agno Agent
        self._agent = Agent(
            model=self._model,
            goal=AGENT_GOAL,
            instructions=AGENT_INSTRUCTIONS,
            additional_context=context,
            markdown=True  
        )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Black Hat Agent with the given user input and optionally saves the output to the database.
        
        Args:
            user_input: The input string for the agent.
            meeting_id: Optional. The ID of the meeting to associate the output with. If provided, the 
            output will be saved to the database.

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
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=6, agent_name="Black Hat", output_text=output_text)
            
        return output_text
