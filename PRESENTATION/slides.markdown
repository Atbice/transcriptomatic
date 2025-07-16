---
title: "**Transcriptomatic**" 
sub_title: Evaluering av speech to text modeller
author: Anton Lundström och Robban
theme:
  override:
    footer:
      style: template
      left:
        image: eghed-logo.png
      center: Transcriptomatic
      right: "{current_slide} / {total_slides}"
      height: 3
    palette:
      classes:
        noice: # For your new "Röd Hatt" (Comic relief) or general emphasis
          foreground: red
        svart_hatt: # Original Black Hat (Critical Analysis & Risks)
          foreground: black
        gul_hatt: # Original Yellow Hat (Optimism & Benefits)
          foreground: yellow
        gron_hatt: # Original Green Hat (Creativity & New Ideas)
          foreground: green
        bla_hatt: # For your new "Blå Hatt" (Dirigenten)
          foreground: blue
        lila_hatt: # For your new "Lila Hatt" (Frågegeneratorn)
          foreground: magenta # Standard terminal purple
---



<!-- incremental_lists: true -->
Varför gör vi detta?
==============
* **Utmaningen**: Hitta bästa Tal-till-Text (STT) på Svenska.
* **Varför detta projekt?**
    * Engelska: Gott om högkvalitativa STT-modeller.
    * Svenska: Utbudet är mer begränsat – vilka fungerar bäst *här*?
    * **Vårt fokus:** Hur klarar modellerna av **längre format**? (T.ex. från möten, intervjuer, poddar).
* **Mål**: Ge en tydlig bild av hur bra olika modeller är på att transkribera vid praktisk tillämpning.
<!-- end_slide -->
<!-- incremental_lists: true -->    

Tidig ASR och den statistiska eran (Automatic Speech Recognition)
==============
*  <span class="bla_hatt">**De första stegen**</span> **(1950-tal – tidigt 1970-tal): Banbrytande system**
    * **1952:** Bell Labs "Audrey" – Kände igen talade <span class="noice">**siffror**</span> från en enskild talare.
    * **1962:** IBM:s "Shoebox" – Kände igen <span class="noice">**16 engelska ord**</span> och utförde enkel aritmetik.


* <span class="bla_hatt">**Den statistiska eran**</span> **(1970-tal – 2000-tal): HMM och GMM dominerar**
    * **1970-talet:** DARPA:s SUR-program återupplivade forskningen, siktade på <span class="noice">**1000-ords**</span> vokabulärer.
    * <span class="gron_hatt">**Hidden Markov Models**</span>(HMM): Blev den dominerande metoden. En probabilistisk modell som ser tal som en sekvens av dolda fonetiska enheter.
    * <span class="gron_hatt">**Gaussian Mixture Models**</span>(GMM): Användes med HMM för att modellera distributionen av akustiska särdrag.
    * <span class="gron_hatt">**N-gram**</span> språkmodeller:** Kombinerades med HMM-GMM för att förutsäga sannolikheten för ordsekvenser.
    * **Mitten av 1980-talet:** IBM:s <span class="gron_hatt">**"Tangora"**</span> – Röststyrd skrivmaskin med <span class="noice">**20 000-ords**</span> vokabulär.
    * **1993:** <span class="gron_hatt">**CMU:s Sphinx-II**</span> – Första talaroberoende systemet för kontinuerligt tal med stort ordförråd (LVCSR).
    * **Kännetecken:** Datadrivet, statistiskt angreppssätt, bättre hantering av kontinuerligt tal och större vokabulärer.
*  <span class="bla_hatt">**Djupinlärningens intåg**</span> **(sent 1980-tal – tidigt 2000-tal): Hybridmodeller**
    * **Hybrid DNN-HMM-system:** <span class="gron_hatt">**Deep Neural Networks**</span> (DNN) ersatte GMM för akustisk modellering, vilket förbättrade differentieringen av fonem. HMM bibehölls för temporal modellering.

<!-- end_slide -->
<!-- incremental_lists: true -->
Revolutionen fortsätter: End-to-End-arkitekturer och språkmodellernas intåg
==============
* <span class="bla_hatt">**Mot End-to-End-paradigm**</span> **(tidigt 2000-tal – mitten av 2010-talet):**
    * <span class="gron_hatt">**Connectionist Temporal Classification**</span> (CTC) (2006): Möjliggjorde direkt träning av RNN:er på osegmenterad sekvensdata genom att använda en "blank" symbol och summera över alla möjliga anpassningar. Eliminerade behovet av förjusterad data.
    * <span class="gron_hatt">**Recurrent Neural Networks**</span> (RNN) & LSTM: Förenklade ASR genom att direkt mappa tal till text och hanterade temporala beroenden bättre än tidigare DNN:er. LSTM löste problem med försvinnande/exploderande gradienter.
* <span class="bla_hatt">**End-to-End**</span> **tar över (mitten av 2010-talet – nutid): Nya arkitekturer**
    * <span class="gron_hatt">**Listen, Attend, and Spell**</span> (LAS) (ca 2015-2016): Encoder (Listener) + Uppmärksamhetsbaserad Decoder (Speller). Uppmärksamhetsmekanismen lät dekodern fokusera på relevanta ljudsegment.
    * <span class="gron_hatt">**Transformer-arkitekturen**</span>(ca 2017-nutid): Förlitar sig helt på självuppmärksamhetsmekanismer för att modellera globala beroenden. Mycket parallelliserbar och utmärkt för lång kontext.
    * <span class="gron_hatt">**Recurrent Neural Network Transducer**</span> (RNN-T): Naturligt lämpad för strömmande ASR tack vare monoton, ramvis bearbetning.
    * **Kännetecken:** Förenklade ASR-pipelines (ett enda neuralt nätverk), betydande noggrannhetsförbättringar.
