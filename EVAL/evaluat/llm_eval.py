# ./EVAL/evaluation/llm_eval.py
import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

PROMPT_TEMPLATE = """
Du utvärderar resultatet från en tal-till-text-modell. Jämför Modelltranskriptionen med Referenstranskriptionen baserat på följande kriterier:

**Referenstranskription**:
{reference}

**Modelltranskription**:
{model}

Betygsätt Modelltranskriptionen från 1 (Mycket Dålig) till 10 (Utmärkt) på följande dimensioner, genom att jämföra den med Referenstranskriptionen:

1.  **Kontextuell Korrekthet (1-10)**:
    * **Definition**: Behåller Modelltranskriptionen den ursprungliga innebörden och avsikten från Referenstranskriptionen, även om formuleringen skiljer sig? Betyget 10 innebär att meningen är helt bevarad. Betyget 1 innebär att meningen är förlorad eller kraftigt förvrängd.
    * **Beakta**: Får lyssnaren samma förståelse? Förmedlas nyckelpunkter korrekt? Är huvudbudskapet detsamma? Fokusera på semantisk innebörd.

2.  **Övergripande Förståelse (1-10)**:
    * **Definition**: Lyckas Modelltranskriptionen fånga huvudpunkterna och det övergripande syftet från Referenstranskriptionen? Betyget 10 innebär att kärnbudskapet är fullständigt förstått. Betyget 1 innebär att kärnbudskapet till stor del saknas eller är oklart.
    * **Beakta**: Fångar Modelltranskriptionen essensen? Är den viktigaste informationen (som namn, datum, nummer, viktiga handlingar) närvarande och korrekt? Detta fokuserar på förmedlingen av *huvudidéerna*.

Returnera utvärderingen i exakt detta JSON-format, och se till att alla betyg är heltal mellan 1 och 10:

{{
  "kontextuell_korrekthet": <int 1-10>,
  "overgripande_forstaelse": <int 1-10>,
  "kommentar": "<Ge en kortfattad motivering på en mening som sammanfattar betygen. Håll det kort.>"
}}
"""

class LLMEvaluator:
    """
    A class to evaluate transcription pairs using Azure OpenAI.
    """
    def __init__(self):
        """
        Initializes the LLMEvaluator by loading environment variables
        and setting up the Azure OpenAI client.
        """
        load_dotenv()
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

        if not all([self.api_key, self.endpoint, self.deployment]):
            raise RuntimeError("Missing Azure OpenAI credentials in .env.")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )

    def evaluate_pair(self, reference: str, model: str):
        """
        Evaluates a single pair of reference and model transcriptions
        using the configured Azure OpenAI client and prompt template.

        Args:
            reference: The reference transcription string.
            model: The model transcription string.

        Returns:
            A dictionary containing the evaluation results if successful,
            otherwise None.
        """
        prompt = PROMPT_TEMPLATE.format(reference=reference, model=model)
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
            )
            content = response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Failed to get response from OpenAI API: {e}")
            return None

        result = None
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            print("[WARN] Failed to parse JSON directly. Attempting extraction. Content was:\n", content)
            # Try to extract up to the last closing brace
            last_brace = content.rfind('}')
            if last_brace != -1:
                possible_json = content[:last_brace+1]
                try:
                    result = json.loads(possible_json)
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse extracted JSON. Skipping. Content was:\n", possible_json)
                    return None
            else:
                print("[ERROR] No JSON object found in model response. Skipping. Content was:\n", content)
                return None
        except Exception as e:
             print(f"[ERROR] An unexpected error occurred during JSON parsing: {e}. Content was:\n", content)
             return None

        # Check if the parsed JSON is a dictionary and contains the expected keys
        if isinstance(result, dict) and all(key in result for key in ["kontextuell_korrekthet", "overgripande_forstaelse", "kommentar"]):
            return result
        else:
            print("[ERROR] Parsed JSON does not contain expected keys or is not a dictionary. Skipping. Content was:\n", result)
            return None
