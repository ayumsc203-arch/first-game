import os
import math
import wave
import struct

def generate_wav(filename, duration, sample_rate, wave_func):
    """Generates a WAV file using a custom waveform function."""
    num_samples = int(duration * sample_rate)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = i / sample_rate
            value = wave_func(t, duration)
            # Clip and convert to 16-bit signed integer
            val = int(max(-32767, min(32767, value * 32767)))
            wav_file.writeframesraw(struct.pack('<h', val))

def create_click(t, d):
    # Quick decay high pitch
    envelope = math.exp(-30 * t)
    return math.sin(2 * math.pi * 1000 * t) * envelope

def create_hover(t, d):
    # Quiet quick low pitch click
    envelope = math.exp(-60 * t)
    return math.sin(2 * math.pi * 400 * t) * envelope * 0.3

def create_snap(t, d):
    # Woodblock-like sound
    envelope = math.exp(-15 * t)
    return math.sin(2 * math.pi * 600 * t) * envelope

def create_wrong(t, d):
    # Two detuned low frequencies
    envelope = math.exp(-8 * t)
    wave1 = math.sin(2 * math.pi * 150 * t)
    wave2 = math.sin(2 * math.pi * 155 * t)
    return (wave1 + wave2) * 0.5 * envelope

def create_shutter(t, d):
    # White noise-like burst mixed with a click
    # Simple pseudo-random using t
    envelope = math.exp(-15 * t)
    import random
    noise = random.uniform(-1, 1)
    click = math.sin(2 * math.pi * 800 * t) * math.exp(-100 * t)
    return (noise * 0.5 + click * 0.5) * envelope

def create_countdown(t, d):
    # Clean beep
    envelope = 1.0 if t < d - 0.05 else math.exp(-100 * (t - (d - 0.05)))
    return math.sin(2 * math.pi * 800 * t) * envelope * 0.5

def create_countdown_smile(t, d):
    # Higher pitch beep
    envelope = 1.0 if t < d - 0.05 else math.exp(-100 * (t - (d - 0.05)))
    return math.sin(2 * math.pi * 1200 * t) * envelope * 0.6

def create_victory(t, d):
    # Multi-note arpeggio (C major: C4, E4, G4, C5)
    notes = [261.63, 329.63, 392.00, 523.25]
    num_notes = len(notes)
    note_duration = d / num_notes
    note_index = int(t / note_duration)
    if note_index >= num_notes:
        note_index = num_notes - 1
    
    freq = notes[note_index]
    # Local t within the note
    local_t = t % note_duration
    # Easing out at the end of each note slightly, and overall fade
    note_env = math.exp(-3 * local_t)
    overall_env = (d - t) / d
    return math.sin(2 * math.pi * freq * t) * note_env * overall_env * 0.6

def generate_all_sounds(target_dir):
    sounds = {
        "click.wav": (0.1, create_click),
        "hover.wav": (0.05, create_hover),
        "snap.wav": (0.15, create_snap),
        "wrong.wav": (0.4, create_wrong),
        "shutter.wav": (0.3, create_shutter),
        "countdown.wav": (0.25, create_countdown),
        "countdown_smile.wav": (0.5, create_countdown_smile),
        "victory.wav": (1.2, create_victory)
    }
    
    sample_rate = 44100
    for filename, (duration, func) in sounds.items():
        filepath = os.path.join(target_dir, filename)
        generate_wav(filepath, duration, sample_rate, func)
        print(f"Generated: {filepath}")

if __name__ == "__main__":
    import sys
    dest = sys.argv[1] if len(sys.argv) > 1 else "../assets/sounds"
    generate_all_sounds(dest)