* <span class="bla_hatt">**Stora Språkmodeller**</span> **(LLM) gör entré (sent 2010-tal – nutid): Förbättrad språkförståelse**
    * **Motivering:** Övervinna språkmodelleringsflaskhalsar, utnyttja LLM:ers världskunskap och kontextuella förståelse.
    * **Tidiga integrationsstrategier:**
        * <span class="gron_hatt">**N-bästa omvärdering**</span> (Rescoring): Förtränade LLM:er (BERT, tidiga GPT:er) rangordnar hypoteser från ASR-system.
        * **Efterbearbetning & felkorrigering:** LLM:er "rensar" eller "översätter" ASR-utdata.
    * **Resultat:** Förbättrad hantering av sällsynta ord, kontext, tvetydigheter (t.ex. homofoner) och felkorrigering.



<!-- end_slide -->
<!-- incremental_lists: true -->
Den moderna ASR-eran: LLM-synergi, utmaningar och visioner
=================================================================
* <span class="bla_hatt">**Djupintegration av LLM**</span> **(tidigt 2020-tal – nutid):**
    * <span class="gron_hatt">**Textbaserad:**</span> LLM bearbetar text från ASR (t.ex. generative error correction - GER).
    * <span class="gron_hatt">**Latent representationsbaserad:**</span> Talrepresentationer från en encoder anpassas och matas till en LLM.
    * <span class="gron_hatt">**Ljud-token-baserad:**</span> Tal konverteras till diskreta semantiska eller akustiska "tokens" som LLM:er bearbetar.
    * **Påverkan:** Ytterligare noggrannhetsförbättringar, särskilt i komplexa lingvistiska sammanhang. Förbättrad igenkänning av sällsynta ord och motståndskraft mot brus.
* <span class="bla_hatt">**Aktuella Utmaningar**</span>:
    * **Beräkningseffektivitet:** Särskilt för realtidsanvändning på enheter med begränsade resurser.
    * **Bias och rättvisa:** Hantera och mildra bias i träningsdata och modeller.
    * **Lågresursspråk:** Utveckla högpresterande modeller för språk med begränsad träningsdata.
    * **Robusthet:** Förbättra prestanda i bullriga miljöer och med varierande talstilar.
* <span class="bla_hatt">**Framtida Riktningar och Visioner**</span>:
    * **Optimala integrationsstrategier:** Fortsatt forskning kring hur tal- och språkkomponenter bäst kombineras.
    * **Parameter-Efficient Fine-Tuning (PEFT):** Effektiva metoder (t.ex. LoRA) för att anpassa stora LLM:er.
    * **Tillförlitlighet:** Minska hallucinationer och öka modellernas pålitlighet.
    * **Multimodal förståelse:** System som kan bearbeta och förstå information från flera källor (t.ex. ljud och video).
    * **Konversationell AI:** Mer naturliga och kontextmedvetna dialogsystem.


<!-- end_slide -->
<!-- incremental_lists: true -->
Sammanfattning: KBLab KB-Whisper
==============
- KBLab har utvecklat KB-Whisper, en ny tal-till-text-modell speciellt framtagen för svenska.

    * Den bygger på OpenAIs populära Whisper-modell men har finjusterats på en massiv datamängd om 50 000 timmar svenskt tal (från bland annat TV-textning och riksdagsprotokoll).
    * Resultatet är en kraftig förbättring av prestandan för svensk taligenkänning.
    * Tester visar en genomsnittlig minskning av ordfelet (WER) med hela 47 % jämfört med OpenAIs bästa modell (Whisper-large-v3).
    * En stor fördel är att även mindre KB-Whisper-modeller presterar bättre än OpenAIs större modeller. Detta gör högkvalitativ svensk taligenkänning mer tillgänglig och kostnadseffektiv.
    * Modellerna är fritt tillgängliga via KBLab på HuggingFace.    
- TLDR: KB-Whisper är KBLabs version av Whisper, optimerad för svenska med stora mängder data, vilket ger mycket bättre och effektivare taligenkänning än OpenAIs original för svenskt ljud.

<!-- end_slide -->
<!-- incremental_lists: true -->
Projektets Kärna - Vad undersöker vi?
==============
* **Syfte:**
    * Utvärdera och jämföra olika STT-modeller för svenska, särskilt för längre tal.
    * Bidra med kunskap: Vilka modeller passar bäst för svenskt tal.
* **Nyckelfrågor vi vill besvara:**
    1.  Hur presterar olika modeller (särskilt KBLabs KB-Whisper) på längre ljudformat på svenska?
    2.  Skillnader mellan open-source och kommersiella alternativ?
    3.  Vilka är deras styrkor och svagheter för just svenskt tal?



<!-- end_slide -->
<!-- incremental_lists: true -->
Så Gjorde Vi: Metod & Avgränsningar
==============
* **Data:**
    * Poddar vi har fått tillåtense att använda.
    * Material från Riksdagen (fritt att använda).
    * All data har **manuellt transkriberats** för att ha en "facit".
    * ~ 5 timmar data.
    * Moseboken som verifieringsdata. 
* **Avgränsningar:**
    * Fokus på specifika, tillgängliga open-source och kommersiella modeller.
    * Prioriterar **långformat ljud**.
    * *Ej primärt fokus:*
        * Korta, isolerade ljudklipp.
        * Extremt breda dialektstudier.
* **Övergripande Strategi:**
    * **Kvantitativ metod:** Objektiv mätning och jämförelse.
    * Utvecklat ett **eget utvärderingsskript** för systematisk testning.


<!-- end_slide -->
<!-- incremental_lists: true -->
Evalueringsmetriker – Hur mäter vi?
==============
Här introducerar vi de mått vi använt för att bedöma modellernas prestanda.
Vi kommer gå igenom:
* Word Error Rate (WER)
* Character Error Rate (CER)
* BERTScore
* METEOR
* LLM utvärdering

