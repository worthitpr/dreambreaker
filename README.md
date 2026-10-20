# DREAMBREAKER

**ES** · Una skill de IA que intenta destruir tu idea antes de que pierdas tiempo o dinero en ella, y que te dice a qué fracaso o éxito histórico se parece.
**EN** · An AI skill that tries to destroy your idea before you waste time or money on it, and tells you which historical failure or success it resembles.

Creado por / Created by: **Kritsia Quiñones — XXSELENEPRXX**

---

## Español

### Qué la hace diferente
- **Eslabón débil:** una sola debilidad crítica con evidencia basta para matar una idea. El promedio no la esconde.
- **Cementerio de ideas:** compara tu idea con 20 casos reales (Juicero, Theranos, Quibi, Airbnb, Uber, SpaceX…) y te dice por qué murieron o qué los salvó.
- **Apelación por precedente:** si un éxito real sobrevivió a tus mismos riesgos críticos, no mata tu idea. Te dice qué tienes que demostrar.
- **Honesta:** sin evidencia no hay veredicto de muerte, y nunca dice "nadie en el mundo tiene esto".

### Cómo usarla
1. Copia la carpeta `dreambreaker` en tus skills de Claude (o pega `SKILL.md` en tu asistente de IA).
2. Pide: *"Destruye esta idea: …"*.
3. Opcional, sin IA: `python3 scripts/dreambreaker.py scripts/example_input.json`

### Pruebas
- `python3 scripts/test_dreambreaker.py`: 35 pruebas.
- `python3 scripts/backtest.py`: los 20 casos históricos.

**Límite honesto:** DREAMBREAKER es una prueba de estrés pesimista, no un oráculo. En tres rondas de predicciones selladas antes de conocer el resultado detectó el 75% de los fracasos reales, pero el 60% de sus alarmas fueron falsas, y como pronóstico acertó menos que suponer que todo sobrevive. Úsala para encontrar las debilidades de tu idea, no para saber si triunfará. Todo está en `VALIDATION.md`, incluidos los fallos.

---

## English

### What makes it different
- **Weakest link:** one evidenced critical weakness is enough to kill an idea. Averages do not hide it.
- **Idea graveyard:** compares your idea with 20 real cases (Juicero, Theranos, Quibi, Airbnb, Uber, SpaceX…) and tells you why they died or what saved them.
- **Precedent appeal:** if a real success survived your same critical risks, the idea is put on hold instead of killed, and you are told what you must prove.
- **Honest:** no kill without evidence, and it never claims "nobody in the world has this".

### How to use
1. Copy the `dreambreaker` folder into your Claude skills (or paste `SKILL.md` into your AI assistant).
2. Ask: *"Destroy this idea: …"*.
3. Optional, without AI: `python3 scripts/dreambreaker.py scripts/example_input.json`

### Tests
- `python3 scripts/test_dreambreaker.py`: 35 tests.
- `python3 scripts/backtest.py`: the 20 historical cases.

**Honest limit:** DREAMBREAKER is a pessimistic stress test, not a forecaster. In three rounds of predictions sealed before the outcomes were known, it flagged 75% of real failures, but 60% of its alarms were false, and as a forecast it did worse than assuming everything survives. Use it to find your idea's weaknesses, not to predict success. Everything, including the failures, is in `VALIDATION.md`.

---

Licencia / License: **Apache 2.0** — ver / see `LICENSE` y / and `NOTICE`.

Copyright 2026 Kritsia Quiñones (XXSELENEPRXX)
