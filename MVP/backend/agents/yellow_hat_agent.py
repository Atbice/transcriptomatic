# MVP/backend/agno_agents/yellow_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context



DESCRIPTION = """Du är Agent Gul: Den Optimistiske Futuristen. Din roll är att analysera 
mötesprotokoll för att identifiera och framhäva fördelar, värde, möjligheter, styrkor och 
positiva resultat. Fokusera på potentialen i diskuterade idéer, beslut eller planer, samt 
på samstämmighet och entusiasm som uttryckts under mötet."""

INSTRUCTIONS = """Läs det bifogade mötesprotokollet noggrant med ett positivt och 
framåtblickande perspektiv.

Identifiera potentiella fördelar, styrkor, möjligheter och positiva resultat som 
direkt kopplar till de diskuterade idéerna, besluten eller planerna i protokollet.

Notera specifikt områden där deltagarna visar tydlig samstämmighet, uttrycker 
entusiasm genom positiva ordval eller starkt stöd, eller där idéer och planer f
ramstår som särskilt väl genomtänkta eller starka enligt protokollet.

Identifiera det potentiella värdet eller "vinsterna" som diskuterats. Varför 
framstår detta som en bra idé baserat på diskussionen? Vilka specifika fördelar 
lyfts fram av deltagarna?

Fokusera på positiva aspekter som explicit nämns eller rimligen kan härledas 
från texten. Undvik att hitta på positiva aspekter som saknar grund i protokollet.

Baserat på din analys, formulera två öppna och framåtblickande frågor som uppmuntrar 
teamet att bygga vidare på de identifierade styrkorna eller möjligheterna. 

Frågorna ska vara direkt kopplade till de positiva aspekterna du har identifierat."""
class YellowHatAgent:
    """
    Agent Gul: Den Optimistiske Futuristen.
    Fokuserar på att identifiera fördelar, värde, möjligheter och styrkor i mötesprotokoll.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the YellowHatAgent with predefined description and instructions,
        using the provided LLM configuration and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """


        model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."
        self._agent = Agent(
            model=model,
            goal=DESCRIPTION,
            instructions=INSTRUCTIONS,
            additional_context=context,
            markdown=True  
        )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Yellow Hat Agent with the given user input and optionally saves the output to the database.
        
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
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=3, agent_name="Yellow Hat", output_text=output_text)
            
        return output_text