<!-- end_slide -->
<!-- incremental_lists: true -->
Word Error Rate (WER) - Felprocent på Ord
==============
* **Vad det är**: Tänk dig att du jämför vad datorn hörde med vad som faktiskt sades. WER räknar hur många ord som är fel, saknas eller lagts till för mycket. Man delar detta antal fel med det totala antalet ord som skulle ha sagts.
* **Exempel:**
    * **Rätt**:
      *  "köp mjölk och bröd" (4 ord)
      * Datorn hörde: "köp filmjölk och"
    * **Fel:** 
      * "mjölk" byttes mot "filmjölk" (1 fel - byte)
      * "bröd" (saknas) (1 saknat ord)
        * 
    * WER = (Antal byten + Antal saknade + Antal extra) / Totalt antal rätta ord
* **Mål**: <span class="noice">**Lägre är bättre**</span> (0% är perfekt).



<!-- end_slide -->
<!-- incremental_lists: true -->
Character Error Rate (CER) - Felprocent på Bokstäver
==============
* **Vad det är**: Fungerar precis som WER, men räknar fel på bokstavsnivå istället för ordnivå. Hur många bokstäver är fel, saknas eller är extra? Dela med totala antalet bokstäver som borde finnas. Används ofta för språk utan tydliga ordmellanrum eller för att fånga små stavfel.
* **Exempel:**
    * **Rätt**:
      * "hej" (3 bokstäver)
      * Datorn hörde: "nej"
    * **Fel:** 
      * 'h' byttes mot 'n' (1 bokstavsfel - byte).

    * CER = (Antal bokstavsbyten + Antal saknade bokstäver + Antal extra bokstäver) / Totalt antal rätta bokstäver
    * CER = (1 + 0 + 0) / 3 ≈ 0.33 (eller 33%)
* **Mål**: <span class="noice">**Lägre är bättre**</span> (0% är perfekt).




<!-- end_slide -->
<!-- incremental_lists: true -->
BERTScore - Mäter Likhet i Betydelse
==============
* **Vad det är**: Detta mått kollar hur lika i betydelse datorns text är jämfört med den korrekta texten. Den använder smart AI (BERT) för att förstå om orden betyder ungefär samma sak, även om de inte är exakt desamma.
* **Exempel:**
    * **Rätt**:
      * "Bilen är röd"
      * Datorn hörde: "Fordonet är rött"
    * Analys: WER skulle se detta som fel eftersom "Bilen" != "Fordonet" och "röd" != "rött". Men BERTScore förstår att meningen betyder nästan exakt samma sak och ger därför ett högt betyg (nära 1).

* **Mål**: <span class="noice">**Högre är bättre**</span> (närmare 1).
* Vi har använt **bert-base-multilingual-cased** i våra test.

<!-- end_slide -->
<!-- incremental_lists: true -->
METEOR - Smartare Ordmatchning
==============
* **Vad det är**: Det här måttet är lite smartare än WER. Det försöker matcha ord som betyder samma sak (t.ex. 'bil' och 'fordon') eller är olika former av samma ord (t.ex. 'springer' och 'sprang'). Målet är att bättre matcha hur en människa skulle bedöma om texten är bra, även om exakt samma ord inte används.
* **Exempel:**
    * **Rätt**:
      * "Hunden sprang snabbt"
      * Datorn hörde: "Valpen springer fort"
    * Analys: WER ser många fel. METEOR kan matcha "Hunden" med "Valpen" (liknande betydelse), "sprang" med "springer" (samma grundord) och "snabbt" med "fort" (synonymer). Därför ger METEOR ett högre betyg än WER.
* **Mål**: <span class="noice">**Högre är bättre**</span> (närmare 1).


<!-- end_slide -->

Resultat alla modeller
==============
![image:width:100%](_interesting_models_all.png)



<!-- end_slide -->
<!-- incremental_lists: true -->
Resultat lokala modeller
==============
![image:width:100%](_local_model.png)




<!-- incremental_lists: true -->
<!-- end_slide -->

Jämnförelse mellan städad och rå data.
==============
![image:width:100%](is_it_clean.png)



<!-- end_slide -->
<!-- incremental_lists: true -->


Del 2 Mötesassistent
==============
![image:width:100%](agent3.png)



<!-- end_slide -->
<!-- incremental_lists: true -->
Introduktion Mötesassistent - Utmaningen
==============
* **Problemet:**
    * Fånga och förstå talad information i realtid är svårt (möten, föreläsningar).
    * Manuell transkribering och analys är tidskrävande.
    * Extrahera olika insikter (fakta, risker, idéer, känslor) kräver olika perspektiv.
* **Vår Lösning: Mötesassistenten**
    * System som fångar ljud, transkriberar live.
    * Använder intelligenta **agenter** för mångfacetterad analys.
    * Ger återkoppling direkt till användaren (t.ex. relevanta frågor, input i realtid).





<!-- end_slide -->
<!-- incremental_lists: true -->
Hur Det Fungerar - Flödet
==============
![image:width:100%](flow.png)



<!-- end_slide -->
<!-- incremental_lists: true -->
Agentsystemet - Kärnan i Mötesassistenten
==============
* **Koncept:** Multi-agentsystem där varje agent har distinkt "roll" och analytiskt fokus.
    * Inspirerat av "Six thinking hats".
* **Orkestrering (`agent_runner.py`):**
    * `set_active_meeting(meeting_id)`: Anger aktivt möte.
    * `agent_scheduler()`: Bakgrundstråd som periodiskt triggar agentkörning.
    * `run_agent_suite(meeting_id, fetch_mode)`:
        * Hämtar LLM-konfiguration.
        * Hämtar nya/fullständiga transkriptioner.
        * Initierar och kör varje agent.
* **Verktyg (`agent_utils.py`):**
    * `create_azure_model()`: Konfigurerar LLM-anslutning (**Azure OpenAI / AI Foundry**).
    * `get_transcription_context()`: Ger transkriptionsdata till agenter.
    * `save_agent_output_to_db()`: Sparar agentresultat.





