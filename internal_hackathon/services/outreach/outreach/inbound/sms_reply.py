"""Short-code keyword parser."""


def parse_sms(text: str) -> str:
    keyword = text.strip().upper()
    return {"1": "ACK", "HELP": "REQUEST_HELP", "STOP": "WITHDRAW_CONTACT"}.get(keyword, "UNRECOGNISED")
