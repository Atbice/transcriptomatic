# MVP/backend/agno_agents/purple_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context

# Description extracted from <purpose> in purble_hat.xml
description = """Du är Agent Lila, en specialiserad frågegenerator. Ditt enda syfte är att analysera utdata från Agenterna Vit (Fakta), Svart (Risker), Gul (Möjligheter), Grön (Kreativa Idéer), och Röd (Humor) och baserat på dessa analyser, generera **så många relevanta frågor som möjligt**.
Målet är att identifiera alla områden som kräver ytterligare klargörande, diskussion, kritisk granskning, beslutsfattande eller utforskning inför kommande möten eller arbete. Du ska **inte** syntetisera eller besvara frågorna, endast generera dem."""

# Instructions extracted and concatenated from <instruction> tags in purble_hat.xml
instructions = """Du kommer att få utdata från Agenterna Vit, Svart, Gul, Grön och Röd, alla baserade på samma mötesprotokoll. Utgå från att denna indata är tydligt strukturerad eller separerad per agent.
Granska **alla** mottagna agentutdata noggrant för att identifiera potentiella frågeställningar.
Generera frågor baserade på **alla** typer av insikter från agenterna:
- **Från Vit (Fakta):** Frågor kring obesvarade punkter, åtgärder utan ägare/deadline, identifierade informationsluckor, tvetydiga data eller beslut som saknar tydlig motivering i protokollet.
- **Från Svart (Risker):** Frågor om hur risker ska hanteras/mitigeras, om grundantaganden bakom svagheter, om konsekvensanalyser, om alternativa vägar för att undvika brister, och om plan B för identifierade utmaningar.
- **Från Gul (Möjligheter):** Frågor om hur möjligheter bäst kan realiseras, hur styrkor kan utnyttjas maximalt, hur man bygger vidare på enighet/entusiasm, och vilka konkreta steg som krävs för att utforska potential.
- **Från Grön (Kreativa Idéer):** Frågor om genomförbarheten/värdet av nya idéer, om implikationerna av "Tänk Om"-scenarier, om hur man kan testa/pilota kreativa förslag, och om hur idéer kan anpassas för att lösa specifika problem.
- **Från Röd (Humor):** Frågor som (med försiktighet) utforskar *varför* vissa ämnen genererade skämt (indikerar det känslighet, förvirring, starka åsikter?) eller om innehållet i ett skämt oavsiktligt belyste en relevant fråga.
Sträva efter att generera **många** frågor. Hellre en fråga för mycket än en för lite, så länge den är relevant till någon av agenternas analyser.
Formulera frågorna så att de är öppna och uppmuntrar till diskussion och eftertanke.
Strukturera den genererade frågelistan genom att kategorisera frågorna. Använd de föreslagna kategorierna nedan, eller skapa andra logiska grupperingar om det passar materialet bättre.
Presentera den kategoriserade listan i markdown format."""

class PurpleHatAgent:
    """
    Agent Lila (Purple Hat): Generates clarifying and exploratory questions
    based on the analysis outputs from White, Black, Yellow, Green, and Red hat agents.
    Its sole purpose is to generate questions, not answer them.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the Purple Hat Agent (Agent Lila), using the provided LLM configuration and meeting ID for transcription context.

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
            goal=description,
            instructions=instructions,
            additional_context=context,
            markdown=True  
        )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Purple Hat Agent with the given user input and optionally saves the output to the database.
        
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
            save_agent_output(meeting_id=meeting_id, agent_id=7, agent_name="Purple Hat", output_text=output_text)
            
        return output_text

# Example usage block (optional, for testing)
# if __name__ == '__main__':
#     # This assumes the environment (e.g., API keys for the model) is set up correctly
#     # You would need to provide a valid llm_config dictionary here
#     # For example: llm_config = {"api_key": "YOUR_API_KEY", "model_name": "gpt-4"}
#     # agent = PurpleHatAgent(llm_config={}) # Replace with actual config
#     # print(f"Initialized {agent.__class__.__name__}")
#     # print(f"Description: {description}")
#     # print(f"Instructions: {instructions}") # Can be long
#     # print(f"Using model: {agent._agent.model}")

#     # Example input mimicking the structure expected by the agent's instructions
#     example_input = """
#     **Agent Vit (Fakta):**
#     - Åtgärd 'Skapa rapport X' saknar deadline.
#     - Data för Q3 försäljning är preliminär.
#     - Beslut om leverantör Y togs utan dokumenterad motivering.

#     **Agent Svart (Risker):**
#     - Risk: Beroende av enskild utvecklare for modul Z.
#     - Svaghet: Otydlig kommunikationsplan internt.
#     - Brist: Saknar fallback-lösning for API-integration.

#     **Agent Gul (Möjligheter):**
#     - Möjlighet: Ny marknad W oppnar sig nasta kvartal.
#     - Styrka: Starkt kundengagemang pa sociala medier.

#     **Agent Gron (Kreativa Ideer):**
#     - Ide: Gamifiera onboarding-processen.
#     - Tank Om: Vad hander om vi dubblar marknadsforingsbudgeten?

#     **Agent Rod (Humor):**
#     - Skamt om hur lang tid projekt Z tar (kopplat till utvecklarberoende).
#     """

#     # print("\n--- Running Agent Lila with example input ---")
#     # try:
#     #     # Use print_response for streaming output as requested by instructions (markdown)
#     #     # agent._agent.print_response(example_input, stream=True)

#     #     # Or use run() to get the result as a string
#     #     # result = agent.run(example_input)
#     #     # print("\n--- Agent Result ---")
#     #     # print(result)
#     # except Exception as e:
#     #     print(f"\n--- Error running agent ---")
#     #     print(f"An error occurred: {e}")
#     #     print("Ensure your API key and model configuration are correct.")