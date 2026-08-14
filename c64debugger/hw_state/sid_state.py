import math
from typing import Dict, Any, List

def freq_to_note(freq_hz: float) -> str:
    """
    Converte una frequenza in Hz nella nota musicale corrispondente (es: A-4 per 440Hz).
    """
    if freq_hz <= 16.35:  # Sotto il C-0
        return "None"
    try:
        midi_note = round(12 * math.log2(freq_hz / 440.0) + 69)
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12
        if 0 <= octave <= 9:
            return f"{note_names[note_index]}-{octave}"
    except (ValueError, OverflowError):
        pass
    return "None"


class SIDState:
    """
    Rappresenta lo stato del chip audio SID ($D400-$D41C).
    """
    def __init__(self, data: bytes = b"") -> None:
        self.raw_data = data if len(data) >= 29 else b"\x00" * 29
        self.voices: List[Dict[str, Any]] = []
        self.cutoff_freq: int = 0
        self.resonance: int = 0
        self.volume: int = 0
        self.parse()

    def parse(self) -> None:
        d = self.raw_data
        self.voices = []

        # Parse the 3 voices
        for v_idx in range(3):
            base = v_idx * 7
            freq_raw = d[base] | (d[base + 1] << 8)
            # Freq_Hz = (freq_raw * 985248) / 16777216 for PAL C64
            freq_hz = (freq_raw * 985248.0) / 16777216.0

            pw_raw = d[base + 2] | ((d[base + 3] & 0x0F) << 8)
            ctrl = d[base + 4]
            ad = d[base + 5]
            sr = d[base + 6]

            # Waveforms
            noise = bool(ctrl & 0x80)
            pulse = bool(ctrl & 0x40)
            sawtooth = bool(ctrl & 0x20)
            triangle = bool(ctrl & 0x10)
            test = bool(ctrl & 0x08)
            ring = bool(ctrl & 0x04)
            sync = bool(ctrl & 0x02)
            gate = bool(ctrl & 0x01)

            # ADSR
            attack = (ad & 0xF0) >> 4
            decay = ad & 0x0F
            sustain = (sr & 0xF0) >> 4
            release = sr & 0x0F

            waveform_name = "None"
            if noise:
                waveform_name = "Noise"
            elif pulse:
                waveform_name = "Pulse"
            elif sawtooth:
                waveform_name = "Sawtooth"
            elif triangle:
                waveform_name = "Triangle"

            self.voices.append({
                "voice_index": v_idx + 1,
                "frequency_raw": freq_raw,
                "frequency_hz": round(freq_hz, 2),
                "note": freq_to_note(freq_hz) if (freq_hz > 0 and (pulse or sawtooth or triangle)) else "None",
                "pulse_width": pw_raw,
                "waveform": waveform_name,
                "gate": gate,
                "test": test,
                "ring": ring,
                "sync": sync,
                "attack": attack,
                "decay": decay,
                "sustain": sustain,
                "release": release
            })

        # Filter Cutoff ($D415-$D416) -> 11-bit
        self.cutoff_freq = (d[0x15] & 0x07) | (d[0x16] << 3)

        # Resonance ($D417)
        self.resonance = (d[0x17] & 0xF0) >> 4

        # Volume ($D418)
        self.volume = d[0x18] & 0x0F

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voices": self.voices,
            "cutoff_freq": self.cutoff_freq,
            "resonance": self.resonance,
            "volume": self.volume
        }
