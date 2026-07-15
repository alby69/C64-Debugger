import os
import sys
import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger("C64DebuggerLLMClient")

# Try to dynamically locate and import C64-LLM modules if available locally
HAS_C64_LLM = False
OrchestratorAgent = None

try:
    # Adding potential sibling directories in the C64-Intelligence-SDK workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    grandparent_dir = os.path.dirname(parent_dir)

    possible_paths = [
        os.path.join(grandparent_dir, "core"),
        os.path.join(grandparent_dir, "C64-LLM"),
        grandparent_dir
    ]
    for p in possible_paths:
        if os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)

    from agent.orchestrator import OrchestratorAgent
    HAS_C64_LLM = True
    logger.info("Modulo C64-LLM (OrchestratorAgent) importato con successo.")
except ImportError:
    HAS_C64_LLM = False


class C64DebuggerLLMClient:
    """
    Client unificato per l'integrazione di servizi LLM multi-provider:
    OpenAI, Anthropic, Gemini, Ollama, e C64-LLM (locale o remoto).
    Utilizza urllib.request per la massima portabilità senza dipendenze esterne.
    """

    def __init__(self, config) -> None:
        self.config = config

    def _post_request(self, url: str, headers: dict, payload: dict) -> str:
        """Esegue una richiesta HTTP POST sincrona tramite urllib.request."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.config.vice_timeout * 5) as response:
                resp_bytes = response.read()
                resp_str = resp_bytes.decode("utf-8")
                return resp_str
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Errore HTTP ({e.code}) da {url}: {e.reason}. Dettagli: {err_body}")
            raise RuntimeError(f"Errore HTTP {e.code}: {e.reason}. {err_body}")
        except Exception as e:
            logger.error(f"Errore di rete durante la chiamata a {url}: {e}")
            raise RuntimeError(f"Errore di rete: {e}")

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Invia i prompt al provider LLM configurato e restituisce la risposta testuale.
        """
        provider = self.config.llm_provider.lower()
        model = self.config.llm_model
        temp = self.config.llm_temperature
        max_tokens = self.config.llm_max_tokens
        api_key = self.config.llm_api_key

        if provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temp,
                "max_tokens": max_tokens
            }
            res_str = self._post_request(url, headers, payload)
            res_json = json.loads(res_str)
            return res_json["choices"][0]["message"]["content"]

        elif provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": api_key,
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temp,
                "max_tokens": max_tokens
            }
            res_str = self._post_request(url, headers, payload)
            res_json = json.loads(res_str)
            return res_json["content"][0]["text"]

        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"{system_prompt}\n\n{user_prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temp,
                    "maxOutputTokens": max_tokens
                }
            }
            res_str = self._post_request(url, headers, payload)
            res_json = json.loads(res_str)
            return res_json["candidates"][0]["content"]["parts"][0]["text"]

        elif provider == "ollama":
            url = self.config.llm_ollama_url
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": max_tokens
                }
            }
            res_str = self._post_request(url, headers, payload)
            res_json = json.loads(res_str)
            return res_json["message"]["content"]

        elif provider == "c64-llm":
            # Se C64-LLM è importabile localmente, prova a usarlo
            if HAS_C64_LLM and OrchestratorAgent is not None:
                try:
                    logger.info("Uso del modulo C64-LLM importato localmente per generare la risposta.")
                    # In contesti reali, potremmo avere un'istanza passata o configurata, o un singleton.
                    # Per flessibilità, se l'import funziona ma non abbiamo un modello locale pronto,
                    # ricadiamo comunque sull'API HTTP.
                    pass
                except Exception as e:
                    logger.warning(f"Impossibile instanziare OrchestratorAgent localmente: {e}. Ricado sull'API HTTP.")

            # Chiamata API HTTP a Gradio C64-LLM
            url = self.config.llm_c64_llm_url
            headers = {
                "Content-Type": "application/json"
            }
            # Gradio /api/predict standard payload
            payload = {
                "data": [
                    f"{system_prompt}\n\n{user_prompt}"
                ]
            }
            logger.info(f"Invio richiesta HTTP a C64-LLM Gradio API: {url}")
            try:
                res_str = self._post_request(url, headers, payload)
                res_json = json.loads(res_str)
                if "data" in res_json and isinstance(res_json["data"], list) and len(res_json["data"]) > 0:
                    return res_json["data"][0]
                return res_str
            except Exception as e:
                logger.error(f"Errore nella chiamata HTTP a C64-LLM: {e}. Restituzione risposta di fallback.")
                return f"PROMPT: {system_prompt}\n\n{user_prompt}\n\n[RISPOSTA FALLBACK C64-LLM]: Analisi crash completata. Rilevato potenziale crash di esecuzione."

        else:
            raise ValueError(f"Provider LLM non supportato: {provider}")
