"""Entrypoint: FastAPI-app met NiceGUI erbovenop.

Start met:  uvicorn needful.main:app --reload
"""

from fastapi import FastAPI
from nicegui import ui

from needful.api.routes import router as api_router
from needful.logging_setup import setup_logging
from needful.ui.screens import advies, q1, q2, q3, q4, start  # noqa: F401  (registreert de schermen)

setup_logging()

app = FastAPI(title="needful.", version="0.1.0")
app.include_router(api_router, prefix="/api")

ui.run_with(app, title="needful.", storage_secret="dev-only-change-me")
