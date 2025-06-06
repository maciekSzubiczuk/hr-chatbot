from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from engine import ChatbotEngine
from speech_utils import SPEECH_AVAILABLE, recognize_speech, speak


class ChatbotGUI(tk.Tk):
    """Interfejs graficzny. Jeśli audio dostępne – przycisk 🎤."""

    COLORS_LIGHT = {
        "bg": "#f6f7fb",
        "panel": "#ffffff",
        "user_fg": "#1448d4",
        "user_bg": "#dbe4ff",
        "bot_fg": "#075d1b",
        "bot_bg": "#d4ffe2",
        "sys_fg": "#666666",
        "sys_bg": "#ececec",
        "entry_bg": "#ffffff",
    }
    COLORS_DARK = {
        "bg": "#1e1f22",
        "panel": "#2c2e32",
        "user_fg": "#6ea8ff",
        "user_bg": "#163b7b",
        "bot_fg": "#59d68c",
        "bot_bg": "#094220",
        "sys_fg": "#bbbbbb",
        "sys_bg": "#3d3d3d",
        "entry_bg": "#2c2e32",
    }

    def __init__(self) -> None:
        super().__init__()
        self.dark_mode = False
        self.engine = ChatbotEngine()

        self.title("🤖 Chatbot Rekrutacyjny")
        self.minsize(760, 540)
        self._apply_theme()

        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(
            header,
            text="🤖 Chatbot Rekrutacyjny",
            style="Title.TLabel",
            anchor="center",
        ).pack(side=tk.LEFT, padx=12, pady=8)

        theme_btn = ttk.Button(
            header,
            text="🌙",
            width=3,
            command=self._toggle_theme,
            style="Accent.TButton",
        )
        theme_btn.pack(side=tk.RIGHT, padx=8, pady=6)

        chat_frame = ttk.Frame(self, style="Panel.TFrame")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            state="disabled",
            wrap=tk.WORD,
            relief=tk.FLAT,
            font=("Segoe UI", 11),
            padx=10,
            pady=10,
            bd=0,
            cursor="arrow",
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self._config_tags()

        entry_frame = ttk.Frame(self, style="Panel.TFrame")
        entry_frame.pack(fill=tk.X, padx=6, pady=6)

        self.entry = ttk.Entry(entry_frame, font=("Segoe UI", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Control-Return>", self._on_enter)

        send_btn = ttk.Button(
            entry_frame,
            text="Wyślij",
            command=self._on_enter,
            style="Accent.TButton",
        )
        send_btn.pack(side=tk.LEFT, padx=(6, 0))

        if SPEECH_AVAILABLE:
            self.btn_speech = ttk.Button(
                entry_frame, text="🎤", width=3, command=self._toggle_speech
            )
            self.btn_speech.pack(side=tk.LEFT, padx=(6, 0))
            self.speech_on = False
            self.speech_queue: queue.Queue[str] = queue.Queue()
            self.bind("<<SpeechRecognized>>", self._on_speech_recognized)
            self.asr_thread = threading.Thread(target=self._speech_loop, daemon=True)

        self._write("System", "Witaj! Napisz \"asystent\" aby wejść w tryb LLM.")

    def _apply_theme(self) -> None:
        colors = self.COLORS_DARK if self.dark_mode else self.COLORS_LIGHT
        self.configure(bg=colors["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Panel.TFrame", background=colors["panel"])
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 16, "bold"),
            background=colors["panel"],
            foreground=colors["user_fg"],
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=6,
        )

    def _toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        self._config_tags()
        c = self.COLORS_DARK if self.dark_mode else self.COLORS_LIGHT
        self.chat_area.configure(bg=c["panel"])
        self.entry.configure(background=c["entry_bg"], foreground=c["user_fg"])

    def _config_tags(self) -> None:
        c = self.COLORS_DARK if self.dark_mode else self.COLORS_LIGHT

        self.chat_area.tag_configure(
            "user",
            foreground=c["user_fg"],
            background=c["user_bg"],
            font=("Segoe UI", 11, "bold"),
            lmargin1=6,
            lmargin2=6,
            rmargin=6,
            spacing1=4,
            spacing3=4,
        )

        self.chat_area.tag_configure(
            "bot",
            foreground=c["bot_fg"],
            background=c["bot_bg"],
            font=("Segoe UI", 11),
            lmargin1=6,
            lmargin2=6,
            rmargin=6,
            spacing1=4,
            spacing3=4,
        )

        self.chat_area.tag_configure(
            "system",
            foreground=c["sys_fg"],
            background=c["sys_bg"],
            font=("Segoe UI", 10, "italic"),
            justify="center",
            lmargin1=6,
            lmargin2=6,
            rmargin=6,
            spacing1=6,
            spacing3=6,
        )

    def _write(self, speaker: str, text: str) -> None:
        tag = {"Ty": "user", "Bot": "bot"}.get(speaker, "system")
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"{speaker}: {text}\n", tag)
        self.chat_area.configure(state="disabled")
        self.chat_area.yview(tk.END)

    def _on_enter(self, event=None) -> None:  # type: ignore[override]
        user_txt = self.entry.get().strip()
        if not user_txt:
            return
        self.entry.delete(0, tk.END)
        self._write("Ty", user_txt)

        resp = self.engine.handle(user_txt)
        self._write("Bot", resp)

        if SPEECH_AVAILABLE and getattr(self, "speech_on", False):
            speak(resp)

    def _toggle_speech(self) -> None:
        self.speech_on = not getattr(self, "speech_on", False)
        self.btn_speech.state(["pressed" if self.speech_on else "!pressed"])
        if self.speech_on and not self.asr_thread.is_alive():
            self.asr_thread.start()

    def _speech_loop(self) -> None:
        while True:
            if not getattr(self, "speech_on", False):
                continue
            text, _conf = recognize_speech(timeout=5)
            if text:
                self.speech_queue.put(text)
                self.event_generate("<<SpeechRecognized>>", when="tail")

    def _on_speech_recognized(self, _event) -> None:
        try:
            txt = self.speech_queue.get_nowait()
        except queue.Empty:
            return
        self.entry.delete(0, tk.END)
        self.entry.insert(0, txt)
        self._on_enter()
