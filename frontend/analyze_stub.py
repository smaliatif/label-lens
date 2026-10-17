"""Finto analyze() per fare testing"""
import json, time
from pathlib import Path

def analyze(image, profile: dict) -> dict:
    time.sleep(1.5)  # simula la latenza del modello
    return json.loads((Path(__file__).parent / "samples" / "sample_result.json").read_text())
