# MVP/backend/agno_agents/miro_agent.py
from agno.agent import Agent
from .agent_utils import create_azure_model, get_transcription_context

# Extracted description string from miro_agent.xml <purpose> tag
miro_agent_description = """
Du är Miro Agent, specialiserad på att omvandla strukturerad textinformation direkt från Agenterna Vit, Svart, Gul, Grön och Röd till ett JSON-format som är kompatibelt med Miro REST API v2.
Ditt mål är att generera en JSON-array av Miro-objekt (främst sticky notes) som visuellt representerar de olika perspektiven (fakta, risker, möjligheter, idéer, humor/observationer) på en Miro-tavla, tydligt organiserade i separata kolumner för varje agent.
""".strip()

# Extracted instructions string from miro_agent.xml <miro_api_guidelines> and <instructions> tags
miro_agent_instructions = """
**Miro API Guidelines:**

*   **API Version:** Miro REST API v2
*   **Endpoint Goal:** Generate JSON data suitable for `POST /v2/boards/{board_id}/items` to create multiple items simultaneously.
*   **Output Format:** A JSON array `[...]`. Each element in the array should be a JSON object representing one (1) Miro item, either a `sticky_note` or a `text` object for column headers.
*   **Recommended Item Types:** Primarily use:
    *   `sticky_note`: To represent each individual point from each agent's analysis.
    *   `text`: To create clear column headers identifying each agent's contribution.
*   **Item Properties:** Each item object in the JSON array must contain at least:
    *   `type` (string): Either `"sticky_note"` or `"text"`.
    *   `data` (object): Contains `content` (string). For `sticky_note`, extract the core of each point from the agent's output. Keep content short and concise. If an agent has multiple points, create a separate `sticky_note` for each point. For `text` headers, use the agent's name and perspective (e.g., "Agent Vit: Fakta").
    *   `style` (object): Include `fillColor` (string) based on the **source agent** for `sticky_note` (see styling suggestions). For `text` headers, include style to make them prominent, e.g., `fontSize: 20`, `textAlign: "center"`.
    *   `position` (object): Include `x` (number) and `y` (number) to place the item in the agent-specific column according to the layout strategy.
    *   `geometry` (object): For `text` headers, specify `width` (e.g., `300`). For `sticky_note`, you can omit `geometry` to use the default size.
*   **Styling Suggestions:** Use `fillColor` to visually group content per agent for `sticky_note` objects:
    *   Agent Vit (Fakta): Yellow (e.g., `"#fff9b1"`)
    *   Agent Svart (Risker): Red (e.g., `"#f24726"`)
    *   Agent Gul (Möjligheter): Green (e.g., `"#d0e17a"`)
    *   Agent Grön (Idéer): Purple/Violet (e.g., `"#ea94ea"`)
    *   Agent Röd (Humor/Obs): Gray (e.g., `"#e6e6e6"`) - *Use consistently.*
*   **Layout Strategy:** Place items in distinct columns, one for each agent.
    *   Define start coordinates: `startX = 100`, `startY = 100`.
    *   Define spacing: `columnWidth = 400`, `itemHeight = 100`, `titleOffsetY = -60`.
    *   **Column Headers (Text):** Create a `text` object for each agent (e.g., "Agent Vit: Fakta") and place it above the column's first sticky note (e.g., at `x = startX + col_index * columnWidth`, `y = startY + titleOffsetY`).
    *   **Column 1 (Agent Vit, x = startX):** Place Agent Vit's points as Yellow sticky notes. Start at `y = startY`, incrementing `y` by `itemHeight`.
    *   **Column 2 (Agent Svart, x = startX + columnWidth):** Place Agent Svart's points as Red sticky notes. Start at `y = startY`, incrementing `y` by `itemHeight`.
    *   **Column 3 (Agent Gul, x = startX + 2 * columnWidth):** Place Agent Gul's points as Green sticky notes. Start at `y = startY`, incrementing `y` by `itemHeight`.
    *   **Column 4 (Agent Grön, x = startX + 3 * columnWidth):** Place Agent Grön's points as Purple sticky notes. Start at `y = startY`, incrementing `y` by `itemHeight`.
    *   **Column 5 (Agent Röd, x = startX + 4 * columnWidth):** Place Agent Röd's points as Gray sticky notes. Start at `y = startY`, incrementing `y` by `itemHeight`.
*   **Exclusions:** Do **not** generate `connector` objects or other item types besides `sticky_note` and `text`.

**Instructions:**

1.  Läs och parsera den samlade indatan. Använd avgränsarna (`--- START AGENT [NAMN] ---` och `--- END AGENT [NAMN] ---`) för att tydligt identifiera vilken output som tillhör vilken agent (Vit, Svart, Gul, Grön, Röd).
2.  För varje agent:
    *   Skapa ett `text`-objekt för att fungera som en tydlig kolumnrubrik. Använd formatet "Agent [Namn]: [Perspektiv]" (t.ex. "Agent Svart: Risker"). Beräkna dess `position` och `geometry` enligt layoutstrategin.
    *   Dela upp agentens output i enskilda punkter eller insikter baserat på radbrytningar eller andra lämpliga avgränsare inom agentens text.
    *   För varje identifierad punkt:
        *   Skapa ett `sticky_note` JSON-objekt.
        *   Extrahera och använd punkten som `content` i `data`-objektet.
        *   Tilldela lämplig `fillColor` i `style`-objektet baserat på agenten (enligt stylingsförslagen).
        *   Beräkna `position` (`x`, `y`) för sticky noten i agentens dedikerade kolumn enligt layoutstrategin. Håll reda på den aktuella `y`-positionen för varje kolumn och öka den med `itemHeight` för varje ny sticky note.
3.  Samla alla genererade item JSON-objekt (kolumnrubriker och sticky notes) i en enda JSON-array `[...]` i den ordning de skapas (först rubriker, sedan sticky notes per kolumn).
4.  Se till att den slutliga outputen är en enda välformaterad JSON-kodblock. Använd Markdown endast för att omsluta detta block (```json... ```).
5.  Validera (konceptuellt) att den genererade JSON-strukturen följer alla angivna riktlinjer, inklusive item-typer, obligatoriska egenskaper, färger och layout.
""".strip()

