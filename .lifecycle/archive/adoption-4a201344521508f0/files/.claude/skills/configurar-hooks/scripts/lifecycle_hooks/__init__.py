"""Runtime portable y autónomo para hooks lifecycle asesores."""

from .contracts import COMMON_EVENTS, HookEvent
from .dispatcher import DispatchResult, dispatch_event, verify_hook_receipt
from .normalizer import host_error_response, host_response, normalize_host_event

__all__ = [
    "COMMON_EVENTS",
    "DispatchResult",
    "HookEvent",
    "dispatch_event",
    "host_error_response",
    "host_response",
    "normalize_host_event",
    "verify_hook_receipt",
]
