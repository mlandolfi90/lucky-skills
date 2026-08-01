"""Atomic adoption reference adapter."""

from .planner import build_plan
from .transaction import apply_plan

__all__ = ["apply_plan", "build_plan"]
