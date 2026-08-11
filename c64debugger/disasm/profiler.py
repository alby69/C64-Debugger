from typing import Dict, List, Any

class C64Profiler:
    """
    Profiler di base per codice 6502 del Commodore 64.
    Tiene traccia delle esecuzioni (hits) e dei cicli macchina spesi per ciascun indirizzo.
    """

    def __init__(self) -> None:
        self.hits: Dict[int, int] = {}
        self.cycles: Dict[int, int] = {}
        self.is_running: bool = False

    def start(self) -> None:
        """Avvia la sessione di profiling."""
        self.is_running = True

    def stop(self) -> None:
        """Arresta la sessione di profiling."""
        self.is_running = False

    def reset(self) -> None:
        """Azzera tutti i dati raccolti dal profiler."""
        self.hits.clear()
        self.cycles.clear()

    def record_sample(self, address: int, cycles_spent: int = 2) -> None:
        """
        Registra un campione di esecuzione per un determinato indirizzo.

        Args:
            address: Indirizzo dell'istruzione eseguita.
            cycles_spent: Cicli CPU impiegati dall'istruzione (default standard: 2).
        """
        if not self.is_running:
            return

        address &= 0xFFFF
        self.hits[address] = self.hits.get(address, 0) + 1
        self.cycles[address] = self.cycles.get(address, 0) + cycles_spent

    def get_report(self, sort_by: str = "cycles") -> List[Dict[str, Any]]:
        """
        Genera il report ordinato.

        Args:
            sort_by: Criterio di ordinamento ("hits" o "cycles").
        """
        report = []
        for addr in self.hits:
            report.append({
                "address": addr,
                "hits": self.hits[addr],
                "cycles": self.cycles.get(addr, 0)
            })

        if sort_by == "hits":
            report.sort(key=lambda x: x["hits"], reverse=True)
        else:
            report.sort(key=lambda x: x["cycles"], reverse=True)

        return report

    def format_report(self, limit: int = 20) -> str:
        """
        Ritorna una rappresentazione testuale formattata del report delle prestazioni.
        """
        report_data = self.get_report()[:limit]
        if not report_data:
            return "Nessun dato di profiling registrato."

        lines = [
            "==================================================",
            "          REPORT PROFILING PRESTAZIONI C64        ",
            "==================================================",
            f"{'Indirizzo':<12}{'Esecuzioni (Hits)':<20}{'Cicli CPU Stimati':<18}",
            "--------------------------------------------------"
        ]

        total_hits = sum(self.hits.values())
        total_cycles = sum(self.cycles.values())

        for entry in report_data:
            addr_str = f"${entry['address']:04X}"
            lines.append(f"{addr_str:<12}{entry['hits']:<20}{entry['cycles']:<18}")

        lines.append("--------------------------------------------------")
        lines.append(f"Totale hits:  {total_hits}")
        lines.append(f"Totale cicli: {total_cycles}")
        lines.append("==================================================")
        return "\n".join(lines)
