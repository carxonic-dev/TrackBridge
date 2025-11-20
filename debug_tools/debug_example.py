"""
Kleine Debug-Demo für dieses Projekt.

- ipdb:  inline-Debugger im Terminal
- pudb:  Vollbild-TUI-Debugger im Terminal
"""

from __future__ import annotations

from typing import Any


def demo_function(a: int, b: int) -> int:
    """
    Einfache Testfunktion, an der wir Debugger ausprobieren.
    """
    result = a + b
    return result


def run_with_ipdb() -> None:
    """
    Startet die Demo mit ipdb.
    """
    import ipdb  # type: ignore[import]
    ipdb.set_trace()  # Breakpoint

    x = 40
    y = 2
    res = demo_function(x, y)
    print(f"[ipdb-demo] Ergebnis: {res}")


def run_with_pudb() -> None:
    """
    Startet die Demo mit pudb als Vollbild-TUI.
    """
    import pudb  # type: ignore[import]
    pudb.set_trace()  # Breakpoint

    x = 10
    y = 5
    res = demo_function(x, y)
    print(f"[pudb-demo] Ergebnis: {res}")


if __name__ == "__main__":
    # Wähle hier, welches Demo-Szenario du testen willst:
    mode: str = "ipdb"  # "ipdb" oder "pudb"

    if mode == "ipdb":
        run_with_ipdb()
    elif mode == "pudb":
        run_with_pudb()
    else:
        raise ValueError(f"Unbekannter Modus: {mode}")