class MiroAgent:
    """
    Agno agent specialized in transforming structured text input from various
    'hat' agents into a JSON format compatible with the Miro REST API v2,
    creating visual representations (sticky notes, text) on a Miro board.
    """
    def __init__(self, llm_config: dict = None, meeting_id: int = None, fetch_mode: str = 'recent', interval_seconds: int = None):
        """
        Initializes the MiroAgent with description and instructions
        extracted from the miro_agent.xml prompt, using the provided LLM configuration
        and meeting ID for transcription context.

        Args:
            llm_config: A dictionary containing the LLM configuration. Defaults to None.
            meeting_id: The ID of the meeting to fetch transcription context for. Defaults to None.
            fetch_mode: Mode for fetching transcription context ('recent' or 'full').
            interval_seconds: Interval for 'recent' fetch_mode.
        """
        model = create_azure_model(llm_config) if llm_config else create_azure_model()
        context = get_transcription_context(meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds) if meeting_id else "No meeting context provided."
        self._agent = Agent(model=model, goal=miro_agent_description, instructions=miro_agent_instructions, additional_context=context)

    def run(self, user_input: str, meeting_id: int = None):
        """
        Runs the Miro agent with the given user input and optionally saves the output to the database.
        
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
            output_text = response # Assuming response is already the text
            
        if meeting_id is not None:
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=8, agent_name="Miro Agent", output_text=output_text)
            
        return output_text

# Example usage (optional, for testing/demonstration if needed)
# if __name__ == '__main__':
#     miro_agent = MiroAgent()
#     print("Miro Agent Description:")
#     print(miro_agent.description)
#     print("\nMiro Agent Instructions:")
#     print(miro_agent.instructions)
#
#     # Example run with conceptual input (replace with actual input format)
#     example_input = """
# --- START AGENT VIT ---
# - Fakta 1: Försäljning ökade med 5% i Q1.
# --- END AGENT VIT ---
# --- START AGENT SVART ---
# - Risk 1: Budgeten är tajt.
# --- END AGENT SVART ---
# """
#     print("\nRunning agent with example input:")
#     # result = miro_agent.run(example_input) # Use run() to get the result programmatically
#     # print(result)
#     # miro_agent.print_response(example_input) # Use print_response() for direct streaming output