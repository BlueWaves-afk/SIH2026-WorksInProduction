"""DTMF handler."""


def parse_keypress(key: str) -> str:
    return {"1": "CONFIRM_SAFE", "2": "REQUEST_OFFICER", "9": "STOP"}.get(key, "UNRECOGNISED")
