from typing import Dict, Any, List

class VICState:
    """
    Rappresenta lo stato del chip video VIC-II ($D000-$D02E).
    """
    def __init__(self, data: bytes = b"") -> None:
        self.raw_data = data if len(data) >= 47 else b"\x00" * 47
        self.sprite_coords: List[tuple] = []
        self.raster_msb: int = 0
        self.ecm: bool = False
        self.bitmap_mode: bool = False
        self.screen_on: bool = False
        self.row_select: int = 25
        self.vertical_scroll: int = 0
        self.raster_line: int = 0
        self.sprite_enable: List[bool] = []
        self.multicolor_mode: bool = False
        self.column_select: int = 40
        self.horizontal_scroll: int = 0
        self.screen_matrix_base_offset: int = 0x0400
        self.bitmap_base_offset: int = 0
        self.charset_base_offset: int = 0
        self.border_color: int = 14
        self.background_color0: int = 6
        self.background_color1: int = 0
        self.background_color2: int = 0
        self.background_color3: int = 0
        self.bad_line: bool = False
        self.parse()

    def parse(self) -> None:
        d = self.raw_data
        self.sprite_coords = [
            (
                d[i * 2] | (256 if (d[0x10] & (1 << i)) else 0),
                d[i * 2 + 1]
            )
            for i in range(8)
        ]

        # Control Register 1 ($D011)
        r1 = d[0x11]
        self.raster_msb = (r1 & 0x80) >> 7
        self.ecm = bool(r1 & 0x40)
        self.bitmap_mode = bool(r1 & 0x20)
        self.screen_on = bool(r1 & 0x10)
        self.row_select = 25 if (r1 & 0x08) else 24
        self.vertical_scroll = r1 & 0x07

        # Raster Counter ($D012)
        self.raster_line = d[0x12] | (self.raster_msb << 8)

        # Sprite Enable ($D015)
        self.sprite_enable = [bool(d[0x15] & (1 << i)) for i in range(8)]

        # Control Register 2 ($D016)
        r2 = d[0x16]
        self.multicolor_mode = bool(r2 & 0x10)
        self.column_select = 40 if (r2 & 0x08) else 38
        self.horizontal_scroll = r2 & 0x07

        # Memory Pointers ($D018)
        mp = d[0x18]
        self.screen_matrix_base_offset = ((mp & 0xF0) >> 4) * 0x0400
        if self.bitmap_mode:
            self.bitmap_base_offset = ((mp & 0x08) >> 3) * 0x2000
            self.charset_base_offset = 0
        else:
            self.bitmap_base_offset = 0
            self.charset_base_offset = ((mp & 0x0E) >> 1) * 0x0800

        # Colors ($D020 - $D024)
        self.border_color = d[0x20] & 0x0F
        self.background_color0 = d[0x21] & 0x0F
        self.background_color1 = d[0x22] & 0x0F
        self.background_color2 = d[0x23] & 0x0F
        self.background_color3 = d[0x24] & 0x0F

        # Bad Line detection: Screen must be on, raster line must be in range $30-$F7,
        # and the lower 3 bits of raster line must match the vertical scroll value.
        self.bad_line = self.screen_on and (0x30 <= self.raster_line <= 0xF7) and ((self.raster_line & 0x07) == self.vertical_scroll)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raster_line": self.raster_line,
            "screen_on": self.screen_on,
            "bitmap_mode": self.bitmap_mode,
            "multicolor_mode": self.multicolor_mode,
            "ecm": self.ecm,
            "row_select": self.row_select,
            "column_select": self.column_select,
            "vertical_scroll": self.vertical_scroll,
            "horizontal_scroll": self.horizontal_scroll,
            "screen_matrix_base_offset": self.screen_matrix_base_offset,
            "bitmap_base_offset": self.bitmap_base_offset,
            "charset_base_offset": self.charset_base_offset,
            "border_color": self.border_color,
            "background_color": self.background_color0,
            "sprite_enable": self.sprite_enable,
            "sprite_coords": self.sprite_coords,
            "bad_line": self.bad_line
        }