<!-- end_slide -->
<!-- incremental_lists: true -->
Six Thinking Hats - Anpassad Metodik
==============
### Ursprunglig Metod (Edward de Bono)
Förbättrar tänkande i möten genom sex perspektiv:
* **Vit hatt**: Fakta & information.
* <span class="noice">**Röd hatt**</span>: Känslor & intuition.
* <span class="svart_hatt">**Svart hatt**</span>: Kritisk analys & risker.
* <span class="gul_hatt">**Gul hatt**</span>: Optimism & fördelar.
* <span class="gron_hatt">**Grön hatt**</span>: Kreativitet & nya idéer.
* <span class="bla_hatt">**Blå hatt**</span>: Översikt & processhantering. 
### Vår Anpassning för LLM-agenter
Initiala tester visade att Röd och Blå hatt var svåra för LLMs. Vi designade om och la till:
* <span class="noice">**Röd hatt (Ny):** Comic relief</span> - Skapa (försök till) skämt.
* <span class="bla_hatt">**Blå hatt (Ny):** Dirigenten</span> - Bedöm relevans/kvalitet på andra agenters output.
* <span class="lila_hatt">**Lila hatt (Ny):** Frågegeneratorn</span> - Ställ relevanta uppföljningsfrågor.
* **Miro (Under utveckling):** Skapa Miro-objekt.

<!-- end_slide -->
<!-- incremental_lists: true -->
Exempel på en agent
==============
**DESCRIPTION** = """Agent Green: Expert på kreativ katalysering, specialiserad på att generera innovativa idéer och alternativa lösningar baserade på mötesprotokoll. Rollen är att utforska nya perspektiv, brainstorma kreativa tillvägagångssätt, föreslå okonventionella lösningar och stimulera nytänkande kring de diskuterade ämnena."""

**INSTRUCTIONS** = """
Läs det tillhandahållna mötesprotokollet noggrant.

Granska mötesprotokollet noggrant. 

Identifiera nyckelproblem, mål och idéer från mötet.

Brainstorma nya idéer:

Alternativa lösningar som inte nämndes.

Kreativa sätt att tackla utmaningar, inspirerade 
av risker/svagheter.

Okonventionella vägar till målen.

Skapa "Tänk om...?"-scenarier för bredare perspektiv.

Formulera två öppna frågor för att utforska idéerna vidare.
"""



<!-- end_slide -->
<!-- incremental_lists: true -->
Exempel på kod till agent
==============
```python
class GreenHatAgent:
    def __init__(self, llm_config: dict, meeting_id: int = None): 
        model = create_azure_model(llm_config)
        context = get_transcription_context(meeting_id) if meeting_id else
        "No meeting context provided."
        self._agent = Agent(
            model=model,
            description=DESCRIPTION,
            instructions=INSTRUCTIONS,
            additional_context=context,
            markdown=True  # Ensure markdown formatting is enabled
        )
    def run(self, user_input: str, meeting_id: int = None):
        response = self._agent.run(user_input=user_input)
        if hasattr(response, 'content'):
            output_text = response.content
        else:
            output_text = response        
        if meeting_id is not None:
            from .agent_utils import save_agent_output
            save_agent_output(meeting_id=meeting_id, agent_id=4, agent_name="Green Hat", output_text=output_text)            
        return output_text

```

<!-- end_slide -->
<!-- incremental_lists: true -->
Insikt med agentsystem
==============
![image:width:100%](prompt3.png)


<!-- end_slide -->
<!-- incremental_lists: true -->
Teknisk Stack 
==============

* **Frontend:** **React** (JavaScript/JSX, HTML, CSS), **Web Audio API** för ljudupptagning, **WebSockets** för realtidskommunikation.  
* **Backend:** **Python** med **FastAPI** som webbramverk.  
* **Transkriberingsmotor:** **KBLab Whisper-modeller** (t.ex. KBLab/kb-whisper-small, KBLab/kb-whisper-base) via Hugging Face transformers och **PyTorch**.  
* **Språkmodeller (LLM):** **Azure OpenAI** (t.ex. GPT-4o-mini) och **Azure AI Foundry** (t.ex. DeepSeek-modeller) via agno-biblioteket (konfigurerat i constants.py).  
* **Databas:** **SQLite** via **SQLAlchemy** .  


<!-- end_slide -->
<!-- incremental_lists: true -->
Lärdomar
==============
* Databaser är svårt.  

* Multi-agentsystem är komplicerat.  

* Manuellt transkribera är tråkigt.  

* KBLab visar att man kan komma långt men en specialiserad finetune.  



<!-- end_slide -->
<!-- incremental_lists: true -->
Förbättringar
==============
* **Transkriberingsprocess:**
    * Implementera mer avancerad **meningssegmentering (chunking/splitting)**.
    * Undersöka och integrera tekniker för **talaridentifiering (speaker diarization)**.
    * Bättre hantering av **bakgrundsljud och varierande ljudkvalitet**.
* **Systemarkitektur & Databas:**
    * Migrera till **PostgreSQL** som databas för ökad skalbarhet och prestanda.
    * Implementera stöd för **LISTEN/NOTIFY i PostgreSQL** för att möjliggöra mer omedelbara och live-uppdateringar i systemet.
* **Agentfunktionalitet & LLM-interaktion:**
    * **Djupare utnyttjande av agnos-bibliotekets funktioner**.
    * **Färdigställa Miro-agenten** för att möjliggöra visuell representation och interaktion.
    * Utveckla fler **specialiserade agentroller** eller förbättra.
* **Integrationer & Arbetsflöden:**
    * Implementera integration med **Microsoft Teams**.<purpose>
    You are an expert AI assistant tasked with generating a complete and formal academic report in Swedish.
    Your goal is to produce a well-structured report on a given [[topic]], using the provided [[report_title]], [[author_name]], and [[report_date]], and adhering strictly to the specified Swedish report template structure and content guidelines for each section.
