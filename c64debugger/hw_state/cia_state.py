from typing import Dict, Any

class CIAState:
    """
    Rappresenta lo stato di un chip CIA ($DC00-$DC0F o $DD00-$DD0F).
    """
    def __init__(self, data: bytes = b"", name: str = "CIA1") -> None:
        self.raw_data = data if len(data) >= 16 else b"\x00" * 16
        self.name = name
        self.port_a: int = 0
        self.port_b: int = 0
        self.timer_a: int = 0
        self.timer_b: int = 0
        self.tod_hours: int = 0
        self.tod_minutes: int = 0
        self.tod_seconds: int = 0
        self.tod_tenths: int = 0
        self.tod_pm: bool = False
        self.icr: int = 0
        self.cra: int = 0
        self.crb: int = 0
        self.timer_a_active: bool = False
        self.timer_b_active: bool = False
        self.parse()

    def parse(self) -> None:
        d = self.raw_data
        self.port_a = d[0x00]
        self.port_b = d[0x01]
        self.timer_a = d[0x04] | (d[0x05] << 8)
        self.timer_b = d[0x06] | (d[0x07] << 8)
        self.tod_tenths = d[0x08] & 0x0F
        self.tod_seconds = ((d[0x09] & 0x70) >> 4) * 10 + (d[0x09] & 0x0F)
        self.tod_minutes = ((d[0x0A] & 0x70) >> 4) * 10 + (d[0x0A] & 0x0F)
        # TOD Hours: bit 7 is AM/PM (1 = PM, 0 = AM)
        self.tod_pm = bool(d[0x0B] & 0x80)
        self.tod_hours = ((d[0x0B] & 0x10) >> 4) * 10 + (d[0x0B] & 0x0F)
        self.icr = d[0x0D]
        self.cra = d[0x0E]
        self.crb = d[0x0F]

        self.timer_a_active = bool(self.cra & 0x01)
        self.timer_b_active = bool(self.crb & 0x01)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "port_a": self.port_a,
            "port_b": self.port_b,
            "timer_a": self.timer_a,
            "timer_b": self.timer_b,
            "timer_a_active": self.timer_a_active,
            "timer_b_active": self.timer_b_active,
            "tod": f"{self.tod_hours:02d}:{self.tod_minutes:02d}:{self.tod_seconds:02d}.{self.tod_tenths}",
            "tod_pm": self.tod_pm,
            "icr": self.icr,
            "cra": self.cra,
            "crb": self.crb
        }
