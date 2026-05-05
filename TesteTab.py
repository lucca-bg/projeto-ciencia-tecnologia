import sys
import librosa
import numpy as np
from scipy import signal

# Escolha o arquivo de áudio a testar. Use o argumento de linha de comando para mudar o arquivo.
audio_path = sys.argv[1] if len(sys.argv) > 1 else "testeesc.wav"
y, sr = librosa.load(audio_path, sr=None)

# High-pass filter (80 Hz cutoff) to remove rumble and low-frequency noise
sos = signal.butter(4, 80, 'hp', fs=sr, output='sos')
y = signal.sosfilt(sos, y)

# Normalization: scale to [-1, 1] range
max_val = np.max(np.abs(y))
if max_val > 0:
    y = y / max_val

# Notas de violão (6 cordas, 0-12 casas)
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
    """
    Find tab position for a note.
    If preferred_pos is None, returns the lowest fret.
    If preferred_pos is (string_idx, fret), finds the closest position to it.
    """
    candidates = [(pos[1], pos[0]) for n, pos in zip(notes, positions) if n == note]
    # candidates format: [(fret, string_index), ...]
    
    if not candidates:
        return None
    
    if preferred_pos is None:
        # Default: lowest fret
        fret, string_idx = min(candidates)
        return string_idx, fret
    
    # Find closest to preferred position
    prev_string_idx, prev_fret = preferred_pos
    
    # Find closest by distance
    def distance(cand):
        fret, string_idx = cand
        fret_dist = abs(fret - prev_fret)
        string_dist = abs(string_idx - prev_string_idx) * 3  # Weight string changes more
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


guitar_freqs, guitar_notes, guitar_positions = build_guitar_notes()
sequence = build_note_sequence(y, sr, guitar_freqs, guitar_notes, guitar_positions)

print(f"Arquivo: {audio_path}")
if not sequence:
    print("Nenhuma frequência relevante detectada.")
else:
    print("Sequência detectada:")
    for index, note_data in enumerate(sequence, start=1):
        string_idx, fret = note_data['tab_pos'] if note_data['tab_pos'] is not None else (None, None)
        string_name = ['e', 'B', 'G', 'D', 'A', 'E'][5 - string_idx] if string_idx is not None else 'unknown'
        print(f"{index:02d}. {note_data['note']} ({note_data['freq']:.2f} Hz) - {string_name}{fret} - {note_data['start']:.2f}s")

    # Ask user for the first note position
    first_note = sequence[0]['note']
    print(f"\n=== Primeira nota: {first_note} ===")
    first_candidates = [(pos[1], pos[0]) for n, pos in zip(guitar_notes, guitar_positions) if n == first_note]
    
    # Verifica se há mais de uma opção para a primeira nota e solicita ao usuário escolher
    if(len(first_candidates) > 1):
        print("Opções disponíveis:")
        for i, (fret, string_idx) in enumerate(first_candidates):
            string_name = ['e', 'B', 'G', 'D', 'A', 'E'][5 - string_idx]
            print(f"{i}. Corda {string_name}, casa {fret}")
    
        choice = int(input(f"Escolha (0-{len(first_candidates) - 1}): "))
    else:
        choice = 0    
    chosen_fret, chosen_string = first_candidates[choice]
    first_position = (chosen_string, chosen_fret)
    sequence[0]['tab_pos'] = first_position
    
    # Rebuild all subsequent positions based on proximity to the first
    for i in range(1, len(sequence)):
        prev_pos = sequence[i - 1]['tab_pos']
        current_note = sequence[i]['note']
        tab_pos = find_tab_position(current_note, guitar_notes, guitar_positions, preferred_pos=prev_pos)
        sequence[i]['tab_pos'] = tab_pos

    print("\n=== Tablatura ===")
    
    def format_tab_cell(fret):
        if fret is None:
            return "----"
        fret_str = str(fret)
        if len(fret_str) == 1:
            return f"-{fret_str}--"
        return f"{fret_str}--"

    strings = ['e', 'B', 'G', 'D', 'A', 'E']
    tab_lines = [string_name + '|' for string_name in strings]
    for note_data in sequence:
        for idx in range(len(strings)):
            if note_data['tab_pos'] is not None and idx == 5 - note_data['tab_pos'][0]:
                tab_lines[idx] += format_tab_cell(note_data['tab_pos'][1]) + '|'
            else:
                tab_lines[idx] += "----|"

    print("\nTab:")
    for line in tab_lines:
        print(line)
