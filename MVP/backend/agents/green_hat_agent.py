# MVP/backend/agno_agents/green_hat_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context


# Original role text from XML: "Du är Agent White, en expert på kreativ katalysering, specialiserad på att generera innovativa idéer och alternativa lösningar baserade på mötesprotokoll. Din roll är att utforska nya perspektiv, brainstorma kreativa tillvägagångssätt, föreslå okonventionella lösningar och stimulera nytänkande kring de diskuterade ämnena."
DESCRIPTION = """Agent Green: Expert på kreativ katalysering, specialiserad på att generera innovativa idéer och alternativa lösningar baserade på mötesprotokoll. Rollen är att utforska nya perspektiv, brainstorma kreativa tillvägagångssätt, föreslå okonventionella lösningar och stimulera nytänkande kring de diskuterade ämnena."""

INSTRUCTIONS = """Läs det tillhandahållna mötesprotokollet noggrant.
Granska mötesprotokollet noggrant.
Identifiera nyckelproblem, mål och idéer från mötet.
Brainstorma nya idéer:
Alternativa lösningar som inte nämndes.
Kreativa sätt att tackla utmaningar, inspirerade av risker/svagheter.
Okonventionella vägar till målen.
Skapa "Tänk om...?"-scenarier för bredare perspektiv.
Formulera två öppna frågor för att utforska idéerna vidare.
Presentera i markdown, enligt angiven struktur."""

class GreenHatAgent:
    """
    Agno Agent implementation for the Green Hat role (Kreativ Katalysering).
    Focuses on creative catalysis, generating innovative ideas, alternative solutions,
    and stimulating new thinking based on meeting protocols.
    """
    def __init__(self, llm_config: dict, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the GreenHatAgent with predefined description and instructions,
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
            markdown=True  # Ensure markdown formatting is enabled
        )

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Green Hat agent with the given user input and optionally saves the output to the database.
        
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
            save_agent_output(meeting_id=meeting_id, agent_id=4, agent_name="Green Hat", output_text=output_text)
            
        return output_text

# Example usage block (can be uncommented for direct testing)
# if __name__ == '__main__':
#     # This assumes the script is run in an environment where sibling imports work
#     # and necessary configurations (like API keys for the model) are set up.
#     try:
#         green_agent = GreenHatAgent()
#         print("Green Hat Agent Initialized")
#         print("\nDescription:")
#         print(green_agent.description)
#         # print("\nInstructions:") # Instructions are quite long
#         # print(green_agent.instructions)
#         print(f"\nUsing Model: {green_agent.model_config.get('model', 'Not specified')}")
#
#         # Example run with a dummy prompt (replace with actual meeting summary)
#         # meeting_summary_prompt = """
#         # Mötesprotokoll:
#         # Teamet diskuterade att lansera Projekt "Odyssé" i Q3 med en budget på 150 000 kr via ett traditionellt pressmeddelande.
#         # Målet är att öka marknadsandelen med 2%.
#         # En nylig rapport visade en 10% minskning i webbtrafik, vilket ses som en utmaning.
#         # En risk med budgeten identifierades.
#         # """
#         # print("\n--- Running Agent (Example) ---")
#         # # Use print_response for streaming output or run() to get the result string
#         # # Note: Running this requires the agno library and potentially API keys configured.
#         # # green_agent.print_response(meeting_summary_prompt)
#         # result = green_agent.run(meeting_summary_prompt)
#         # print("\nAgent Result (non-streaming):")
#         # print(result)
#
#     except ImportError as e:
#         print(f"ImportError: {e}. Make sure necessary libraries are installed and paths are correct.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         print("Ensure API keys and model configurations are correctly set up in BaseAgnoAgent or environment.")