</purpose>

<instructions>
    <instruction>Your primary task is to generate a full report in Swedish, formatted in Markdown.</instruction>
    <instruction>Use the provided main [[topic]] as the central subject for the report's content.</instruction>
    <instruction>Populate the report's metadata fields: the title should be [[report_title]], the author should be [[author_name]], and the date should be [[report_date]]. These correspond to the `[Rapporttitel]`, `[Ditt namn]`, and `[Datum]` placeholders in the original template structure.</instruction>
    <instruction>The structure of your report must follow the "Swedish Report Template" detailed below. This includes all specified sections in the correct order, rendered as Markdown.</instruction>
    <instruction>For each section of the template (e.g., Abstract, Bakgrund och problemformulering), generate relevant, detailed, and coherent content based on the [[topic]]. Pay close attention to the specific guidelines and questions provided within each section's description in the template (the text in brackets `[...]`).</instruction>
    <instruction>If specific supplementary details are provided for any section (e.g., [[abstract_details]], [[background_details]], [[method_details]], etc.), you must incorporate this information into the content you generate for that section. If no specific details are provided for a section, generate the content based solely on the [[topic]] and the template's guidelines for that section.</instruction>
    <instruction>The "Innehållsförteckning" (Table of Contents) should be generated to accurately reflect the main sections of the report, using Markdown links to the corresponding sections.</instruction>
    <instruction>Maintain a formal, objective, and academic writing style suitable for a Swedish report throughout the entire document.</instruction>
    <instruction>Ensure the final output is a single, continuous report in Markdown format, starting with the title and following the template structure meticulously.</instruction>
</instructions>

