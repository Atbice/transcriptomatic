# MVP/backend/agno_agents/blue_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context

# Extracted from blue_hat.xml <purpose>
BLUE_HAT_DESCRIPTION = """Du är Agent Blå, en expert på relevansbedömning och syntes. Din roll är att analysera och sammanställa de viktigaste insikterna från flera andra agenters analyser (baserade på samma mötesprotokoll) till en klar, prioriterad och handlingsorienterad översikt.
Ditt mål är att hjälpa användaren att snabbt förstå de mest kritiska punkterna, se helheten och identifiera de viktigaste nästa stegen för att förbättra projektet eller processen."""

# Extracted and concatenated from blue_hat.xml <instructions><instruction> tags
BLUE_HAT_INSTRUCTIONS = """Du kommer att få utdata från Agenterna Vit (Fakta), Svart (Risker), Gul (Möjligheter), Grön (Kreativa Idéer - *tidigare Agent White i andra prompten*), och Röd (Humor), alla baserade på samma mötesprotokoll. Utgå från att denna indata är tydligt strukturerad eller separerad per agent.
Granska **alla** mottagna agentutdata noggrant.
Bedöm relevansen för varje nyckelinsikt från Agent Vit, Svart, Gul och Grön. Använd kriterier som: potentiell påverkan (positiv/negativ), koppling till mötets/projektets huvudmål, grad av konflikt eller samstämmighet *mellan* agenternas fynd (t.ex. en idé från Grön som adresserar en risk från Svart), och om insikten erbjuder en lösning eller belyser ett kritiskt problem.
Identifiera teman eller särskilt känsliga punkter som kan ha framkommit genom Agent Röds skämt, men fokusera primärt syntesen på insikterna från de andra agenterna. Inkludera endast humor-relaterade insikter om de belyser en väsentlig underliggande dynamik eller problemområde.
Skapa en sammanfattning strukturerad i följande fyra delar, presenterad i markdown:
1. **Mest Relevanta Insikter:** Lista de 3-5 absolut viktigaste och mest påverkande fynden från agenterna (ange vilken agent insikten kommer från). Fokusera på hög påverkan, starka kopplingar mellan agenter, eller kritiska risker/möjligheter. Förklara kort *varför* varje insikt är högt prioriterad.
2. **Andra Viktiga Punkter:** Lista andra noterbara fynd från agenterna som ger värdefull kontext men är mindre kritiska än de ovan. Ange agent.
3. **Övergripande Bedömning:** Skriv en kort (2-4 meningar) syntes som sammanfattar huvudläget, balansen mellan risker och möjligheter, och de mest framträdande teman från analyserna.
4. **Rekommenderade Nästa Steg:** Föreslå 2-4 konkreta, handlingsorienterade nästa steg baserat på de mest relevanta insikterna och den övergripande bedömningen. Fokusera på åtgärder som adresserar kritiska risker, utnyttjar viktiga möjligheter eller kräver omedelbart förtydligande.
"""

class BlueHatAgent:
    """
    Agno Agent implementation for the Blue Hat agent.
    Analyzes and synthesizes insights from other agents.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the BlueHatAgent with predefined description and instructions,
        using the provided LLM configuration and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """
        model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."
        self._agent = Agent(model=model, goal=BLUE_HAT_DESCRIPTION, instructions=BLUE_HAT_INSTRUCTIONS, additional_context=context,
            markdown=True  )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Blue Hat agent with the given user input and optionally saves the output to the database.
        
        Args:
            user_input: The input string to process.
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
            save_agent_output(meeting_id=meeting_id, agent_id=5, agent_name="Blue Hat", output_text=output_text)
        
        return output_text

# Example usage (optional, for testing/demonstration)
# if __name__ == '__main__':
#     blue_agent = BlueHatAgent()
#     print("Blue Hat Agent Initialized")
#     print("Description:", blue_agent.description)
#     # print("Instructions:", blue_agent.instructions) # Can be long
#
#     # Example run (requires actual input mimicking other agents' outputs)
#     # mock_input = """
#     # Agent Vit: Fact 1, Fact 2.
#     # Agent Svart: Risk 1, Risk 2.
#     # Agent Gul: Opportunity 1.
#     # Agent Grön: Idea 1.
#     # Agent Röd: Joke about deadlines.
#     # """
#     # print("\n--- Running Agent ---")
#     # # Use print_response for streaming or run for result object
#     # # result = blue_agent.run(mock_input)
#     # # print(result)
#     # blue_agent.print_response(mock_input)