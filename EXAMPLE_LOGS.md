# 📝 EJEMPLOS DE LOGS: Sistema de Recuperación de Errores

Esta guía muestra ejemplos reales de cómo se ven los logs cuando el sistema funciona correctamente.

---

## 1️⃣ INICIO DE UNA INSTANCIA

### ✅ Cuando funciona correctamente:

**Archivo:** `trajectories/user/config__gpt-4o___instance_1/instance_1/instance_1.debug.log`

```
2025-10-28 12:00:00.123 [DEBUG] [swea-run] Starting environment
2025-10-28 12:00:01.456 [DEBUG] [swea-run] Environment started
2025-10-28 12:00:01.457 [DEBUG] [swea-run] Running agent
2025-10-28 12:00:01.458 [DEBUG] [swea-run] Error detector reset for new instance  ← ✅ ESTO ES CRÍTICO
2025-10-28 12:00:02.789 [INFO] [swea-lm] Cost: $0.02, Calls: 1
...
```

### ❌ Cuando NO funciona:

```
2025-10-28 12:00:00.123 [DEBUG] [swea-run] Starting environment
2025-10-28 12:00:01.456 [DEBUG] [swea-run] Environment started
2025-10-28 12:00:01.457 [DEBUG] [swea-run] Running agent
                                                                ← ❌ FALTA el "Error detector reset"
2025-10-28 12:00:02.789 [INFO] [swea-lm] Cost: $0.02, Calls: 1
```

---

## 2️⃣ DETECCIÓN DE UN ERROR

### ✅ Cuando se detecta correctamente:

**Archivo:** `instance_1.debug.log`

```
2025-10-28 12:01:15.234 [INFO] [swea-agent] Executing action: str_replace
2025-10-28 12:01:15.567 [DEBUG] [pattern_detector] Error added: syntax at main.py:42  ← ✅ ERROR DETECTADO
2025-10-28 12:01:15.568 [INFO] [swea-agent] Observation received
```

**Detalles completos del error detectado:**

```python
{
    'timestamp': 0,
    'error_type': 'syntax',              # Tipo clasificado automáticamente
    'message': 'SyntaxError: invalid syntax',
    'file': 'main.py',                   # Archivo extraído del traceback
    'line': 42,                          # Línea extraída del traceback
    'action': 'str_replace',             # Acción que causó el error
    'code_snippet': 'def foo(',          # Snippet del código problemático
    'traceback': '...'                   # Traceback completo
}
```

### ❌ Cuando NO se detecta:

```
2025-10-28 12:01:15.234 [INFO] [swea-agent] Executing action: str_replace
                                                                ← ❌ FALTA "Error added"
2025-10-28 12:01:15.568 [INFO] [swea-agent] Observation received
```

---

## 3️⃣ DETECCIÓN DE LOOP

### ✅ Cuando se detecta un loop:

**Archivo:** `instance_1.debug.log`

```
2025-10-28 12:02:30.111 [DEBUG] [pattern_detector] Error added: syntax at script.py:45
2025-10-28 12:03:45.222 [DEBUG] [pattern_detector] Error added: syntax at script.py:45
2025-10-28 12:05:00.333 [DEBUG] [pattern_detector] Error added: syntax at script.py:45
2025-10-28 12:06:15.444 [DEBUG] [pattern_detector] Error added: syntax at script.py:45
2025-10-28 12:07:30.555 [DEBUG] [pattern_detector] Error added: syntax at script.py:47
2025-10-28 12:07:30.556 [WARNING] [pattern_detector] Loop detectado: Repeatedly failing at line 45  ← ✅ LOOP DETECTADO
2025-10-28 12:07:30.557 [INFO] [pattern_detector] Suggesting alternative approach
```

**Tipos de loops que se detectan:**

1. **Mismo error repetido:**
```
[WARNING] Loop detectado: Repetitive syntax errors
```

2. **Misma línea:**
```
[WARNING] Loop detectado: Repeatedly failing at line 45
```

3. **Alternancia entre dos errores:**
```
[WARNING] Loop detectado: Alternating between {'syntax', 'indentation'}
```

4. **Múltiples errores en el mismo archivo:**
```
[WARNING] Loop detectado: Multiple errors in same file: main.py
```

---

## 4️⃣ SUGERENCIAS DE RECUPERACIÓN

### ✅ En la observación (trajectory):

**Archivo:** `instance_1.traj` (JSON)

```json
{
  "role": "user",
  "message_type": "observation",
  "content": "Your edits have been applied, but the linter has found syntax errors.\n\n<ERRORS>\n- line 42 col 8: SyntaxError: invalid syntax\n</ERRORS>\n\nPlease review the changes and make sure they are correct.\n\n======================================================================\n⚠️  SYNTAX ERROR - Try these steps:\n1. Check for missing/extra parentheses, brackets, or quotes\n2. Verify the line before/after your edit for completion\n3. Review the original code structure before editing\n4. Look for unclosed strings, lists, or function calls\n\n🚨 WARNING: This is your 3th syntax error.\nConsider:\n- Taking a completely different approach to solve this issue\n- Re-reading the file to understand the context better\n- Starting with a simpler change first\n- Searching for similar code patterns in the repository\n======================================================================"
}
```

