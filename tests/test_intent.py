from nova.intent import IntentParser


def test_common_commands_and_variants():
    parser = IntentParser()
    assert parser.parse("help").name == "help"
    assert parser.parse("Tell me the time").name == "time"
    assert parser.parse("what is today's date").name == "date"
    assert parser.parse("remember build Nova").entities["content"] == "build Nova"
    assert parser.parse("remind me to test the app").name == "task.add"
    assert parser.parse("finish task 3").entities["id"] == "3"
    assert parser.parse("calculate (2 + 3) * 4").name == "calculate"
    assert parser.parse("open https://example.com").name == "open.url"


def test_aliases_are_exact_and_allowlisted():
    parser = IntentParser({"launch nova": "help", "danger": "os.execute"})
    assert parser.parse("launch nova").name == "help"
    assert parser.parse("danger").name == "unknown"
    assert parser.parse("launch nova now").name == "unknown"
