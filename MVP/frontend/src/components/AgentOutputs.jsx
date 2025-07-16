import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; // Import ReactMarkdown
import './../App.css';

// Define the Six Thinking Hats agents with their colors and descriptions
const SIX_THINKING_HATS = {
  "White Hat": { // Key matches backend agent_name
    color: "white",
    description: "Presents objective, factual information",
    displayName: "Vit Hatt (Data Provider)" // User-facing name
  },
  "Red Hat": { // Key matches backend agent_name
    color: "red",
    description: "Lightens the mood with humor and creativity",
    displayName: "Röd Hatt (Mood Lifter)" // User-facing name
  },
  "Black Hat": { // Key matches backend agent_name
    color: "black",
    description: "Pinpoints potential risks and challenges",
    displayName: "Svart Hatt (Risk Identifier)" // User-facing name
  },
  "Yellow Hat": { // Key matches backend agent_name
    color: "yellow",
    description: "Highlights positive aspects and opportunities",
    displayName: "Gul Hatt (Optimism Promoter)" // User-facing name
  },
  "Green Hat": { // Key matches backend agent_name
    color: "green",
    description: "Proposes creative solutions and innovative ideas",
    displayName: "Grön Hatt (Idea Generator)" // User-facing name
  },
  "Blue Hat": { // Key matches backend agent_name
    color: "blue",
    description: "Reviews outputs and selects valuable insights",
    displayName: "Blå Hatt (Value Gatekeeper)" // User-facing name
  },
  "Purple Hat": { // Add Purple Hat
    color: "purple",
    description: "Summarizes and synthesizes insights",
    displayName: "Lila Hatt (Synthesizer)" // User-facing name
  }
};

