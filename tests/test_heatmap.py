import time
from c64debugger.heatmap.heatmap_engine import MemoryHeatmap

def test_heatmap_basic():
    heatmap = MemoryHeatmap(fade_duration=2.0)
    assert heatmap.enabled is False

    # Recording access when disabled should do nothing
    heatmap.record_access(0xC000, 'X')
    assert heatmap.access_types[0xC000] is None

    # Enable and record access
    heatmap.enabled = True
    t0 = time.time()
    heatmap.record_access(0xC000, 'X', timestamp=t0)
    assert heatmap.access_types[0xC000] == 'X'
    assert heatmap.access_timestamps[0xC000] == t0

    # Get color
    color_x = heatmap.get_ansi_color(0xC000, 0xEA, current_time=t0)
    assert "\033[93m" in color_x  # Yellow for execute

    # Test fade out
    color_fade = heatmap.get_ansi_color(0xC000, 0xEA, current_time=t0 + 3.0)
    # Since t0 + 3.0 is beyond fade_duration of 2.0, color should default to color of value 0xEA
    # 0xEA is 234, which is in range for Blue or Bold White
    assert "\033[93m" not in color_fade


def test_heatmap_colors_and_grid():
    heatmap = MemoryHeatmap(fade_duration=5.0)
    heatmap.enabled = True
    heatmap.color_mode = "RGB"

    # Red for 0-85
    assert heatmap.get_color_for_value(10) == "\033[31m"
    # Green for 86-170
    assert heatmap.get_color_for_value(100) == "\033[32m"
    # Blue for 171-255
    assert heatmap.get_color_for_value(200) == "\033[34m"

    # Test render_grid
    data = b"\x00" * 32
    lines = heatmap.render_grid(0xC000, data)
    assert len(lines) == 2
    assert "$C000" in lines[0]
    assert "$C010" in lines[1]
