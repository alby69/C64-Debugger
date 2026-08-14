from typing import Dict, Any, List, Optional, Tuple

class TimelineEngine:
    """
    Gestisce la registrazione continua e la navigazione temporale dello stato della RAM
    e dei registri CPU del Commodore 64.
    """
    def __init__(self, max_snapshots: int = 300) -> None:
        self.max_snapshots = max_snapshots
        self.snapshots: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.enabled: bool = False

    def record_state(self, ram: bytes, registers: Dict[str, Any]) -> None:
        """
        Registra un nuovo stato nella timeline. Rimuove eventuali stati futuri orfani
        se ci troviamo nel mezzo di un rewind.
        """
        if not self.enabled:
            return

        if len(ram) != 65536:
            # Assicurati che sia un dump completo della RAM
            return

        # Se eravamo tornati indietro e registriamo un nuovo passo, tagliamo il futuro alternativo
        if -1 < self.current_index < len(self.snapshots) - 1:
            self.snapshots = self.snapshots[:self.current_index + 1]

        # Aggiunge il nuovo snapshot
        self.snapshots.append({
            "ram": ram,
            "registers": registers.copy()
        })

        # Mantiene il limite massimo di snapshot (ring buffer)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

        self.current_index = len(self.snapshots) - 1

    def rewind(self, steps: int = 1) -> Optional[Dict[str, Any]]:
        """
        Sposta l'indice corrente indietro di N passi. Ritorna lo stato corrispondente.
        """
        if not self.snapshots:
            return None
        self.current_index = max(0, self.current_index - steps)
        return self.snapshots[self.current_index]

    def forward(self, steps: int = 1) -> Optional[Dict[str, Any]]:
        """
        Sposta l'indice corrente in avanti di N passi. Ritorna lo stato corrispondente.
        """
        if not self.snapshots:
            return None
        self.current_index = min(len(self.snapshots) - 1, self.current_index + steps)
        return self.snapshots[self.current_index]

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.current_index < len(self.snapshots):
            return self.snapshots[self.current_index]
        return None

    def reset(self) -> None:
        self.snapshots.clear()
        self.current_index = -1

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "total_snapshots": len(self.snapshots),
            "current_index": self.current_index,
            "max_snapshots": self.max_snapshots
        }
