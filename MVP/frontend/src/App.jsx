import React, { useState, useEffect } from 'react';
import AudioRecorder from './components/AudioRecorder';
import AgentOutputs from './components/AgentOutputs';
import ErrorBoundary from './components/ErrorBoundary';
import axios from 'axios';
import './App.css';

function App() {
  const [isSetupComplete, setIsSetupComplete] = useState(false);
  const [meetingId, setMeetingId] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [meetingTitle, setMeetingTitle] = useState('');
  const [meetingAgenda, setMeetingAgenda] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false); // Add state for dark mode
  
  const apiBaseUrl = '/api';

  // Effect for fetching meetings
  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        const response = await axios.get(`${apiBaseUrl}/meetings`);
        setMeetings(response.data.meetings);
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching meetings:', err);
        setError('Failed to load meetings. Please try again later.');
        setIsLoading(false);
      }
    };
    fetchMeetings();
  }, [apiBaseUrl]);

  // Effect for managing dark mode
  useEffect(() => {
    // Check local storage for saved preference
    const savedMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    // Initialize based on saved preference or system preference
    const initialMode = savedMode !== null ? JSON.parse(savedMode) : prefersDark;
    setDarkMode(initialMode);

    // Apply the class to the body
    if (initialMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, []); // Run only once on mount to initialize

  // Update body class and local storage when darkMode state changes
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
      localStorage.setItem('darkMode', JSON.stringify(true));
    } else {
      document.body.classList.remove('dark-mode');
      localStorage.setItem('darkMode', JSON.stringify(false));
    }
  }, [darkMode]); // Run whenever darkMode changes

  const handleCreateMeeting = async (e) => {
    e.preventDefault();
    
    if (!meetingTitle.trim()) {
      setError('Please enter a meeting title');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Create a new meeting
      const response = await axios.post(`${apiBaseUrl}/meetings`, {
        title: meetingTitle,
        agenda: meetingAgenda
      });
      
      setMeetingId(response.data.meeting_id);
      setIsSetupComplete(true);
      setIsLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error creating meeting:', err);
      setError('Failed to create meeting. Please try again.');
      setIsLoading(false);
    }
  };

  const handleSelectMeeting = (id) => {
    setMeetingId(id);
    setIsSetupComplete(true);
  };

  // Function to toggle dark mode
  const toggleDarkMode = () => {
    setDarkMode(prevMode => !prevMode);
  };

  return (
    // App container class might not be needed if body handles background
    <div className="App widescreen">
      <header className="App-header">
        <h1>Audio Transcription App</h1>
        <button onClick={toggleDarkMode} className="theme-toggle-button">
          {darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        </button>
      </header>
      
      {!isSetupComplete ? (
        <div className="meeting-setup">
          <h2>Meeting Setup</h2>
          
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : (
            <>
              {error && <div className="error-message">{error}</div>}
              
              <form onSubmit={handleCreateMeeting} className="meeting-form">
                <div className="form-group">
                  <label htmlFor="meeting-title">Meeting Title (required)</label>
                  <input
                    id="meeting-title"
                    type="text"
                    value={meetingTitle}
                    onChange={(e) => setMeetingTitle(e.target.value)}
                    placeholder="Enter meeting title"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="meeting-agenda">Meeting Agenda (optional)</label>
                  <textarea
                    id="meeting-agenda"
                    value={meetingAgenda}
                    onChange={(e) => setMeetingAgenda(e.target.value)}
                    placeholder="Enter meeting agenda"
                    rows={4}
                  />
                </div>
                
                <button type="submit" className="create-meeting-button">
                  Create New Meeting
                </button>
              </form>
              
              {meetings.length > 0 && (
                <div className="existing-meetings">
                  <h3>Or select an existing meeting:</h3>
                  <div className="meetings-list">
                    {meetings.map(meeting => (
                      <div
                        key={meeting.id}
                        className="meeting-item"
                        onClick={() => handleSelectMeeting(meeting.id)}
                      >
                        <h4>{meeting.title}</h4>
                        <p className="meeting-date">
                          {new Date(meeting.start_time).toLocaleString()}
                        </p>
                        {meeting.agenda && (
                          <p className="meeting-agenda">{meeting.agenda}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <main>
          <ErrorBoundary>
            <AudioRecorder meetingId={meetingId} apiBaseUrl={apiBaseUrl} />
          </ErrorBoundary>
          <ErrorBoundary showDetails={true}>
            <AgentOutputs meetingId={meetingId} apiBaseUrl={apiBaseUrl} />
          </ErrorBoundary>
        </main>
      )}
    </div>
  );
}

export default App;