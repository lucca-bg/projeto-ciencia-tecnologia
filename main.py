from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import librosa
import numpy as np
from scipy import signal
import tempfile
import os
import uuid

app = FastAPI(title="Guitar Tablature API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store processing state in memory (use DB in production)
processing_state = {}

# Guitar configuration
OPEN_STRINGS = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']
NUM_FRETS = 12


def build_guitar_notes():
    freqs = []
    notes = []
    positions = []
    for string_index, string in enumerate(OPEN_STRINGS):
        base = librosa.note_to_hz(string)
        for fret in range(NUM_FRETS + 1):
            freq = base * (2 ** (fret / 12))
            notes.append(librosa.hz_to_note(freq, octave=True))
            freqs.append(freq)
            positions.append((string_index, fret))
    order = np.argsort(freqs)
    return np.array(freqs)[order], np.array(notes)[order], np.array(positions, dtype=int)[order]


def closest_guitar_note(freq, freqs, notes):
    index = np.argmin(np.abs(1200 * np.log2(freq / freqs)))
    return notes[index], freqs[index], index


def find_tab_position(note, notes, positions, preferred_pos=None):
    candidates = [(pos[1], pos[0]) for n, pos in zip(notes, positions) if n == note]
    
    if not candidates:
        return None
    
    if preferred_pos is None:
        fret, string_idx = min(candidates)
        return string_idx, fret
    
    prev_string_idx, prev_fret = preferred_pos
    
    def distance(cand):
        fret, string_idx = cand
        fret_dist = abs(fret - prev_fret)
        string_dist = abs(string_idx - prev_string_idx) * 3
        return fret_dist + string_dist
    
    fret, string_idx = min(candidates, key=distance)
    return string_idx, fret


def best_harmonic_note(pitch, guitar_freqs, guitar_notes):
    best = None
    for h in range(1, 7):
        folded = pitch / h
        if folded < 70 or folded > 330:
            continue
        note, target, _ = closest_guitar_note(folded, guitar_freqs, guitar_notes)
        cents = 1200 * np.log2(folded / target)
        score = abs(cents) + h * 2
        if best is None or score < best[0]:
            best = (score, h, folded, note, target, cents)
    return best


def preprocess_audio(y, sr):
    """Apply high-pass filter and normalization"""
    sos = signal.butter(4, 80, 'hp', fs=sr, output='sos')
    y = signal.sosfilt(sos, y)
    max_val = np.max(np.abs(y))
    if max_val > 0:
        y = y / max_val
    return y


def detect_note_in_segment(segment, sr, guitar_freqs, guitar_notes, guitar_positions):
    f0, voiced_flag, voiced_probs = librosa.pyin(
        segment,
        sr=sr,
        fmin=librosa.note_to_hz('E2'),
        fmax=librosa.note_to_hz('E4'),
        frame_length=2048,
        hop_length=512,
    )
    f0_values = [float(x) for x in f0[~np.isnan(f0)]]
    if not f0_values:
        return None

    votes = {}
    folded_values = {}
    for pitch in f0_values[:150]:
        best = best_harmonic_note(pitch, guitar_freqs, guitar_notes)
        if best is None:
            continue
        _, _, folded, note, target, _ = best
        votes[note] = votes.get(note, 0) + 1
        folded_values.setdefault(note, []).append(folded)

    if not votes:
        return None

    best_note = max(votes, key=votes.get)
    detected_pitch = float(np.mean(folded_values[best_note]))
    target_freq = float(guitar_freqs[np.argmax(guitar_notes == best_note)])
    tab_pos = find_tab_position(best_note, guitar_notes, guitar_positions)
    return {
        'note': best_note,
        'freq': detected_pitch,
        'target_freq': target_freq,
        'tab_pos': tab_pos,
    }


def build_note_sequence(y, sr, guitar_freqs, guitar_notes, guitar_positions):
    onset_frames = librosa.onset.onset_detect(
        y=y,
        sr=sr,
        units='frames',
        backtrack=True,
        hop_length=512,
    )
    if onset_frames.size == 0:
        result = detect_note_in_segment(y, sr, guitar_freqs, guitar_notes, guitar_positions)
        return [result] if result is not None else []

    onset_samples = librosa.frames_to_samples(onset_frames, hop_length=512)
    note_sequence = []
    for i, start in enumerate(onset_samples):
        end = onset_samples[i + 1] if i + 1 < len(onset_samples) else len(y)
        if end - start < 2048:
            continue
        segment = y[start:end]
        result = detect_note_in_segment(segment, sr, guitar_freqs, guitar_notes, guitar_positions)
        if result is not None:
            result['start'] = float(start / sr)
            result['end'] = float(end / sr)
            note_sequence.append(result)
    return note_sequence


def format_tab_cell(fret):
    if fret is None:
        return "----"
    fret_str = str(fret)
    if len(fret_str) == 1:
        return f"-{fret_str}--"
    return f"{fret_str}--"


def generate_tablature(sequence):
    """Generate ASCII tablature from sequence"""
    strings = ['e', 'B', 'G', 'D', 'A', 'E']
    tab_lines = [string_name + '|' for string_name in strings]
    for note_data in sequence:
        for idx in range(len(strings)):
            if note_data['tab_pos'] is not None and idx == 5 - note_data['tab_pos'][0]:
                tab_lines[idx] += format_tab_cell(note_data['tab_pos'][1]) + '|'
            else:
                tab_lines[idx] += "----|"
    return "\n".join(tab_lines)


@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and detect notes from audio file"""
    try:
        session_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Load and process audio
        y, sr = librosa.load(tmp_path, sr=None)
        y = preprocess_audio(y, sr)
        
        # Detect notes
        guitar_freqs, guitar_notes, guitar_positions = build_guitar_notes()
        sequence = build_note_sequence(y, sr, guitar_freqs, guitar_notes, guitar_positions)
        
        if not sequence:
            os.unlink(tmp_path)
            raise HTTPException(status_code=400, detail="No notes detected in audio")
        
        # Store state
        processing_state[session_id] = {
            'sequence': sequence,
            'guitar_freqs': guitar_freqs,
            'guitar_notes': guitar_notes,
            'guitar_positions': guitar_positions,
            'tmp_path': tmp_path
        }
        
        # Get first note options
        first_note = sequence[0]['note']
        first_candidates = [(pos[1], pos[0]) for n, pos in zip(guitar_notes, guitar_positions) if n == first_note]
        
        options = []
        for fret, string_idx in first_candidates:
            string_name = ['e', 'B', 'G', 'D', 'A', 'E'][5 - string_idx]
            options.append({
                'index': len(options),
                'string': string_name,
                'fret': int(fret),
                'display': f"Corda {string_name}, casa {fret}"
            })
        
        return {
            'session_id': session_id,
            'first_note': first_note,
            'num_notes_detected': len(sequence),
            'options': options,
            'sequence_preview': [
                {
                    'index': i,
                    'note': note['note'],
                    'frequency': round(note['freq'], 2),
                    'time': round(note['start'], 2)
                }
                for i, note in enumerate(sequence[:10])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
async def process_with_position(session_id: str, choice: int):
    """Process sequence with chosen starting position"""
    try:
        if session_id not in processing_state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = processing_state[session_id]
        sequence = state['sequence']
        guitar_freqs = state['guitar_freqs']
        guitar_notes = state['guitar_notes']
        guitar_positions = state['guitar_positions']
        
        # Get first note candidates and apply choice
        first_note = sequence[0]['note']
        first_candidates = [(pos[1], pos[0]) for n, pos in zip(guitar_notes, guitar_positions) if n == first_note]
        
        if choice < 0 or choice >= len(first_candidates):
            raise HTTPException(status_code=400, detail="Invalid choice")
        
        chosen_fret, chosen_string = first_candidates[choice]
        first_position = (int(chosen_string), int(chosen_fret))
        sequence[0]['tab_pos'] = first_position
        
        # Rebuild subsequent positions based on proximity
        for i in range(1, len(sequence)):
            prev_pos = sequence[i - 1]['tab_pos']
            current_note = sequence[i]['note']
            tab_pos = find_tab_position(current_note, guitar_notes, guitar_positions, preferred_pos=prev_pos)
            if tab_pos is not None:
                sequence[i]['tab_pos'] = (int(tab_pos[0]), int(tab_pos[1]))
        
        # Generate tablature
        tab = generate_tablature(sequence)
        
        # Clean up
        if state['tmp_path']:
            os.unlink(state['tmp_path'])
        del processing_state[session_id]
        
        return {
            'tablature': tab,
            'sequence': [
                {
                    'index': i,
                    'note': note['note'],
                    'frequency': round(note['freq'], 2),
                    'string': ['e', 'B', 'G', 'D', 'A', 'E'][5 - note['tab_pos'][0]] if note['tab_pos'] else 'unknown',
                    'fret': int(note['tab_pos'][1]) if note['tab_pos'] else None,
                    'time': round(note['start'], 2)
                }
                for i, note in enumerate(sequence)
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {'status': 'ok'}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
