import argparse
from nova.app import NovaApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Nova local-first personal assistant")
    parser.add_argument("--voice", action="store_true", help="capture one offline voice command per turn")
    args = parser.parse_args()
    app = NovaApp()
    if not args.voice:
        app.run()
        return
    from nova.voice import VoiceUnavailable, listen_once
    print("Nova v1.0 voice mode | say 'exit' to quit")
    while app.running:
        try:
            text = listen_once()
            if not text:
                print("Nova > I didn't catch that. Try again.")
                continue
            print(f"You > {text}")
            print(f"Nova > {app.handle(text).message}")
        except (VoiceUnavailable, KeyboardInterrupt) as exc:
            print(f"Nova > {exc or 'Voice mode stopped.'}")
            break


if __name__ == "__main__":
    main()
