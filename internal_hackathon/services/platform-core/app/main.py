"""Retired runtime entrypoint.

``services/backend`` is the only deployable FastAPI application. This package
still carries type/reference material used by the design docs, but starting it
as a second service would create split-brain API, schema, and auth behaviour.
"""


def create_app():
    raise RuntimeError("platform-core is a reference package; run services/backend/app/main.py")


app = None