<swedish_report_template_structure>
  # [[report_title]]
 
  **Författare:** [[author_name]]
  **Datum:** [[report_date]]
  **Ämne:** [[topic]]

  ---

  ## Sammanfattning (Abstract)
  [[abstract_details]]

  ---

  ---

  ## Förkortningar 
  [[glossary_terms]]

  ---

  ## Innehållsförteckning
  - [1. Introduktion](#1-introduktion)
    - [1.1 Bakgrund](#11-bakgrund)
    - [1.2 Problemformulering](#12-problemformulering)
    - [1.3 Syfte och Frågeställningar](#13-syfte-och-frågeställningar)
    - [1.4 Avgränsningar](#14-avgränsningar)
    - [1.5 Disposition](#15-disposition)
  - [2. Teoretisk Referensram och Litteraturgenomgång](#2-teoretisk-referensram-och-litteraturgenomgång)
    - [2.1 Relevant Teori/Modeller](#21-relevant-teorimodeller)
    - [2.2 Tidigare Forskning](#22-tidigare-forskning)
  - [3. Metod](#3-metod)
    - [3.1 Val av Metod](#31-val-av-metod)
    - [3.2 Datainsamling](#32-datainsamling)
    - [3.3 Urval](#33-urval)
    - [3.4 Analysmetod](#34-analysmetod)
    - [3.5 Etiska Överväganden](#35-etiska-överväganden)
  - [4. Resultat](#4-resultat)
    - [4.1 Resultat relaterat till Frågeställning 1/Tema A](#41-resultat-relaterat-till-frågeställning-1tema-a)
    - [4.2 Resultat relaterat till Frågeställning 2/Tema B](#42-resultat-relaterat-till-frågeställning-2tema-b)
  - [5. Diskussion](#5-diskussion)
    - [5.1 Sammanfattning av Resultat](#51-sammanfattning-av-resultat)
    - [5.2 Tolkning och Analys av Resultat](#52-tolkning-och-analys-av-resultat)
    - [5.3 Jämförelse med Tidigare Forskning](#53-jämförelse-med-tidigare-forskning)
    - [5.4 Metoddiskussion (Styrkor och Svagheter)](#54-metoddiskussion-styrkor-och-svagheter)
    - [5.5 Implikationer och Rekommendationer](#55-implikationer-och-rekommendationer)
  - [6. Slutsatser och Framtida Arbete](#6-slutsatser-och-framtida-arbete)
    - [6.1 Slutsatser](#61-slutsatser)
    - [6.2 Framtida Arbete](#62-framtida-arbete)
  - [Referenser (Källförteckning)](#referenser-källförteckning)
  - [Bilagor](#bilagor)
    - [Bilaga A: [Titel på Bilaga A]](#bilaga-a-titel-på-bilaga-a) - [Förkortningar](#förkortningar)

  ---

  ## 1. Introduktion
  ### 1.1 Bakgrund
  [[background_details]]

  ### 1.2 Problemformulering
  [Definiera det specifika problem eller den kunskapslucka som rapporten adresserar. Motivera varför det är viktigt.]

  ### 1.3 Syfte och Frågeställningar
  [Ange rapportens övergripande syfte och de specifika forskningsfrågor eller hypoteser som ska besvaras här...]

  ### 1.4 Avgränsningar
  [[delimitations_details]]

  ### 1.5 Disposition
  [Ge en kort översikt över rapportens struktur här...]

  ---

  ## 2. Teoretisk Referensram och Litteraturgenomgång

  ### 2.1 Relevant Teori/Modeller
  [Presentera och förklara relevanta teorier/modeller här...]

  ### 2.2 Tidigare Forskning
  [Sammanfatta och granska tidigare forskning här...]
  ---

  ## 3. Metod
  [[method_details]]

  ### 3.1 Val av Metod
  [Beskriv och motivera val av metod här...]

  ### 3.2 Datainsamling
  [Beskriv datainsamlingsprocessen här...]

  ### 3.3 Urval
  [Beskriv urvalet här...]

  ### 3.4 Analysmetod
  [Beskriv analysmetoden här...]

  ### 3.5 Etiska Överväganden
  [Diskutera etiska överväganden här...]
  ---

  ## 4. Resultat
  [[results_details]]

  ### 4.1 [Resultat relaterat till Frågeställning 1/Tema A]
  [Presentera resultat för frågeställning 1/tema A här...]

  ### 4.2 [Resultat relaterat till Frågeställning 2/Tema B]
  [Presentera resultat för frågeställning 2/tema B här...]
  ---

  ## 5. Diskussion
  [[discussion_details]]

  ### 5.1 Sammanfattning av Resultat
  [Sammanfatta de viktigaste resultaten här...]

  ### 5.2 Tolkning och Analys av Resultat
  [Tolka och analysera resultaten här...]

  ### 5.3 Jämförelse med Tidigare Forskning
  [Jämför resultaten med tidigare forskning här...]

  ### 5.4 Metoddiskussion (Styrkor och Svagheter)
  [Diskutera metodens styrkor och svagheter här...]

  ### 5.5 Implikationer och Rekommendationer
  [Diskutera implikationer och ge rekommendationer här...]

  ---

  ## 6. Slutsatser och Framtida Arbete

  ### 6.1 Slutsatser
  [Presentera de huvudsakliga slutsatserna här...]
  [[conclusion_details]]

  ### 6.2 Framtida Arbete
  [Föreslå framtida arbete här...]

  ---

  ## Referenser (Källförteckning)
  [[bibliography_list]]

  ---

  ## Bilagor
  [[appendices_content]]

  ---


</swedish_report_template_structure>




<report_input_variables>
    <variable name="topic" description="The main subject of the report.">Utvärdering av Speech-to-Text-modeller för svenska</variable>
    <variable name="report_title" description="The title of the report.">Transcriptomatic</variable>
    <variable name="author_name" description="The author's name.">Anton Lundström, Robert Zeijlon</variable>
    <variable name="report_date" description="The date of the report.">16 maj 2025</variable>
    <variable name="abstract_details" description="Optional: Specific points or full text for the abstract." optional="true">
        Varför utvärdera STT-modeller för svenska?
        Till skillnad från engelska är utbudet av högkvalitativa Speech-to-Text (STT) modeller för svenska mer begränsat. Detta gör det särskilt viktigt att noggrant utvärdera befintliga modellers prestanda för att identifiera de som bäst hanterar det svenska språket.
        Vårt test fokuserar specifikt på hur väl olika STT-modeller hanterar längre ljudformat. Detta är avgörande för att bedöma deras lämplighet i scenarier som möten, intervjuer och andra situationer där talet ofta är mer komplext och sammanhängande. Genom att utvärdera modellerna på denna typ av data siktar vi på att sammaställa en bild av hur pass bra de är på att transkribera verkliga samtal på svenska.
    </variable>
    <variable name="background_details" description="Optional: Specific points or full text for the background and problem statement section." optional="true">
        Det finns många modeller som är väldigt bra på att transkribera engelska, båda betal och open source. Problemet är att det på svenska inte finns lika många. Därför vill vi testa och utvärdera hur bra modellerna är på svenska. För att göra detta behövde vi skapa lite egen data. Vi har kontaktakt några poddarn om tillåtelse att använda deras material som data och även tagit lite från riksdagen som är fri att använda i sånna här syften. Vi har manuellt transkriberat denna data. Det vi är mest intresserade av är hur bra KBLabs modeller presterar. Sammanfattning: KBLab KB-Whisper 
        KBLab har utvecklat KB-Whisper, en ny tal-till-text-modell speciellt framtagen för svenska.
        Den bygger på OpenAIs populära Whisper-modell men har finjusterats på en massiv datamängd om 50 000 timmar svenskt tal (från bland annat TV-textning och riksdagsprotokoll).
        Resultatet är en kraftig förbättring av prestandan för svensk taligenkänning.
        Tester visar en genomsnittlig minskning av ordfelet (WER) med hela 47 % jämfört med OpenAIs bästa modell (Whisper-large-v3).
        En stor fördel är att även mindre KB-Whisper-modeller presterar bättre än OpenAIs större modeller. Detta gör högkvalitativ svensk taligenkänning mer tillgänglig och kostnadseffektiv.
        Modellerna är fritt tillgängliga via KBLab på HuggingFace.
    </variable>
    <variable name="delimitations_details" description="Optional: Specific points or full text for the delimitations section." optional="true">
        Utvärderingen kommer att inkludera specifika open-source och kommersiella modeller och fokusera på långformat svenskt ljud från poddar och Riksdagens inspelningar.
    </variable>
    <variable name="method_details" description="Optional: Specific points or full text for the method section." optional="true">
        Utvärderingen kommer att genomföras genom att samla in vårat skapade dataset, utveckla ett utvärderingsskript som använder open-source-modeller och betal-modeller, och beräkna standard STT-metrik samt en AI-baserad kontextuell likhet. Word Error Rate (WER) - Felprocent på Ord
        för utvädering av lokala modeller modifierade vi en klient till WhisperLive som är ett open-source program för att transkribera ljud data som en ström från mikrofon eller ljudfil. Vi har modifierat den så att den kan ta en ljudfil som input och sedan transkribera den till text. Vi har även lagt till en funktion för att spara transkriberingen till en fil. WhiperLive server komponentne lämnades omidifierad och hostades med hjälp av podman, ett kontainerverktyg.
        För utvärdering av betal-modeller använde vi deras API:er för att skicka ljudfiler och ta emot transkriberingar. Vi har även använt deras API:er för att hämta metadata om transkriberingarna, såsom WER, CER, BERTScore och METEOR.
        Vi har även använt en AI-modell o4-mini från OpenAI för att beräkna en kontextuell likhet mellan transkriberingarna och originaltexten. Detta gör att vi kan få en bättre förståelse för hur väl modellerna presterar i verkliga situationer där texten inte alltid är exakt densamma som det som sägs.
        Vad det är: Tänk dig att du jämför vad datorn hörde med vad som faktiskt sades. WER räknar hur många ord som är fel, saknas eller lagts till för mycket. Man delar detta antal fel med det totala antalet ord som skulle ha sagts.
        Exempel:
            * Rätt: "Köp mjölk och bröd" (4 ord)
            * Datorn hörde: "Köp filmjölk och"
            * Fel:
                * "mjölk" byttes mot "filmjölk" (1 fel - byte)
                * "bröd" saknas (1 fel - saknas)
                * Inga extra ord lades till.
            * WER = (Antal byten + Antal saknade + Antal extra) / Totalt antal rätta ord
            * WER = (1 + 1 + 0) / 4 = 2 / 4 = 0.5 (eller 50%)
        Lägre siffra är bättre. 0% är perfekt.
        Character Error Rate (CER) - Felprocent på Bokstäver
        Vad det är: Fungerar precis som WER, men räknar fel på bokstavsnivå istället för ordnivå. Hur många bokstäver är fel, saknas eller är extra? Dela med totala antalet bokstäver som borde finnas. Används ofta för språk utan tydliga ordmellanrum eller för att fånga små stavfel.
        Exempel:
            * Rätt: "hej" (3 bokstäver)
            * Datorn hörde: "nej"
            * Fel: 'h' byttes mot 'n' (1 bokstavsfel - byte).
            * CER = (Antal bokstavsbyten + Antal saknade bokstäver + Antal extra bokstäver) / Totalt antal rätta bokstäver
            * CER = (1 + 0 + 0) / 3 ≈ 0.33 (eller 33%)
        Lägre siffra är bättre. 0% är perfekt.
        BERTScore - Mäter Likhet i Betydelse
        Vad det är: Detta mått kollar hur lika i betydelse datorns text är jämfört med den korrekta texten. Den använder smart AI (BERT) för att förstå om orden betyder ungefär samma sak, även om de inte är exakt desamma.
        Exempel:
            * Rätt: "Bilen är röd"
            * Datorn hörde: "Fordonet är rött"
            * Analys: WER skulle se detta som fel eftersom "Bilen" != "Fordonet" och "röd" != "rött". Men BERTScore förstår att meningen betyder nästan exakt samma sak och ger därför ett högt betyg (nära 1).
        Högre siffra (närmare 1) är bättre.
        METEOR - Smartare Ordmatchning
        Vad det är: Det här måttet är lite smartare än WER. Det försöker matcha ord som betyder samma sak (t.ex. 'bil' och 'fordon') eller är olika former av samma ord (t.ex. 'springer' och 'sprang'). Målet är att bättre matcha hur en människa skulle bedöma om texten är bra, även om exakt samma ord inte används.
        Exempel:
            * Rätt: "Hunden sprang snabbt"
            * Datorn hörde: "Valpen springer fort"
            * Analys: WER ser många fel. METEOR kan matcha "Hunden" med "Valpen" (liknande betydelse), "sprang" med "springer" (samma grundord) och "snabbt" med "fort" (synonymer). Därför ger METEOR ett högre betyg än WER.
        Högre siffra är bättre.
    </variable>
    <variable name="results_details" description="Optional: Specific points, data, or full text for the results section." optional="true">
    resultat.csv:
        model,WER_score,CER_score,BERTScore,METEOR_score,Cleaned_WER_score,Cleaned_CER_score,Cleaned_BERTScore,Cleaned_METEOR_score,llm_eval_score,llm_eval_kontextuell_korrekthet,llm_eval_overgripande_forstaelse
        KBLab-kb-whisper-base,0.3316620154373758,0.20782096795732347,0.6572944283485412,0.5540912656547542,0.24770240769814295,0.18780636680647195,0.9042201161384582,0.5769013179423588,0.75,0.7,0.8
        KBLab-kb-whisper-large,0.24174794862621676,0.13118125220248608,0.6631670832633972,0.6353561036172375,0.15792208051782247,0.11183740284620203,0.9454937696456909,0.6672231801960845,0.8099999999999999,0.8,0.8200000000000001
        KBLab-kb-whisper-medium,0.5438466169291332,0.4466789373240596,0.7039427876472473,0.35889630018741076,0.4757172880029902,0.4304331498110126,0.8821757793426513,0.37302208206937587,0.76,0.78,0.74
        KBLab-kb-whisper-small,0.3781399288356494,0.2679782596213817,0.6564270615577698,0.5162746820427674,0.3012799661599871,0.25007611990998085,0.891578984260559,0.5357553886322826,0.75,0.7,0.8
        KBLab-kb-whisper-tiny,0.34655713413840183,0.21617209066670692,0.65699702501297,0.5403147752369064,0.2666348876424825,0.1965898007696431,0.9016248226165772,0.5598028043589631,0.67,0.6399999999999999,0.7
        azure-api,0.2880855853995078,0.17718883669918678,0.6715270400047302,0.6101807702664189,0.20709728653632667,0.15860888179050367,0.9249177932739258,0.6392828038540468,0.8099999999999999,0.76,0.86
        deepgram-api,0.3905919817388414,0.25574741353648595,0.6573428153991699,0.5094770571954016,0.3003323327534527,0.23539665478822833,0.8623398542404175,0.5321708339175848,0.66,0.64,0.6799999999999999
        elevenlabs-api,0.43960530802538794,0.3511889678250092,0.6544082999229431,0.5089278180148229,0.3770427862580633,0.3339473840957088,0.8494328558444977,0.5401176301281866,0.67,0.66,0.6799999999999999
        openAI_large-v3,0.26270119120424357,0.12529881219786573,0.6566288590431213,0.6288573924254216,0.15495576865575908,0.10028776934402997,0.9507565259933471,0.6755998196415305,0.71,0.7,0.72
        openAI_large-v3-turbo,0.2635769798047005,0.12068395168978555,0.659968626499176,0.6508832928372769,0.1528067970887466,0.0949761173431524,0.9524174690246582,0.696408649009921,0.71,0.7,0.72
        openAI_medium,0.4128133281594419,0.3014331147235498,0.6637437462806701,0.46673357931893145,0.3407664587914149,0.2844596501125816,0.8533604383468628,0.48433586925864136,0.6900000000000001,0.7,0.6799999999999999
        openAI_small,0.3754171509132034,0.22882245639993073,0.655376398563385,0.5221491210300764,0.29474873430278903,0.20887609501438842,0.8937592387199402,0.5463803264814702,0.6900000000000001,0.6599999999999999,0.72
        openAI_tiny,0.559304749365029,0.2946209016387651,0.6567734718322754,0.4356838831640036,0.48424221605886525,0.27081551951977545,0.8406870841979981,0.44180163975993664,0.51,0.45999999999999996,0.5599999999999999
    </variable>
    <variable name="discussion_details" description="Optional: Specific points or full text for the discussion/analysis section." optional="true">
        Datan vi har skapat är väldigt begränsad i både storlek och kvalite.
        5 timmar manuellt transcriberade pod avsnit och debat fron riksdagen. 
        Vi har testat 13 olika modeller, både open-source och kommersiella.
        De stora open-source modellerna presterar generellt bättre än de kommersiella,
        halvvägs genom projectet slutade azure och google att erbjuda sin traditionella STT-tjänst och gick över till LLM-baserad transkribering, multi-model med liknande teknik som vi sett för bild annalys med nyare LLM-modeller
        Enorm potensial i LLM-baserad transcribering men tekniken är fortfarande ny och inte helt stabil. Det krävs en prompt för att den ska göra transcriberingen och tekniken är framförallt framtagen för realtides röts chat med LLM modellen
        vi tror att det kommer komma mer specificerade LLM modeller för transcribering inom några år och hoppas på ett bra open-source alternativ.
        KBLab har utvecklat KB-Whisper, en ny tal-till-text-modell speciellt framtagen för svenska.
        Den bygger på OpenAIs populära Whisper och KBlab har finjusterats på en massiv datamängd om 50 000 timmar svenskt tal (från bland annat TV-textning och riksdagsprotokoll).
        Resultatet är en kraftig förbättring av prestandan för svensk taligenkänning.
        Resulattet skulle behöva mer data för att vara mer representativt för verkligheten. Men manuel transkribering är väldigt tidskrävande och tråkigt. Vi kan kan tänka oss att fortsätta detta projekt och gör en mer djupgående analys vid intresse och monitär kompensation.
        Svenska är ett relativt lite språk och det kommer krävas initsiativ från regering eller andra intresenter för att skap bättre modeller. Kommersiellalösningar har inte så stort insitament att tillhanda hålla svenska som en del av deras utbud då intäkterna hat svårt att motivera kostnaden för att utveckla och underhålla modellerna.
        En av utmaningarna för transcriberings modeller som potentielt inte finns hos LLM+baserad transkribering är att modellerna börjar hallusinera när det är tyst och då genereras ord som inte finns i ljudet. Detta kan vara ett problem för både open-source och kommersiella modeller. Lösningar kan vara att efterbehandla eller splitta ljudfilen och ta bort segment av långvarig (1 secund eller mer) tystnader
        Förbättringar man kan göra för Transkriberingsprocessen
            * Implementera mer avancerad **meningssegmentering (chunking/splitting)**.
            * Undersöka och integrera tekniker för **talaridentifiering (speaker diarization)**.
            * Bättre hantering av **bakgrundsljud och varierande ljudkvalitet**.
            * Utveckla en **efterbehandlingsprocess** för att korrigera vanliga fel och hallucineringar.
            * Namn och ovanliga ord kan behöva kusteras i efterhand eller för open-source modeller kan man relativet resursteffectivt finetuna in namn och branchspecifika org för bättre resultat.

    </variable>
    <variable name="bibliography_list" description="Optional: A list of sources/references. Can be a string with multiple entries." optional="true">Referenser till de använda modellerna och datakällorna kommer att inkluderas.https://huggingface.co/KBLab/kb-whisper-large. https://elevenlabs.io/. https://deepgram.com/. https://azure.microsoft.com/. https://huggingface.co/spaces/openai/whisper. </variable>
    <variable name="appendices_content" description="Optional: Content for the appendices section. Can be text or description of attachments." optional="true">
        Detaljerade transkriptioner och ytterligare data kan inkluderas som bilagor. 
    </variable>
    <variable name="abbreviations_list" description="Optional: A list of abbreviations and their meanings. Can be a string with multiple entries." optional="true">STT - Speech-to-Text, WER - Word Error Rate, CER - Character Error Rate, BERTScore - ett mått på textlikhet, METEOR - ett mått på maskinöversättningskvalitet, Podman - ett containerhanteringsverktyg</variable>
    <variable name="glossary_terms" description="Optional: A list of key terms and their definitions." optional="true">Open-source - programvara med öppen källkod, Kommersiella modeller - betalmodeller för Speech-to-Text, Långformat ljud - ljudinspelningar som är längre än vanliga korta klipp, t.ex. möten och poddar</variable>
    <variable name="conclusion_details" description="Optional: Specific points or full text for the conclusion section." optional="true">Slutsatserna kommer att summera de viktigaste resultaten och ge rekommendationer för framtida arbete.</variable>

</report_input_variables>
    * Utforska integration med **kalenderverktyg** för att automatiskt hämta möteskontext (deltagare, agenda).
    * Introducera **automatisk sammanfattning** av transkriberade möten och identifiering av **åtgärdspunkter (action items)**.
* **Prestanda & Utvärdering:**
    * Fortsatt **optimering för lägre latens** i både transkriberings- och agentresponstider.
    * Utöka möjligheterna att **analysera och jämföra agenternas output** över tid och olika möten.

<!-- end_slide -->
<!-- incremental_lists: true -->


![image:width:100%](fragor.png)






