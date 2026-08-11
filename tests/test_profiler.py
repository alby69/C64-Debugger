import pytest
from c64debugger.disasm.profiler import C64Profiler

def test_profiler_lifecycle():
    profiler = C64Profiler()
    assert not profiler.is_running

    profiler.start()
    assert profiler.is_running

    profiler.stop()
    assert not profiler.is_running

def test_profiler_recording():
    profiler = C64Profiler()
    profiler.start()

    profiler.record_sample(0xC000, 2)
    profiler.record_sample(0xC000, 3)
    profiler.record_sample(0xC002, 4)

    report = profiler.get_report(sort_by="cycles")
    assert len(report) == 2
    # 0xC002 has 4 cycles, 0xC000 has 5 cycles. So 0xC000 should be first when sorting by cycles
    assert report[0]["address"] == 0xC000
    assert report[0]["cycles"] == 5
    assert report[0]["hits"] == 2

    assert report[1]["address"] == 0xC002
    assert report[1]["cycles"] == 4
    assert report[1]["hits"] == 1

    # Now test sorting by hits
    profiler.record_sample(0xC002, 2) # Now 0xC002 has 2 hits, 0xC000 has 2 hits
    profiler.record_sample(0xC002, 2) # Now 0xC002 has 3 hits, 0xC000 has 2 hits
    report_hits = profiler.get_report(sort_by="hits")
    assert report_hits[0]["address"] == 0xC002

def test_profiler_format_report():
    profiler = C64Profiler()
    assert "Nessun dato" in profiler.format_report()

    profiler.start()
    profiler.record_sample(0xC000, 2)
    text = profiler.format_report()
    assert "$C000" in text
    assert "Totale hits:  1" in text
