"""Desktop integration boundary.

This module intentionally exposes no arbitrary shell or process-launch primitive.
Future OS skills must be added as typed actions and pass through ActionExecutor.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DesktopCapability:
    name: str
    enabled: bool = False


def available_capabilities() -> tuple[DesktopCapability, ...]:
    return (
        DesktopCapability("window_management"),
        DesktopCapability("application_launch"),
        DesktopCapability("browser_automation"),
        DesktopCapability("notifications"),
    )
