from __future__ import annotations

import datetime as dt
import re
from typing import Callable, Dict, List

from config import GROQ_API_KEY, GROQ_MODEL
import groq

client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
LLM_AVAILABLE = client is not None

class ChatbotEngine:
    def __init__(self) -> None:
        self.mode = "commands"
        self.chat_history: List[dict[str, str]] = []

        self.system_prompt = {
            "role": "system",
            "content": (
                "Jesteś asystentem rekrutacyjnym. "
                "Odpowiadaj wyłącznie na pytania związane z szeroko pojętym rynkiem pracy, procesem rekrutacji, "
                "ogłoszeniami, aplikacjami, statusem kandydatów itp. "
                "Nie odpowiadaj na pytania spoza tego zakresu (np. przepisy kulinarne, porady niezwiązane z pracą)."
            ),
        }

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        self.command_handlers: Dict[str, Callable[[], str]] = {
            "która godzina":      self._cmd_time,
            "lista ofert":        self._cmd_offers,
            "złóż aplikację":     self._cmd_apply,
            "status aplikacji":   self._cmd_status,
            "asystent":           self._cmd_assistant,
            "tryb komend":        self._cmd_commands,
        }

    def _cmd_time(self) -> str:
        return f"Aktualny czas: {dt.datetime.now():%H:%M:%S}"

    def _cmd_offers(self) -> str:
        return (
            "Oto przykładowe oferty pracy:\n"
            "1. Python Developer\n"
            "2. Data Analyst\n"
            "3. DevOps Engineer"
        )

    def _cmd_apply(self) -> str:
        return "Aby złożyć aplikację, podaj imię, nazwisko i adres e-mail – prześlemy Ci formularz."

    def _cmd_status(self) -> str:
        return "Twoja aplikacja jest w trakcie weryfikacji. Skontaktujemy się wkrótce."

    def _cmd_assistant(self) -> str:
        if not LLM_AVAILABLE:
            return "Funkcja asystenta niedostępna – ustaw `GROQ_API_KEY` w .env."
        self.mode = "assistant"
        self.chat_history = [self.system_prompt.copy()]
        return "Tryb LLM aktywny – możesz zadawać pytania o rekrutację."

    def _cmd_commands(self) -> str:
        self.mode = "commands"
        return "Powrót do komend lokalnych."

    def _ask_llm(self, prompt: str) -> str:
        if not LLM_AVAILABLE:
            return "LLM niedostępny."

        self.chat_history.append({"role": "user", "content": prompt})
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=self.chat_history,
                temperature=0.7,
            )
            answer = resp.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as exc:
            return f"Błąd Groq: {exc}"

    def handle(self, user_text: str) -> str:
        cmd = re.sub(r"\?$", "", user_text.lower().strip())

        if self.mode == "commands":
            fn = self.command_handlers.get(cmd)
            if fn:
                return fn()
            return f"Nie rozumiem komendy. Dostępne: {', '.join(sorted(self.command_handlers))}"

        if cmd == "tryb komend":
            return self._cmd_commands()
        return self._ask_llm(user_text)
