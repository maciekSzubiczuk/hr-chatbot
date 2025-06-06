# speech_utils.py
from __future__ import annotations
import queue
import threading

try:
    import pyttsx3
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    pyttsx3 = sr = None       # type: ignore
    SPEECH_AVAILABLE = False

# -----------------------  T T S  ----------------------------------
class _TTSWorker(threading.Thread):

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.q: queue.Queue[str] = queue.Queue()
        self.start()

    def run(self) -> None:
        engine = pyttsx3.init()
        while True:
            txt = self.q.get()
            if txt is None:
                break
            engine.say(txt)
            engine.runAndWait()

    def say(self, text: str) -> None:
        self.q.put(text)

_tts = _TTSWorker() if SPEECH_AVAILABLE else None

def speak(text: str) -> None:
    if SPEECH_AVAILABLE and _tts:
        _tts.say(text)

def recognize_speech(timeout: float = 5.0) -> tuple[str | None, float]:
    """
    Rozpoznawanie mowy – zwraca (tekst, 0.9) lub (None, 0.0).
    Nie rzuca wyjątków w razie timeout/nieudanej rozpoznania.
    """
    if not SPEECH_AVAILABLE:
        return None, 0.0

    recognizer = recognize_speech.recognizer
    mic        = recognize_speech.mic

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=timeout)
        txt = recognizer.recognize_google(audio, language="pl-PL")
        return txt, 0.9
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return None, 0.0
    except Exception as exc:
        print("ASR error:", exc)
        return None, 0.0

if SPEECH_AVAILABLE:
    recognize_speech.recognizer = sr.Recognizer()
    recognize_speech.mic        = sr.Microphone()
