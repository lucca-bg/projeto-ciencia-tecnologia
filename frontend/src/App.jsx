import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  // State variables - these are like memory for the component
  const [file, setFile] = useState(null);                    // The uploaded audio file
  const [loading, setLoading] = useState(false);             // Is it processing?
  const [step, setStep] = useState('upload');                // Which step: 'upload', 'select', or 'result'
  const [sessionId, setSessionId] = useState(null);          // Session ID from backend
  const [options, setOptions] = useState([]);                // First note position options
  const [selectedOption, setSelectedOption] = useState(null); // Which option user selected
  const [result, setResult] = useState(null);                // The final tablature result
  const [error, setError] = useState(null);                  // Error messages

  const API_BASE = 'http://localhost:8000'; // Backend URL

  // Handle file selection
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  // Upload file to backend
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create FormData (required for file upload)
      const formData = new FormData();
      formData.append('file', file);

      // Send to backend
      const response = await axios.post(`${API_BASE}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Extract data from response
      const { session_id, first_note, options: noteOptions, num_notes_detected } = response.data;

      // Store session ID (needed for next step)
      setSessionId(session_id);
      setOptions(noteOptions);
      setStep('select'); // Move to selection step

      console.log(`Detected ${num_notes_detected} notes, starting note: ${first_note}`);
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Send selected position to backend
  const handleProcessing = async () => {
    if (selectedOption === null) {
      setError('Please select a starting position');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Send session ID and chosen option to backend
      const response = await axios.post(`${API_BASE}/api/process`, null, {
        params: {
          session_id: sessionId,
          choice: selectedOption
        }
      });

      // Store result and move to result step
      setResult(response.data);
      setStep('result');
    } catch (err) {
      setError(`Processing failed: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Reset everything to start over
  const handleReset = () => {
    setFile(null);
    setLoading(false);
    setStep('upload');
    setSessionId(null);
    setOptions([]);
    setSelectedOption(null);
    setResult(null);
    setError(null);
  };

  // Copy tablature to clipboard
  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.tablature);
    alert('Tablature copied to clipboard!');
  };

  return (
    <div className="app">
      <div className="container">
        <h1>Guitar Tablature Generator</h1>

        {/* Error message display */}
        {error && <div className="error">{error}</div>}

        {/* STEP 1: FILE UPLOAD */}
        {step === 'upload' && (
          <div className="step">
            <h2>Step 1: Upload Audio</h2>
            <div className="upload-area">
              <label htmlFor="file-input" className="file-label">
                {file ? `Selected: ${file.name}` : 'Click to select audio file'}
              </label>
              <input
                id="file-input"
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                className="file-input"
              />
            </div>
            <button onClick={handleUpload} disabled={loading} className="btn btn-primary">
              {loading ? 'Processing...' : 'Upload & Detect Notes'}
            </button>
          </div>
        )}

        {/* STEP 2: SELECT STARTING POSITION */}
        {step === 'select' && (
          <div className="step">
            <h2>Step 2: Choose Starting Position</h2>
            <p>Where should we play the first note?</p>
            <div className="options">
              {options.map((opt) => (
                <label key={opt.index} className="option-label">
                  <input
                    type="radio"
                    name="position"
                    value={opt.index}
                    checked={selectedOption === opt.index}
                    onChange={() => setSelectedOption(opt.index)}
                  />
                  <span className="option-text">{opt.display}</span>
                </label>
              ))}
            </div>
            <button onClick={handleProcessing} disabled={loading} className="btn btn-primary">
              {loading ? 'Generating...' : 'Generate Tablature'}
            </button>
          </div>
        )}

        {/* STEP 3: RESULT */}
        {step === 'result' && result && (
          <div className="step">
            <h2>Step 3: Your Tablature</h2>
            
            <div className="tablature-box">
              <pre>{result.tablature}</pre>
              <button onClick={copyToClipboard} className="btn btn-secondary">
                Copy Tablature
              </button>
            </div>

            <div className="sequence">
              <h3>Note Sequence</h3>
              <table className="sequence-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Note</th>
                    <th>String</th>
                    <th>Fret</th>
                    <th>Frequency</th>
                    <th>Time (s)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.sequence.map((note) => (
                    <tr key={note.index}>
                      <td>{note.index + 1}</td>
                      <td>{note.note}</td>
                      <td>{note.string}</td>
                      <td>{note.fret}</td>
                      <td>{note.frequency} Hz</td>
                      <td>{note.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button onClick={handleReset} className="btn btn-primary">
              Process Another File
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
