## Implementation Plan for AI Agents

**Overall Goal:** Implement AI agents to provide unique insights from live meetings, making them more efficient and fun.

**Key Components:**

*   **Transcription Pipeline:** Captures audio, transcribes it using the KBLab/kb-whisper-medium model, and stores it in an SQLite database.
*   **Database:** SQLite database with tables for `meetings`, `meeting_relations`, `transcripts`, and `agents_output`.
*   **Agents:** Instances of the `Agent` class from the `agno` framework, each with a specific role (White Hat, Red Hat, Black Hat, Yellow Hat, Green Hat, Blue Hat).
*   **Streamlit App:** Provides a live interface to view transcription and agent outputs.

**Updated Implementation Plan:**

1.  **Integrate the Six Thinking Hats Agents:**
    *   Create agent configurations for each of the six thinking hats (White, Red, Black, Yellow, Green, and Blue) as described in `agent.md`. Use the examples in `README.md` as a starting point.
    *   Ensure each agent has a clear `description`, `instructions`, and `additional_context` (meeting agenda and previous meeting summaries).
    *   Implement the Red Hat's image generation functionality using an appropriate image generation API.
    *   Implement the Blue Hat's value gatekeeping logic to determine which outputs are stored in the database.

2.  **Modify the Agent Processing Workflow:**
    *   Update the agent processing loop to include all six agents.
    *   Ensure the agents process the transcription data periodically (every 5-10 seconds).
    *   **Store the outputs of each agent in the `agents_output` table, including the `agent_id`, `agent_name`, `output_text`, and `timestamp`.**
    *   Implement the Red Hat's image generation and storage in the database.
    *   Implement the Blue Hat's logic for filtering and storing valuable insights in the database.

3.  **Update the Streamlit App:**
    *   Modify the Streamlit app to display the outputs of all six agents in real-time.
    *   Use separate placeholders for each agent's output.
    *   **Fetch the agent outputs from the database and display them in the Streamlit app.**
    *   Update the display every 5 seconds to show the latest outputs.
    *   Implement a mechanism to display the Red Hat's generated images.

4.  **Database Modifications:**
    *   Ensure the database schema includes all necessary fields for storing agent outputs, including the Red Hat's images and the Blue Hat's value judgments.
    *   Modify the database queries to retrieve and display the agent outputs in the Streamlit app.

5.  **Testing and Refinement:**
    *   Thoroughly test the implementation to ensure the agents are functioning correctly and providing valuable insights.
    *   Refine the agent configurations and processing logic as needed to optimize their performance and accuracy.

**Detailed Steps:**

1.  **File Analysis:**
    *   Examine the existing code files (`api.py`, `audio_recorder.py`, `audio_system_recorder.py`, `audio_transcribe.py`, `constants.py`, `database.py`, `streamlit_app.py`) to understand the current implementation of the transcription pipeline, database interaction, and Streamlit app.
    *   Identify the relevant code sections that need to be modified to integrate the agents.

2.  **Code Modifications:**
    *   Modify the `database.py` file to ensure the database schema is up-to-date.
    *   Modify the `audio_transcribe.py` file to incorporate the agent processing workflow.
    *   Modify the `streamlit_app.py` file to display the agent outputs in real-time.

3.  **Agent Implementation:**
    *   Create a new file (e.g., `agents.py`) to define the agent configurations.
    *   Implement the Red Hat's image generation functionality.
    *   Implement the Blue Hat's value gatekeeping logic.

4.  **Integration and Testing:**
    *   Integrate the new code into the existing codebase.
    *   Test the implementation thoroughly to ensure the agents are functioning correctly.
    *   Refine the agent configurations and processing logic as needed.

**Mermaid Diagram:**

```mermaid
graph LR
    A[Audio Input] --> B(Transcription Pipeline)
    B --> C{Database}
    C --> D{Agents}
    D --> C
    C --> E(Streamlit App)
    E --> F[User Interface]

    subgraph Transcription Pipeline
        B --> B1[Capture Audio]
        B1 --> B2[Transcribe Audio]
        B2 --> B3[Store Transcript]
    end

    subgraph Agents
        D --> D1[White Hat]
        D --> D2[Red Hat]
        D --> D3[Black Hat]
        D --> D4[Yellow Hat]
        D --> D5[Green Hat]
        D --> D6[Blue Hat]
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#f9f,stroke:#333,stroke-width:2px