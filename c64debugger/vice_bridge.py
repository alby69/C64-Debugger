import socket
import struct
import subprocess
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Union, Tuple, Optional, List
from .vice_protocol import VICEMonitorProtocol

# Configure logging with support for file rotators
logger = logging.getLogger("VICERemoteMonitorBridge")

def setup_logger(log_file: Optional[str] = None, log_level: int = logging.INFO, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
    """
    Sets up the bridge logger. Optionally adds a rotating file handler.
    """
    logger.setLevel(log_level)
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

class VICERemoteMonitorBridge:
    """
    Bridge di connessione remota per il monitor dell'emulatore VICE (x64sc).
    Supporta sia l'interfaccia a riga di comando (CLI Monitor) sia la connessione
    via socket TCP al monitor (testuale o binario).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6510) -> None:
        self.host: str = host
        self.port: int = port
        self.socket: Optional[socket.socket] = None
        self.vice_process: Optional[subprocess.Popen] = None

    def start_vice_headless(self, prg_path: Optional[str] = None, limit_cycles: int = 10000000, extra_args: Optional[List[str]] = None) -> bool:
        """
        Avvia l'emulatore x64sc (VICE) in modalità headless (senza interfaccia grafica)
        abilitando il monitor remoto TCP sulla porta configurata.
        """
        args = [
            "x64sc",
            "-default",
            "-headless",           # Rende l'interfaccia invisibile (disponibile in VICE moderno)
            "-sound", "none",      # Disabilita il suono per risparmiare CPU
            "-monitorport", str(self.port)  # Abilita il monitor di testo sulla porta configurata
        ]

        if limit_cycles:
            args.extend(["-limitcycles", str(limit_cycles)])

        if prg_path:
            args.extend(["-autostartprgmode", "1", prg_path])

        if extra_args:
            args.extend(extra_args)

        try:
            logger.info(f"Avvio di VICE con comando: {' '.join(args)}")
            # Avviamo il processo in background
            self.vice_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Diamo all'emulatore un attimo per avviarsi e bindare la porta socket
            time.sleep(1.5)
            return True
        except FileNotFoundError:
            logger.error("Emulatore 'x64sc' non trovato nel sistema. Assicurati che VICE sia installato e nel PATH.")
            return False
        except Exception as e:
            logger.error(f"Errore durante l'avvio di VICE: {e}")
            return False

    def connect(self, timeout: float = 2.0, max_retries: int = 5, backoff_factor: float = 1.5) -> Tuple[bool, str]:
        """
        Connette il bridge alla porta monitor TCP di VICE con retry ed esponenziale backoff.
        """
        retry_delay = 0.5
        for attempt in range(max_retries):
            try:
                logger.info(f"Tentativo di connessione a VICE su {self.host}:{self.port} (tentativo {attempt + 1}/{max_retries})...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(timeout)
                self.socket.connect((self.host, self.port))

                # Legge il banner iniziale inviato da VICE (se presente)
                try:
                    banner = self.socket.recv(1024).decode("utf-8", errors="ignore")
                    logger.info(f"Ricevuto banner di benvenuto da VICE: {banner.strip()}")
                except socket.timeout:
                    pass

                logger.info(f"Connesso con successo al Monitor di VICE su {self.host}:{self.port}")
                return True, "Connesso con successo!"
            except Exception as e:
                self.socket = None
                if attempt == max_retries - 1:
                    err_msg = f"Impossibile connettersi al monitor TCP di VICE dopo {max_retries} tentativi: {e}."
                    logger.error(err_msg)
                    return False, err_msg
                logger.warning(f"Connessione fallita ({e}). Attesa di {retry_delay:.2f} secondi prima del prossimo tentativo...")
                time.sleep(retry_delay)
                retry_delay *= backoff_factor

        return False, "Impossibile connettersi."

    def send_command(self, cmd: str) -> str:
        """
        Invia un comando testuale al monitor (es. 'r' per visualizzare i registri,
        'm 0400 0410' per visualizzare una porzione di memoria).
        Ritorna la risposta testuale inviata dall'emulatore.
        """
        if not self.socket:
            logger.warning("Nessuna connessione attiva con VICE.")
            return "Nessuna connessione attiva."

        try:
            # Pulisce i buffer di input rimasti
            self.socket.settimeout(0.1)
            try:
                while True:
                    self.socket.recv(1024)
            except socket.timeout:
                pass

            # Ripristina il timeout originale
            self.socket.settimeout(2.0)

            # Invia il comando testuale seguito da a capo
            if not cmd.endswith("\n"):
                cmd += "\n"

            self.socket.sendall(cmd.encode("utf-8"))

            # Ricezione risposta
            response = ""
            # Continua a leggere finché non incontra il prompt del monitor "(C64)" o simile,
            # oppure finché non va in timeout (se il comando non restituisce output)
            while True:
                data = self.socket.recv(2048).decode("utf-8", errors="ignore")
                if not data:
                    break
                response += data
                # Il prompt tipico del monitor VICE è '(CBRK)' o '(C64)' o 'sys' o '.'
                if any(prompt in response for prompt in ["(C64)", "(CBRK)", "(C64 debugger)", "(C64 monitor)"]):
                    break

            return response.strip()
        except socket.timeout:
            logger.warning("Timeout durante l'attesa della risposta da VICE.")
            return response.strip() if response else "Timeout"
        except Exception as e:
            logger.error(f"Errore di comunicazione: {e}")
            return f"Errore: {e}"

    def get_registers(self) -> Dict[str, Union[int, str]]:
        """
        Esegue il comando 'r' sul monitor e decodifica i registri del processore 6502.
        Ritorna un dizionario con PC, A, X, Y, SP e i flag.
        """
        response = self.send_command("r")
        return VICEMonitorProtocol.parse_registers(response)

    def read_memory(self, start_addr: int, end_addr: int) -> bytes:
        """
        Legge una porzione di memoria usando il comando 'm'.
        Ritorna l'array di byte letti.
        """
        cmd = VICEMonitorProtocol.format_read_memory(start_addr, end_addr)
        response = self.send_command(cmd)
        return VICEMonitorProtocol.parse_memory(response)

    def write_memory(self, addr: int, data: bytes) -> bool:
        """
        Scrive dei byte in memoria usando il comando '>' del monitor.
        """
        if not data:
            return True
        cmd = VICEMonitorProtocol.format_write_memory(addr, data)
        self.send_command(cmd)
        return True

    def write_registers(self, regs: Dict[str, Union[int, str]]) -> bool:
        """
        Scrive i registri CPU usando il comando del monitor (es: '> PC c000').
        """
        for k, v in regs.items():
            if k in ("PC", "A", "X", "Y", "SP") and isinstance(v, int):
                cmd = f"> {k} {v:02x}" if k != "PC" else f"> {k} {v:04x}"
                self.send_command(cmd)
        return True

    def set_breakpoint(self, addr: int) -> bool:
        """
        Imposta un breakpoint ad un indirizzo specifico.
        """
        cmd = VICEMonitorProtocol.format_breakpoint(addr)
        response = self.send_command(cmd)
        return "Breakpoint" in response or "impostato" in response or "Breakpoint" in self.send_command("bk")

    def step_instruction(self) -> Dict[str, Union[int, str]]:
        """
        Esegue un singolo step (istruzione successiva) e ritorna lo stato dei registri.
        """
        self.send_command("z")  # Comando 'z' in VICE esegue il single step (oppure 'step')
        return self.get_registers()

    def stop_execution(self) -> None:
        """
        Invia un comando di stop all'emulatore.
        """
        self.send_command("stop")

    def resume_execution(self) -> None:
        """
        Invia un comando di go per riprendere l'esecuzione ordinaria.
        """
        self.send_command("g")

    def disconnect(self) -> None:
        """
        Chiude la connessione socket.
        """
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.debug(f"Errore durante la chiusura del socket: {e}")
            self.socket = None
            logger.info("Connessione socket chiusa.")

    def kill_vice(self) -> None:
        """
        Termina forzatamente il processo dell'emulatore VICE.
        """
        self.disconnect()
        if self.vice_process:
            try:
                self.vice_process.kill()
                logger.info("Processo VICE terminato.")
            except Exception as e:
                logger.debug(f"Errore durante il kill di VICE: {e}")
            self.vice_process = None
        else:
            # Fallback generico per killare istanze orfane
            try:
                os.system("killall -9 x64sc 2>/dev/null || true")
            except Exception as e:
                logger.debug(f"Errore durante il killall di x64sc: {e}")
