# Debug-Cheat-Sheet · spotify_2_yt-dlp

Dieses Projekt nutzt zwei Debugger:

- **ipdb** → einfacher, schneller CLI-Debugger
- **pudb** → Vollbild-Terminal-Debugger (TUI)

Beide sind in der `.venv` installiert und können direkt verwendet werden.


---

## 1. ipdb (schneller Inline-Debugger)

### 1.1 Breakpoint setzen

In eine beliebige Python-Datei einfügen:

```python
import ipdb; ipdb.set_trace()
```

Sobald der Code diese Zeile erreicht, stoppt die Ausführung und du landest im `ipdb>`-Prompt.

Beispiel in `debug_tools/debug_example.py`:

```python
def run_with_ipdb() -> None:
    import ipdb  # type: ignore[import]
    ipdb.set_trace()

    x = 40
    y = 2
    res = demo_function(x, y)
    print(f"[ipdb-demo] Ergebnis: {res}")
```


### 1.2 Wichtige ipdb-Befehle

| Befehl       | Wirkung                                                                 |
|--------------|-------------------------------------------------------------------------|
| `n`          | *next* – aktuelle Zeile ausführen, zur nächsten springen                |
| `s`          | *step* – in aufgerufene Funktionen hineinspringen                       |
| `c`          | *continue* – Programm bis zum nächsten Breakpoint weiterlaufen lassen   |
| `q`          | *quit* – Debugger beenden, Programm abbrechen                           |
| `l`          | *list* – Code rund um die aktuelle Zeile anzeigen                       |
| `w`          | *where* – Stacktrace anzeigen                                           |
| `p x`        | *print* – Wert der Variable `x` anzeigen                                |
| `pp x`       | *pretty print* – Wert von `x` formatiert anzeigen                       |
| `h`          | *help* – Hilfe anzeigen                                                 |

Typische Mini-Session:

```text
ipdb> n        # nächste Zeile
ipdb> p x      # Wert von x anzeigen
ipdb> c        # weiterlaufen lassen
```

---

## 2. pudb (Vollbild-Terminal-Debugger / TUI)

**TUI = Text User Interface**  
→ Vollbildoberfläche im Terminal mit Code, Variablen, Stack, Breakpoints, Watches.


### 2.1 Breakpoint setzen

In Python:

```python
import pudb; pudb.set_trace()
```

Beispiel in `debug_tools/debug_example.py`:

```python
def run_with_pudb() -> None:
    import pudb  # type: ignore[import]
    pudb.set_trace()

    x = 10
    y = 5
    res = demo_function(x, y)
    print(f"[pudb-demo] Ergebnis: {res}")
```


### 2.2 Start aus dem Terminal

```powershell
# Variante 1: über das Modul
python -m debug_tools.debug_example

# Variante 2: beliebiges Skript
python -m pudb main.py
```


### 2.3 Navigation in pudb (Basis)

- **F5** – Continue (weiterlaufen)
- **F10** – Next (nächste Zeile, nicht in Funktionen hinein)
- **F11** – Step (in Funktionen hinein)
- **Shift+F11** – Step out (aus aktueller Funktion raus)
- **b** – Breakpoint setzen/entfernen
- **q** – pudb beenden (Programm wird beendet)
- **n / p / ↑ / ↓** – in Listen und Menüs navigieren

Außerdem:

- Linkes Panel → Code mit aktuellem Zeilenmarker  
- Rechts oben → Variablen (locals / globals)  
- Rechts unten → Stack, Watch-Ausdrücke usw.


---

## 3. Typische Debug-Workflows in diesem Projekt

### 3.1 Quick-Debug mit ipdb

Use-Case: „Ich will kurz sehen, was in einer Funktion passiert.“

1. In die Ziel-Funktion einfügen:

   ```python
   import ipdb; ipdb.set_trace()
   ```

2. Skript ausführen:

   ```powershell
   python .\main.py
   ```

3. Im `ipdb>`-Prompt:

   ```text
   ipdb> n        # Zeile ausführen
   ipdb> p token  # Variable anschauen
   ipdb> c        # weiterlaufen lassen
   ```

4. Bei Bedarf `q` für Abbruch.


### 3.2 Ausführlich debuggen mit pudb

Use-Case: „Ich will in Ruhe durch den Code laufen und Variablen im Blick haben.“

1. In die Datei einfügen:

   ```python
   import pudb; pudb.set_trace()
   ```

2. Skript starten:

   ```powershell
   python -m debug_tools.debug_example
   # oder
   python -m pudb main.py
   ```

3. In der pudb-Oberfläche mit F-Tasten navigieren (F10/F11/F5).


---

## 4. Hinweise zu Installation und venv

Debug-Pakete **immer in der Projekt-venv** installieren:

```powershell
.\.venv\Scripts\Activate.ps1
pip install ipdb pudb
pip freeze > requirements.txt
```

So bleiben Projekte sauber voneinander getrennt und alles ist reproduzierbar.


---

## 5. Minimal-Referenz (für Später-Ich)

- `ipdb` → schnell, textbasiert, kein Vollbild
- `pudb` → Vollbild-TUI, komfortabel für längere Debug-Sessions
- Beide laufen im Terminal, keine extra GUI nötig
- Debug-Punkte sind immer `ipdb.set_trace()` oder `pudb.set_trace()`
