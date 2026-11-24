"""Optional offline Vosk microphone adapter. Requires a local model directory."""
import json
import os
from pathlib import Path


class VoiceUnavailable(RuntimeError):
    pass


def listen_once() -> str:
    model_path = os.environ.get("NOVA_VOSK_MODEL")
    if not model_path or not Path(model_path).is_dir():
        raise VoiceUnavailable("Set NOVA_VOSK_MODEL to a downloaded Vosk model directory first.")
    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise VoiceUnavailable('Install voice extras with: pip install -e ".[voice]"') from exc
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    print("Listening once (offline). Speak now...")
    audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    recognizer.AcceptWaveform(audio.tobytes())
    return json.loads(recognizer.FinalResult()).get("text", "").strip()
