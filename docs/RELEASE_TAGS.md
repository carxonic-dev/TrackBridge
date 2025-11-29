# RELEASE_TAGS.md

## TrackBridge – Release-Tag-Konzept (Öffentliche Dokumentation)

Dieses Dokument erklärt, wie Versionen für TrackBridge vergeben werden. Es dient der Orientierung für Nutzer, Mitwirkende und zukünftige Entwickler. Die Regeln sind bewusst einfach gehalten und folgen einer klaren Logik, damit Versionen nachvollziehbar, konsistent und transparent bleiben.

---

## 🎯 Versionsschema

Wir verwenden das Schema **vMAJOR.MINOR.PATCH**.

Beispiele:

- `v1.0.0`
- `v1.0.1`
- `v1.1.0`
- `v2.0.0`

---

## 🟥 MAJOR – Grundlegende Änderungen

Eine neue **MAJOR-Version** wird vergeben, wenn:

- ein bestehender CLI-Befehl geändert wird (Breaking Change)
- die Struktur der `config.json` inkompatibel wird
- bestehende Nutzer ihre Konfiguration anpassen müssen

Beispiel:

- Änderung an der Config-Struktur → `v2.0.0`

---

## 🟧 MINOR – Neue Funktionen

Eine **MINOR-Version** wird vergeben, wenn:

- neue Funktionen hinzugefügt werden
- bestehende Funktionen erweitert werden
- alles weiterhin rückwärtskompatibel bleibt

Beispiele:

- neue CLI-Option → `v1.1.0`
- zusätzliche Exportformate → `v1.2.0`

---

## 🟩 PATCH – Bugfixes & kleine Verbesserungen

Eine **PATCH-Version** wird vergeben, wenn:

- Fehler behoben werden
- kleinere Optimierungen stattfinden
- Dokumentation korrigiert wird

Beispiele:

- Fix für Metadaten-Problem → `v1.0.1`
- kleinere Text-/Linkkorrekturen → `v1.0.2`

---

## 🔄 Entscheidungen treffen – Kurzleitfaden

**Ist die Änderung inkompatibel?**
→ MAJOR erhöhen

**Ist die Änderung ein neues Feature?**
→ MINOR erhöhen

**Wurde nur etwas repariert oder verbessert?**
→ PATCH erhöhen

---

## 🏷 Empfehlung für Tag-Namen

Tags sollen exakt so aussehen:

```text
v1.0.0
v1.0.1
v1.1.0
v2.0.0
```

Keine Sonderformen, keine Zusätze.

Optional für Vorab-Versionen:

```text
v1.2.0-rc.1
```

---

## 📦 Wie ein Release erzeugt wird

1. Änderungen testen
2. Doku aktualisieren (falls nötig)
3. Commit auf `main`
4. Tag setzen:

```bash
git tag v1.0.0
git push origin v1.0.0
```

5. GitHub → „New Release“ → Tag auswählen → Changelog eintragen

---

## 📝 Beispiel-Changelog für GitHub

```text
### 🚀 TrackBridge v1.1.0
- Neues Feature: Unterstützung für zusätzliche Audio-Metadaten
- CLI erweitert: ``run-downloads`` kann jetzt ohne Limit genutzt werden
- Verbesserte Fehlerbehandlung
```

---

## Ziel dieses Dokuments

- Versionen konsistent halten
- Veränderungen transparent machen
- Nutzern und Mitwirkenden Orientierung geben
- Grundlage für künftige Automatisierung schaffen

*_Ende Release-Tag-Konzept_*