const AgentOutputs = ({ meetingId, apiBaseUrl = 'http://localhost:8000' }) => {
  const [agentOutputs, setAgentOutputs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('White Hat'); // Default to White Hat (using the new key)
  const [activeOutputIndex, setActiveOutputIndex] = useState(0);
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Function to fetch agent outputs
  const fetchAgentOutputs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiBaseUrl}/agent_outputs/${meetingId}`);
      
      // Validate response data
      if (!response.data || !Array.isArray(response.data.agent_outputs)) {
        console.error('Invalid response format:', response.data);
        setError('Received invalid data format from server');
        setLoading(false);
        return;
      }
      
      // Group outputs by agent name
      const outputsByAgent = {};
      response.data.agent_outputs.forEach(output => {
        // Validate output object
        if (!output || !output.agent_name) {
          console.warn('Skipping invalid output object:', output);
          return;
        }
        
        if (!outputsByAgent[output.agent_name]) {
          outputsByAgent[output.agent_name] = [];
        }
        
        // Ensure output_text is a string
        if (output.output_text === null || output.output_text === undefined) {
          output.output_text = '';
        } else if (typeof output.output_text !== 'string') {
          output.output_text = String(output.output_text);
        }
        
        outputsByAgent[output.agent_name].push(output);
      });
      
      // Sort each agent's outputs by timestamp (newest first)
      Object.keys(outputsByAgent).forEach(agentName => {
        try {
          outputsByAgent[agentName].sort((a, b) => {
            // Handle invalid dates gracefully
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            
            if (isNaN(dateA.getTime()) && isNaN(dateB.getTime())) return 0;
            if (isNaN(dateA.getTime())) return 1;
            if (isNaN(dateB.getTime())) return -1;
            
            return dateB - dateA;
          });
        } catch (sortErr) {
          console.error(`Error sorting outputs for ${agentName}:`, sortErr);
        }
      });
      
      setAgentOutputs(outputsByAgent);
      setActiveOutputIndex(0); // Reset to most recent output when data refreshes
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching agent outputs:', err);
      setError(`Failed to load agent outputs: ${err.message}`);
      setLoading(false);
    }
  };

  // Set up automatic refresh when component mounts
  useEffect(() => {
    // Initial fetch
    fetchAgentOutputs();
    
    // Set up interval for frequent polling (every 5 seconds)
    // More frequent polling since we're not using WebSockets for real-time updates
    const intervalId = setInterval(fetchAgentOutputs, 30000);
    setRefreshInterval(intervalId);
    
    // Clean up interval when component unmounts
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [meetingId, apiBaseUrl]);

  const handleTabClick = (agentName) => {
    setActiveTab(agentName);
    setActiveOutputIndex(0); // Reset to most recent output when changing tabs
  };

  const handlePreviousOutput = () => {
    if (agentOutputs[activeTab] && activeOutputIndex < agentOutputs[activeTab].length - 1) {
      setActiveOutputIndex(activeOutputIndex + 1);
    }
  };

  const handleNextOutput = () => {
    if (activeOutputIndex > 0) {
      setActiveOutputIndex(activeOutputIndex - 1);
    }
  };

  // Safe access to current output with additional checks
  const getCurrentOutput = () => {
    try {
      if (!agentOutputs || !agentOutputs[activeTab]) return null;
      if (!Array.isArray(agentOutputs[activeTab])) return null;
      if (activeOutputIndex >= agentOutputs[activeTab].length) return null;
      return agentOutputs[activeTab][activeOutputIndex];
    } catch (e) {
      console.error("Error accessing current output:", e);
      return null;
    }
  };

  const currentOutput = getCurrentOutput();
  const hasMultipleOutputs = agentOutputs[activeTab] && Array.isArray(agentOutputs[activeTab]) && agentOutputs[activeTab].length > 1;
  const isOldestOutput = agentOutputs[activeTab] && Array.isArray(agentOutputs[activeTab]) && activeOutputIndex === agentOutputs[activeTab].length - 1;
  const isNewestOutput = activeOutputIndex === 0;

  // Safely format timestamp
  const formatTimestamp = (timestamp) => {
    try {
      return timestamp ? new Date(timestamp).toLocaleString() : 'Unknown time';
    } catch (e) {
      console.error("Error formatting timestamp:", e);
      return 'Invalid timestamp';
    }
  };

  // Safely render HTML content
  const renderContent = (content) => {
    try {
      if (!content) {
        return <p>No content available</p>;
      }
      // Ensure content is a string before passing to ReactMarkdown
      const outputText = typeof content === 'string' ? content : String(content);
      // Use ReactMarkdown to render the content
      return <ReactMarkdown>{outputText}</ReactMarkdown>;
    } catch (e) {
      console.error("Error rendering markdown content:", e);
      // Fallback to rendering as plain text if markdown parsing fails
      return <p>{String(content || '')}</p>;
    }
  };

  return (
    <div className="agent-outputs-container">
      <h2>Thinking Hats Insights</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      {/* Tab navigation */}
      <div className="agent-tabs">
        {Object.keys(SIX_THINKING_HATS).map(agentName => (
          <button 
            key={agentName}
            className={`tab-button ${activeTab === agentName ? 'active' : ''} ${SIX_THINKING_HATS[agentName].color}-tab`}
            onClick={() => handleTabClick(agentName)}
          >
            {SIX_THINKING_HATS[agentName].displayName}
          </button>
        ))}
      </div>
      
      {/* Tab content */}
      <div className="tab-content">
        {loading ? (
          <div className="loading">Loading agent insights...</div>
        ) : (
          Object.keys(SIX_THINKING_HATS).map(agentName => (
            <div 
              key={agentName}
              className={`agent-output ${activeTab === agentName ? 'active' : 'hidden'}`}
            >
              <p className="agent-description">
                <em>{SIX_THINKING_HATS[agentName].description}</em>
              </p>
              
              {agentOutputs[agentName] && Array.isArray(agentOutputs[agentName]) && agentOutputs[agentName].length > 0 ? (
                currentOutput ? (
                  <div>
                    <div className="output-header">
                      <p className="timestamp">
                        <em>Generated at: {formatTimestamp(currentOutput.timestamp)}</em>
                      </p>
                      
                      {hasMultipleOutputs && (
                        <div className="output-navigation">
                          <button
                            className="nav-button"
                            onClick={handleNextOutput}
                            disabled={isNewestOutput}
                          >
                            Newer
                          </button>
                          <span className="output-count">
                            {activeOutputIndex + 1} of {agentOutputs[activeTab]?.length || 0}
                          </span>
                          <button
                            className="nav-button"
                            onClick={handlePreviousOutput}
                            disabled={isOldestOutput}
                          >
                            Older
                          </button>
                        </div>
                      )}
                    </div>
                    
                    <div className="output-text">
                      {renderContent(currentOutput.output_text)}
                    </div>
                  </div>
                ) : (
                  <div className="no-output">Error loading output</div>
                )
              ) : (
                <div className="no-output">Waiting for insights...</div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AgentOutputs;