### Tipos de sugerencias según el error:

#### **SYNTAX ERROR:**
```
⚠️  SYNTAX ERROR - Try these steps:
1. Check for missing/extra parentheses, brackets, or quotes
2. Verify the line before/after your edit for completion
3. Review the original code structure before editing
4. Look for unclosed strings, lists, or function calls
```

#### **INDENTATION ERROR:**
```
⚠️  INDENTATION ERROR - Common fixes:
1. Check that all lines use consistent spacing (4 spaces or 1 tab)
2. Verify the indentation matches the surrounding code
3. Use the 'goto' command to see context around your edit
4. Compare with neighboring functions for proper indentation level
```

#### **UNDEFINED NAME:**
```
⚠️  UNDEFINED NAME - Likely causes:
1. Missing import statement at the top of the file
2. Variable defined in a different scope
3. Typo in variable/function name
4. Variable defined after it's used
→ Use 'search_file' to find where this name is defined
→ Use 'search_dir' to search across the entire codebase
```

#### **IMPORT ERROR:**
```
⚠️  IMPORT ERROR - Solutions:
1. Check if the module is available in this environment
2. Verify the import path is correct (relative vs absolute)
3. Look for similar imports elsewhere in the codebase
4. Check if the module needs to be installed
→ Use 'search_dir' to find existing import patterns
```

---

## 5️⃣ RUN BATCH (MÚLTIPLES INSTANCIAS)

### ✅ Cuando funciona correctamente:

**Archivo:** `run_batch.log`

```
2025-10-28 12:00:00.000 [INFO] [swea-run] Starting run. Find output files at trajectories/
2025-10-28 12:00:01.000 [DEBUG] [swea-run] Error detector reset for instance instance_1  ← ✅ Reset instancia 1
2025-10-28 12:00:01.100 [INFO] [swea-run] Running on instance instance_1
2025-10-28 12:05:30.000 [INFO] [swea-run] ✅ instance_1 completed
2025-10-28 12:05:31.000 [DEBUG] [swea-run] Error detector reset for instance instance_2  ← ✅ Reset instancia 2
2025-10-28 12:05:31.100 [INFO] [swea-run] Running on instance instance_2
2025-10-28 12:10:45.000 [INFO] [swea-run] ✅ instance_2 completed
2025-10-28 12:10:46.000 [DEBUG] [swea-run] Error detector reset for instance instance_3  ← ✅ Reset instancia 3
2025-10-28 12:10:46.100 [INFO] [swea-run] Running on instance instance_3
2025-10-28 12:15:20.000 [INFO] [swea-run] ✅ instance_3 completed
```

**Nota importante:** Cada instancia debe tener su propio "Error detector reset". Si falta alguno, habrá contaminación.

### ❌ Cuando hay contaminación:

```
2025-10-28 12:00:00.000 [INFO] [swea-run] Starting run
2025-10-28 12:00:01.000 [DEBUG] [swea-run] Error detector reset for instance instance_1  ← ✅ Solo instancia 1
2025-10-28 12:05:30.000 [INFO] [swea-run] ✅ instance_1 completed
2025-10-28 12:05:31.100 [INFO] [swea-run] Running on instance instance_2               ← ❌ Sin reset
2025-10-28 12:10:45.000 [INFO] [swea-run] ✅ instance_2 completed
2025-10-28 12:10:46.100 [INFO] [swea-run] Running on instance instance_3               ← ❌ Sin reset
```

**Consecuencia:** Los errores de instance_1 se mantienen en instance_2 y instance_3.

---

## 6️⃣ ESTADÍSTICAS COMPLETAS

### Al final de una ejecución con errores:

**Si quisieras imprimir las estadísticas (no se imprimen por defecto):**

```python
{
    'total_errors': 12,
    'by_type': {
        'syntax': 5,
        'indentation': 4,
        'undefined': 2,
        'import': 1
    },
    'recent_errors': 5,
    'recovery_attempts': 8,
    'most_common_error': 'syntax',
    'unique_files_affected': 3,
    'avg_errors_per_file': 4.0,
    'error_rate': 1.0,
    'consecutive_same_type': 2
}
```

---

## 7️⃣ ERRORES COMUNES Y SUS LOGS

### Error 1: Falta importación

**Log:**
```
2025-10-28 12:00:05.000 [ERROR] [swea-run] ImportError: cannot import name 'reset_global_error_detector' from 'sweagent.agent.history_processors'
Traceback (most recent call last):
  File "sweagent/run/run_single.py", line 40, in <module>
    from sweagent.agent.history_processors import reset_global_error_detector
ImportError: cannot import name 'reset_global_error_detector'
```

**Causa:** El archivo `history_processors.py` no tiene la función `reset_global_error_detector()`.

