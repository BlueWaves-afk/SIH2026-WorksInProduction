"""Writes shadow predictions without feeding the decision path."""


def log_prediction(store: list[dict], prediction: dict) -> None:
    store.append({"prediction": prediction, "acting": False})
