import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Restore meetingId prop, remove meeting creation logic
const AudioRecorder = ({ meetingId, apiBaseUrl = '/api' }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [sessionStarted, setSessionStarted] = useState(false); // Tracks if transcription session is active
  const [errorMessage, setErrorMessage] = useState('');
  const [transcription, setTranscription] = useState('');
  const [audioSource, setAudioSource] = useState('microphone');
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('default');

  // --- State for STT model selection ---
  const [availableSttModels, setAvailableSttModels] = useState([]);
  const [selectedSttModel, setSelectedSttModel] = useState(''); // For Whisper models

  // --- State for LLM model selection ---
  const [availableLlmModels, setAvailableLlmModels] = useState([]);
  const [selectedLlmModel, setSelectedLlmModel] = useState(''); // For GPT/DeepSeek etc.

  // --- State for Agent Interval ---
  const [agentInterval, setAgentInterval] = useState(300); // Default to 300 seconds (5 minutes)

  // Remove Meeting Detail states
  // const [meetingTitle, setMeetingTitle] = useState('');
  // const [meetingAgenda, setMeetingAgenda] = useState('');
  // const [meetingCreated, setMeetingCreated] = useState(false);
  // const [currentMeetingId, setCurrentMeetingId] = useState(null); // Use meetingId prop

  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorNodeRef = useRef(null);
  const streamRef = useRef(null);

  // Configuration
  const SAMPLE_RATE = 16000; // Must match the backend's expected sample rate
  const CHUNK_DURATION_MS = 4000; // 4 seconds

  // Load available audio devices on component mount
  useEffect(() => {
    const loadAudioDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        setAudioDevices(audioInputs);
        console.log('Available audio devices:', audioInputs);
      } catch (error) {
        console.error('Error loading audio devices:', error);
        setErrorMessage(`Failed to load audio devices: ${error.message}`);
      }
    };
    loadAudioDevices();
  }, []);

  // Fetch available STT (Whisper) models on component mount
  useEffect(() => {
    const fetchSttModels = async () => {
      if (!apiBaseUrl) return;
      try {
        const response = await axios.get(`${apiBaseUrl}/stt_models`);
        if (response.data && response.data.models && response.data.models.length > 0) {
          setAvailableSttModels(response.data.models);
          const defaultModel = response.data.models.find(m => m.includes('small')) || response.data.models[0];
          setSelectedSttModel(defaultModel);
          console.log('Available STT models:', response.data.models, 'Default:', defaultModel);
        } else {
          setErrorMessage('No STT models available from backend.');
        }
      } catch (error) {
        console.error('Failed to fetch STT models:', error);
        setErrorMessage(`Failed to fetch STT models: ${error.message}`);
      }
    };
    fetchSttModels();
  }, [apiBaseUrl]);

  // Fetch available LLM models on component mount
  useEffect(() => {
    const fetchLlmModels = async () => {
       if (!apiBaseUrl) return;
      try {
        const response = await axios.get(`${apiBaseUrl}/llm_models`);
        if (response.data && response.data.models && response.data.models.length > 0) {
          setAvailableLlmModels(response.data.models);
          setSelectedLlmModel(response.data.models[0]); // Select the first LLM by default
          console.log('Available LLM models:', response.data.models, 'Default:', response.data.models[0]);
        } else {
          setErrorMessage('No LLM models available from backend.');
        }
      } catch (error) {
        console.error('Failed to fetch LLM models:', error);
        setErrorMessage(`Failed to fetch LLM models: ${error.message}`);
      }
    };
    fetchLlmModels();
  }, [apiBaseUrl]);

  // Remove effect that fetched meeting details (LLM is selected here now)

  useEffect(() => { // Effect for cleanup
    return () => {
      if (isRecording) {
        stopAudioCapture();
      }
    };
  }, [isRecording]);

  // Function to start the backend transcription session AND update meeting config
  const startTranscriptionSession = async () => {
    if (!meetingId) {
      setErrorMessage('Meeting ID is missing.');
      return false;
    }
    if (!selectedSttModel) {
      setErrorMessage('Please select an STT model.');
      return false;
    }
     if (!selectedLlmModel) {
      setErrorMessage('Please select an LLM model.');
      return false;
    }
     if (!agentInterval || parseInt(agentInterval, 10) < 30) {
      setErrorMessage('Please set a valid agent interval (>= 30 seconds).');
      return false;
    }

    try {
      // Call the updated endpoint with all configs
      const response = await axios.post(`${apiBaseUrl}/start_session/${meetingId}`, {
          stt_model_name: selectedSttModel,
          llm_model_key: selectedLlmModel,
          agent_run_interval_seconds: parseInt(agentInterval, 10)
      });
      console.log('Session started/updated:', response.data);
      setSessionStarted(true);
      setErrorMessage('');
      return true;
    } catch (error) {
      console.error('Failed to start session:', error);
      const detail = error.response?.data?.detail || error.message;
      setErrorMessage(`Failed to start session: ${detail}`);
      setSessionStarted(false);
      return false;
    }
  };

  // Function to end the backend transcription session
  const endTranscriptionSession = async () => {
    if (!sessionStarted || !meetingId) {
      console.log("No active transcription session to end.");
      return;
    }
    try {
      const response = await axios.post(`${apiBaseUrl}/end_session`);
      console.log('Transcription session ended:', response.data);
      setSessionStarted(false);
      setErrorMessage('');
    } catch (error) {
      console.error('Failed to end transcription session:', error);
      setErrorMessage(`Failed to end transcription session: ${error.message}`);
    }
  };

  // Remove createMeeting function

  const getAudioStream = async () => {
    try {
      if (audioSource === 'microphone') {
        return await navigator.mediaDevices.getUserMedia({
          audio: { deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined }
        });
      } else if (audioSource === 'system') {
        const displayStream = await navigator.mediaDevices.getDisplayMedia({
          video: { cursor: 'never', displaySurface: 'monitor' },
          audio: { suppressLocalAudioPlayback: false, echoCancellation: false, noiseSuppression: false, autoGainControl: false }
        });
        const audioTrack = displayStream.getAudioTracks()[0];
        if (!audioTrack) throw new Error("No system audio detected. Did you select to share audio?");
        const videoTrack = displayStream.getVideoTracks()[0];
        if (videoTrack) {
          videoTrack.enabled = false;
          const videoElement = document.createElement('video');
          videoElement.srcObject = new MediaStream([videoTrack]);
          videoElement.style.cssText = 'width:1px;height:1px;position:absolute;opacity:0.01;';
          document.body.appendChild(videoElement);
          videoElement.play().catch(e => console.error("Error playing video:", e));
        }
        return displayStream;
      }
    } catch (error) {
      console.error(`Error accessing ${audioSource}:`, error);
      throw new Error(`Failed to access ${audioSource}: ${error.message}`);
    }
  };

  // Simplified start recording function
  const startAudioCapture = async () => {
    setErrorMessage('');
    if (!meetingId) {
        setErrorMessage("Cannot record without a Meeting ID.");
        return;
    }

    // 1. Start/Update Transcription Session (sends config to backend)
    if (!sessionStarted) { // Only call start session if not already started
        console.log("Attempting to start transcription session and set config...");
        const sessionOk = await startTranscriptionSession(); // Uses state variables
        if (!sessionOk) {
            return; // Error message set by startTranscriptionSession
        }
        console.log("Transcription session started/config updated.");
    } else {
         console.log("Transcription session already active.");
    }

    // 2. Start Audio Recording
    console.log("Attempting to start audio recording...");
    try {
      streamRef.current = await getAudioStream();
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
      const source = audioContextRef.current.createMediaStreamSource(streamRef.current);
      processorNodeRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);

      let audioChunk = [];
      let lastSendTime = Date.now();

      processorNodeRef.current.onaudioprocess = (event) => {
        const audioData = event.inputBuffer.getChannelData(0);
        audioChunk = [...audioChunk, ...Array.from(audioData)];
        const currentTime = Date.now();
        if (currentTime - lastSendTime >= CHUNK_DURATION_MS) {
          const audioArray = new Float32Array(audioChunk);
          sendAudioChunk(audioArray);
          audioChunk = [];
          lastSendTime = currentTime;
        }
      };

      source.connect(processorNodeRef.current);
      processorNodeRef.current.connect(audioContextRef.current.destination);

      setIsRecording(true);
      console.log("Audio recording started.");
    } catch (error) {
      console.error('Failed to start audio recording:', error);
      setErrorMessage(`Failed to start audio recording: ${error.message}`);
      setIsRecording(false);
    }
  };

  const stopAudioCapture = () => {
    try {
      if (processorNodeRef.current) processorNodeRef.current.disconnect();
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') audioContextRef.current.close();
      if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      console.log("Audio capture stopped.");
    } catch (error) {
      console.error('Error stopping audio capture:', error);
    }
  };

  const sendAudioChunk = async (audioArray) => {
    if (!meetingId) {
        console.error("Cannot send audio chunk: No active meeting ID.");
        return;
    }
    try {
      const buffer = new ArrayBuffer(audioArray.length * 4);
      const view = new DataView(buffer);
      for (let i = 0; i < audioArray.length; i++) view.setFloat32(i * 4, audioArray[i], true);
      const base64Audio = arrayBufferToBase64(buffer);

      const response = await axios.post(
        `${apiBaseUrl}/transcribe/${meetingId}`,
        { audio_data: base64Audio, sample_rate: SAMPLE_RATE }
      );

      if (response.data.transcription) {
        setTranscription(prev => prev + ' ' + response.data.transcription);
      }
    } catch (error) {
      console.error('Error sending audio chunk:', error);
    }
  };

  const arrayBufferToBase64 = (buffer) => {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return window.btoa(binary);
  };

  // Render with LLM, STT, Interval selectors
  return (
    <div className="audio-recorder">
      <h2>Audio Recorder (Meeting ID: {meetingId || 'Not Set'})</h2>

      {/* Settings Panel */}
      <div className="settings-panel">
        <h3>Settings</h3>

         {/* LLM Model Selector */}
         <div className="model-selector form-group">
            <label htmlFor="llm-model-select">LLM Model (for Agents):</label>
            <select
            id="llm-model-select"
            value={selectedLlmModel}
            onChange={(e) => setSelectedLlmModel(e.target.value)}
            disabled={sessionStarted || isRecording} // Lock once session starts
            >
            <option value="" disabled>-- Select LLM --</option>
            {availableLlmModels.map(model => (
                <option key={model} value={model}>{model}</option>
            ))}
            </select>
            {sessionStarted && <span className="note"> (LLM Model locked during session)</span>}
        </div>

        {/* STT Model Selector */}
        <div className="model-selector form-group">
          <label htmlFor="stt-model-select">STT Model (for Transcription):</label>
          <select
            id="stt-model-select"
            value={selectedSttModel}
            onChange={(e) => setSelectedSttModel(e.target.value)}
            disabled={sessionStarted || isRecording} // Lock once session starts
          >
            <option value="" disabled>-- Select STT Model --</option>
            {availableSttModels.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
          {sessionStarted && <span className="note"> (STT Model locked during session)</span>}
        </div>

         {/* Agent Run Interval Input */}
         <div className="form-group">
            <label htmlFor="agent-interval">Agent Run Interval (seconds):</label>
            <input
            type="number"
            id="agent-interval"
            value={agentInterval}
            onChange={(e) => setAgentInterval(e.target.value)}
            min="30"
            step="10"
            disabled={sessionStarted || isRecording} // Lock once session starts
            placeholder="e.g., 300"
            />
            <small className="form-note">How often agents analyze recent transcript (min 30s).</small>
            {sessionStarted && <span className="note"> (Interval locked during session)</span>}
        </div>

        {/* Audio Source Selector */}
        <div className="audio-source-selector form-group">
          <h4>Audio Source</h4>
          <div className="radio-group">
            <label>
              <input type="radio" value="microphone" checked={audioSource === 'microphone'} onChange={() => setAudioSource('microphone')} disabled={isRecording} />
              <span>Microphone</span>
            </label>
            <label>
              <input type="radio" value="system" checked={audioSource === 'system'} onChange={() => setAudioSource('system')} disabled={isRecording} />
              <span>System Audio</span>
            </label>
          </div>

          {audioSource === 'microphone' && (
            <div className="device-selector">
              <label htmlFor="microphone-select">Select Microphone:</label>
              <select id="microphone-select" value={selectedDeviceId} onChange={(e) => setSelectedDeviceId(e.target.value)} disabled={isRecording}>
                <option value="default">Default Microphone</option>
                {audioDevices.map(device => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label || `Microphone (${device.deviceId.slice(0, 8)}...)`}
                  </option>
                ))}
              </select>
            </div>
          )}

          {audioSource === 'system' && (
            <div className="system-audio-info">
              <p><strong>Note:</strong> When prompted, you must select "Share audio" in the screen sharing dialog.</p>
              <p>System audio capture works best with Chrome browser version 74+.</p>
            </div>
          )}
        </div> {/* Closes audio-source-selector */}
      </div> {/* Closes settings-panel */}

      {/* Controls Container */}
      <div className="controls-container">
        <div className="recording-controls">
          <h3>Recording Controls</h3>
          {!isRecording ? (
            <button
              className="record-button"
              onClick={startAudioCapture}
              // Disable if required selections are missing OR already recording
              disabled={!meetingId || !selectedSttModel || !selectedLlmModel || !agentInterval || isRecording}
            >
              Start Recording {audioSource === 'microphone' ? 'Microphone' : 'System Audio'}
            </button>
          ) : (
            <button
              className="stop-button"
              onClick={stopAudioCapture}
              disabled={!isRecording}
            >
              Pause Recording
            </button>
          )}
          <p className="control-note">
            You can start and stop recording multiple times within the same session.
          </p>
        </div>

        {/* Session Controls */}
        {sessionStarted && (
            <div className="session-controls">
                <h3>Session Controls</h3>
                <button
                    className="end-session-button"
                    onClick={endTranscriptionSession}
                    disabled={isRecording} // Disable only if actively recording
                >
                    End Session & Stop Agent Processing
                </button>
                <p className="control-note">
                    <strong>Note:</strong> This stops transcription and agent processing for this meeting.
                </p>
            </div>
        )}
      </div> {/* Closes controls-container */}

      {errorMessage && (
        <div className="error-message">
          {errorMessage}
        </div>
      )}

      <div className="transcription-container">
        <h3>Live Transcription:</h3>
        <div className="transcription">
          {transcription || (meetingId ? 'Select settings and start recording.' : 'Waiting for Meeting ID.')}
        </div>
      </div>
    </div> // Closes audio-recorder
  ); // Closes return
}; // Closes component function

export default AudioRecorder;