---

### Error 2: Atributo no existe

**Log:**
```
2025-10-28 12:01:00.000 [ERROR] [swea-agent] AttributeError: 'LastNObservations' object has no attribute 'error_detector'
Traceback (most recent call last):
  File "sweagent/agent/history_processors.py", line 200, in __call__
    self.error_detector.add_error(error_info)
AttributeError: 'LastNObservations' object has no attribute 'error_detector'
```

**Causa:** La inicialización del `error_detector` en `LastNObservations.__init__` falló o no se ejecutó.

---

### Error 3: Detector no se resetea

**Síntoma en logs:**

```
# Instancia 1
[DEBUG] Error added: syntax at file1.py:10
[DEBUG] Error added: indentation at file1.py:15

# Instancia 2 (DEBERÍA EMPEZAR LIMPIO)
[DEBUG] Error added: syntax at file2.py:5
[WARNING] Loop detectado: Repetitive syntax errors  ← ❌ FALSO POSITIVO (incluye errores de instancia 1)
```

**Causa:** `reset_global_error_detector()` no se llamó entre instancias.

---

## 8️⃣ VERIFICACIÓN RÁPIDA CON GREP

### Comandos útiles:

```bash
# 1. ¿Se resetea el detector?
grep -r "Error detector reset" trajectories/ | wc -l
# Debe ser > 0

# 2. ¿Se detectan errores?
grep -r "Error added:" trajectories/ | wc -l
# Debe ser > 0 si el agente cometió errores

# 3. ¿Qué tipos de errores?
grep -r "Error added:" trajectories/ | sed 's/.*Error added: \([^ ]*\).*/\1/' | sort | uniq -c
# Ejemplo de salida:
#   15 syntax
#    8 indentation
#    5 undefined

# 4. ¿Se detectaron loops?
grep -r "Loop detectado" trajectories/ | wc -l
# Puede ser 0 (normal si no hay loops)

# 5. ¿Hay sugerencias?
grep -r "⚠️" trajectories/ | wc -l
# Debe ser > 0 si hubo loops

# 6. ¿Hay errores de importación?
grep -rE "ImportError.*pattern_detector|ModuleNotFoundError" trajectories/ | wc -l
# Debe ser 0
```

---

## 9️⃣ TIMELINE COMPLETO DE UNA EJECUCIÓN EXITOSA

**Secuencia de eventos esperada:**

```
T+0s    [INFO] Starting environment
T+1s    [DEBUG] Environment started
T+1s    [DEBUG] Running agent
T+1s    [DEBUG] Error detector reset for new instance          ← ✅ 1. RESET
T+2s    [INFO] Cost: $0.02, Calls: 1
T+10s   [INFO] Executing action: str_replace
T+10s   [DEBUG] Linting file after edit
T+10s   [DEBUG] Error added: syntax at main.py:42              ← ✅ 2. ERROR DETECTADO
T+10s   [INFO] Observation with lint errors sent to agent
T+15s   [INFO] Cost: $0.04, Calls: 2
T+20s   [INFO] Executing action: str_replace
T+20s   [DEBUG] Error added: syntax at main.py:42              ← ✅ 3. SEGUNDO ERROR
T+25s   [INFO] Executing action: str_replace
T+25s   [DEBUG] Error added: syntax at main.py:45              ← ✅ 4. TERCER ERROR
T+30s   [INFO] Executing action: str_replace
T+30s   [DEBUG] Error added: syntax at main.py:45              ← ✅ 5. CUARTO ERROR
T+35s   [INFO] Executing action: str_replace
T+35s   [DEBUG] Error added: syntax at main.py:45              ← ✅ 6. QUINTO ERROR
T+35s   [WARNING] Loop detectado: Repeatedly failing at line 45 ← ✅ 7. LOOP DETECTADO
T+35s   [INFO] Recovery suggestion added to observation        ← ✅ 8. SUGERENCIA GENERADA
T+40s   [INFO] Cost: $0.10, Calls: 6
T+50s   [INFO] Executing action: search_file                   ← ✅ 9. CAMBIO DE ESTRATEGIA
T+55s   [INFO] Executing action: str_replace                   ← ✅ 10. NUEVO INTENTO
T+55s   [INFO] No lint errors found                            ← ✅ 11. ÉXITO
T+60s   [INFO] Instance completed successfully
```

---

## 🎯 CONCLUSIÓN

Si ves estos elementos en tus logs, **el sistema está funcionando perfectamente**:

1. ✅ `Error detector reset for new instance` al inicio de cada instancia
2. ✅ `Error added: <tipo> at <archivo>:<línea>` cuando el agente comete errores
3. ✅ `Loop detectado: <razón>` cuando hay patrones repetitivos
4. ✅ Sugerencias con `⚠️` en las observaciones después de detectar loops
5. ✅ **SIN** errores de ImportError o ModuleNotFoundError

**¡El sistema de recuperación de errores está operativo! 🚀**
