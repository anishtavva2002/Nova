import argparse
from nova.app import NovaApp
from nova.orchestrator import NovaEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Nova local-first personal assistant")
    parser.add_argument("--voice", action="store_true", help="capture one offline voice command per turn")
    parser.add_argument("--unified", action="store_true", help="enable personal, environment and developer routing")
    args = parser.parse_args()
    app = NovaApp()
    handler = NovaEngine(personal_app=app).handle if args.unified else app.handle
    mode = "unified" if args.unified else "personal"
    if not args.voice:
        print(f"Nova v1.1 | {mode} mode | Local-first | LLM-free")
        print("Type 'help' for commands. Type 'exit' to quit.")
        while app.running:
            try:
                text = input("\nYou > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nNova > Goodbye.")
                break
            if text:
                print(f"Nova > {handler(text)}")
        return
    from nova.voice import VoiceUnavailable, listen_once
    print(f"Nova v1.1 voice mode | {mode} routing | say 'exit' to quit")
    while app.running:
        try:
            text = listen_once()
            if not text:
                print("Nova > I didn't catch that. Try again.")
                continue
            print(f"You > {text}")
            print(f"Nova > {handler(text)}")
        except (VoiceUnavailable, KeyboardInterrupt) as exc:
            print(f"Nova > {exc or 'Voice mode stopped.'}")
            break


if __name__ == "__main__":
    main()
