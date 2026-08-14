from c64debugger.hw_state.vic_state import VICState
from c64debugger.hw_state.sid_state import SIDState, freq_to_note
from c64debugger.hw_state.cia_state import CIAState

def test_vic_state_parsing():
    # 47 bytes for VIC-II registers $D000-$D02E
    data = bytearray(47)
    data[0x11] = 0x1B  # Screen on, 25 rows, vertical scroll 3
    data[0x12] = 0x24  # Raster line 36
    data[0x15] = 0x03  # Sprites 0 & 1 enabled
    data[0x16] = 0x18  # Multicolor, 40 cols, horizontal scroll 0
    data[0x18] = 0x14  # Screen matrix at $0400, charset at $1000

    vic = VICState(bytes(data))
    info = vic.to_dict()

    assert info["raster_line"] == 36
    assert info["screen_on"] is True
    assert info["row_select"] == 25
    assert info["column_select"] == 40
    assert info["multicolor_mode"] is True
    assert info["sprite_enable"] == [True, True, False, False, False, False, False, False]


def test_sid_state_parsing():
    # 29 bytes for SID registers $D400-$D41C
    data = bytearray(29)
    # Voice 1 freq: $1D4C ~ 440 Hz (standard PAL A-4)
    # 1D4C in decimal is 7500
    # (7500 * 985248) / 16777216 = 440.44 Hz (A-4)
    data[0] = 0x4C
    data[1] = 0x1D
    data[4] = 0x21  # Sawtooth waveform + Gate ON
    data[5] = 0x0F  # AD: Attack 0, Decay 15
    data[6] = 0xF0  # SR: Sustain 15, Release 0

    data[0x18] = 0x0F  # Max Volume

    sid = SIDState(bytes(data))
    info = sid.to_dict()

    assert info["volume"] == 15
    voice1 = info["voices"][0]
    assert voice1["frequency_raw"] == 0x1D4C
    assert voice1["waveform"] == "Sawtooth"
    assert voice1["gate"] is True
    assert voice1["note"] == "A-4"


def test_freq_to_note_helpers():
    assert freq_to_note(440.0) == "A-4"
    assert freq_to_note(261.63) == "C-4"
    assert freq_to_note(0.0) == "None"


def test_cia_state_parsing():
    # 16 bytes for CIA registers
    data = bytearray(16)
    data[0x04] = 0x34
    data[0x05] = 0x12  # Timer A = $1234
    data[0x0E] = 0x01  # CRA: Timer A started
    data[0x08] = 0x05  # Tenths of seconds
    data[0x09] = 0x12  # 12 seconds
    data[0x0A] = 0x34  # 34 minutes
    data[0x0B] = 0x91  # 11 hours, PM (bit 7 is 1)

    cia = CIAState(bytes(data), "CIA1")
    info = cia.to_dict()

    assert info["name"] == "CIA1"
    assert info["timer_a"] == 0x1234
    assert info["timer_a_active"] is True
    assert info["tod"] == "11:34:12.5"
    assert info["tod_pm"] is True
