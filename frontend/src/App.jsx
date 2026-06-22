import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {

  const [file, setFile] = useState(null);                    
  const [loading, setLoading] = useState(false);             
  const [step, setStep] = useState('upload');                
  const [sessionId, setSessionId] = useState(null);          
  const [options, setOptions] = useState([]);                
  const [selectedOption, setSelectedOption] = useState(null); 
  const [result, setResult] = useState(null);                
  const [error, setError] = useState(null);                  
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

  //URL do Backend
  const API_BASE = 'http://localhost:8000'; 

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true
      });
      const recorder = new MediaRecorder(stream);
      let chunks = [];
      recorder.ondataavailable = (event) => {
        if(event.data.size > 0){
          chunks.push(event.data);
        }
      };
      recorder.onstop = () => {
        const audioBlob = new Blob(
          chunks,
          {
            type: "audio/webm"
          }
        );
        const audioFile = new File(
          [audioBlob],
          "guitar_recording.webm",
          {
            type:"audio/webm"
          }
        );
        setFile(audioFile);
      };
      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch(error){
      setError(
        "Microphone access denied"
      );
    }
  };

  const stopRecording = () => {
    if(mediaRecorder){
      mediaRecorder.stop();
      setRecording(false);
    }
  };  

  // Upload do arquivo selecionado
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const { session_id, first_note, options: noteOptions, num_notes_detected } = response.data;

      setSessionId(session_id);
      setOptions(noteOptions);
      setStep('select'); 

      console.log(`Detectadas ${num_notes_detected} notas, nota inicial: ${first_note}`);
    } catch (err) {
      setError(`Erro no upload: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessing = async () => {
    if (selectedOption === null) {
      setError('Selecione uma posição inicial');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/api/process`, null, {
        params: {
          session_id: sessionId,
          choice: selectedOption
        }
      });

      setResult(response.data);
      setStep('result');
    } catch (err) {
      setError(`Erro no processamento: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.tablature);
    alert('Tablature copied to clipboard!');
  };

  return (
    <div className="app">
      <div className="container">
        <h1>Gerador de Tablatura</h1>

        {/* Mensagem de erro */}
        {error && <div className="error">{error}</div>}

        {/* PASSO 1: UPLOAD OU GRAVAÇÃO */}
        {step === 'upload' && (
          <div className="step">
            <h2>Upload de Áudio</h2>
            <div className="upload-area">
              <label htmlFor="file-input" className="file-label">
                {file ? `Selecionado: ${file.name}` : 'Clique para selecionar um arquivo ou grave diretamente do seu microfone'}
              </label>
              <input
                id="file-input"
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                className="file-input"
              />
            </div>
            <div className="record-area">
              <button
                onClick={
                  recording
                  ? stopRecording
                  : startRecording
                }
                className="btn btn-secondary"
              >
              {
               recording
               ?
               "⏹ Parar gravação"
               :
               "🎙 Gravar áudio"
              }
              </button>
            </div>
            <button onClick={handleUpload} disabled={loading} className="btn btn-primary">
              {loading ? 'Processando...' : 'Enviar e detectar notas'}
            </button>
          </div>
        )}

        {/* PASSO 2: SELECIONAR POSIÇÃO INICIAL */}
        {step === 'select' && (
          <div className="step">
            <h2>Selecione a Posição Inicial</h2>
            <p>Em qual posição devemos mostrar a primeira nota?</p>
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
              {loading ? 'Gerando...' : 'Gerar Tablatura'}
            </button>
          </div>
        )}

        {/* PASSO 3: RESULTADO */}
        {step === 'result' && result && (
          <div className="step">
            <h2>Sua Tablatura</h2>
            
            <div className="tablature-box">
              <pre>{result.tablature}</pre>
              <button onClick={copyToClipboard} className="btn btn-secondary">
                Copiar Tablatura
              </button>
            </div>

            <div className="sequence">
              <h3>Sequência de Notas</h3>
              <table className="sequence-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Nota</th>
                    <th>Corda</th>
                    <th>Casa</th>
                    <th>Frequência</th>
                    <th>Tempo (s)</th>
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
              Gerar nova tablatura
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
