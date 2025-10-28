# 🔍 GUÍA DE VERIFICACIÓN: Sistema de Recuperación de Errores

Esta guía te ayudará a verificar que el sistema de recuperación de errores está funcionando correctamente.

---

## 📋 CHECKLIST RÁPIDO

Después de ejecutar SWE-agent, verifica:

- [ ] ✅ El log muestra "Error detector reset"
- [ ] ✅ Se detectan errores cuando el agente los comete
- [ ] ✅ Aparecen sugerencias después de errores repetitivos
- [ ] ✅ No hay mensajes de ImportError relacionados con pattern_detector

---

## 1️⃣ COMANDOS PARA VERIFICAR LOGS

### A) Verificar que el detector se resetea

```bash
# Para run_single
grep -r "Error detector reset for new instance" trajectories/

# Para run_batch
grep -r "Error detector reset for instance" trajectories/
```

**Salida esperada:**
```
trajectories/user/config__model___instance_1/instance_1/instance_1.debug.log:Error detector reset for new instance
```

**Si NO aparece:** ❌ Problema crítico - el detector no se está reseteando

---

### B) Verificar detección de errores

```bash
# Buscar en todos los logs de debug
grep -r "Error added:" trajectories/ | head -20
```

**Salida esperada:**
```
Error added: syntax at script.py:45
Error added: indentation at main.py:12
Error added: undefined at test.py:78
```

**Si NO aparece:** ⚠️ El detector no está capturando errores (puede ser que el agente no haya cometido errores)

---

### C) Verificar detección de loops

```bash
# Buscar warnings de loops
grep -r "Loop detectado" trajectories/ | head -10

# O en inglés
grep -r "Loop detected" trajectories/ | head -10
```

**Salida esperada:**
```
WARNING: Loop detectado: Repetitive syntax errors
WARNING: Loop detectado: Repeatedly failing at line 45
```

**Si NO aparece:** ℹ️ Normal si el agente no entró en loops

---

### D) Verificar sugerencias de recuperación

```bash
# Buscar sugerencias en trajectories
grep -r "SYNTAX ERROR\|INDENTATION ERROR\|UNDEFINED NAME" trajectories/

# Ver el contenido de una trajectory específica
cat trajectories/<path>/<instance_id>/<instance_id>.traj | jq '.history[] | select(.content | contains("⚠️"))'
```

**Salida esperada:**
```json
{
  "role": "user",
  "content": "...\n======================================================================\n⚠️  SYNTAX ERROR - Try these steps:\n1. Check for missing/extra parentheses...\n======================================================================"
}
```

---

## 2️⃣ VERIFICACIÓN MANUAL EN ARCHIVOS

### Archivo principal: `<instance_id>.debug.log`

**Ubicación:**
```
trajectories/<user>/<config>__<model>___<instance_id>/<instance_id>/<instance_id>.debug.log
```

**Buscar estas líneas:**

1. **Al inicio del archivo:**
```
Error detector reset for new instance
```

2. **Cuando ocurre un error:**
```
Error added: <tipo> at <archivo>:<línea>
```

3. **Cuando se detecta un loop:**
```
Loop detectado: <razón>
```

---

### Archivo de trajectory: `<instance_id>.traj`

**Ubicación:**
```
trajectories/<user>/<config>__<model>___<instance_id>/<instance_id>/<instance_id>.traj
```

**Buscar en las observaciones (después de acciones con errores):**

```bash
cat <instance_id>.traj | python3 -m json.tool | grep -A 20 "⚠️"
```

Deberías ver bloques como:
```
======================================================================
⚠️  SYNTAX ERROR - Try these steps:
1. Check for missing/extra parentheses, brackets, or quotes
2. Verify the line before/after your edit for completion
...
🚨 WARNING: This is your 3th syntax error.
======================================================================
```

---

## 3️⃣ EJEMPLO DE EJECUCIÓN EXITOSA

### Comando de prueba:

```bash
sweagent run \
    --config config/default.yaml \
    --agent.model.name "azure/gpt-4o" \
    --env.repo.path /path/to/test-repo \
    --problem_statement.text "Fix the syntax error in main.py"
```

### Logs esperados:

**En consola:**
```
🏃 Starting environment
🏃 Running agent
🏃 [DEBUG] Error detector reset for new instance
🤖 [INFO] Cost: $0.05, Calls: 1
...
```

**En `<instance>.debug.log`:**
```
2025-10-28 12:00:00 [DEBUG] Error detector reset for new instance
2025-10-28 12:00:15 [DEBUG] Error added: syntax at main.py:42
2025-10-28 12:00:30 [DEBUG] Error added: syntax at main.py:42
2025-10-28 12:00:45 [DEBUG] Error added: syntax at main.py:42
2025-10-28 12:01:00 [WARNING] Loop detectado: Repeatedly failing at line 42
```

**En la trajectory (observación):**
```
Your edits have been applied, but the linter has found syntax errors.

<ERRORS>
- line 42 col 8: SyntaxError: invalid syntax
</ERRORS>

======================================================================
⚠️  SYNTAX ERROR - Try these steps:
1. Check for missing/extra parentheses, brackets, or quotes
2. Verify the line before/after your edit for completion
3. Review the original code structure before editing
4. Look for unclosed strings, lists, or function calls

🚨 WARNING: This is your 3th syntax error.
Consider:
- Taking a completely different approach to solve this issue
- Re-reading the file to understand the context better
- Starting with a simpler change first
- Searching for similar code patterns in the repository
======================================================================
```

---

## 4️⃣ SEÑALES DE PROBLEMAS

### ❌ Problema 1: No se resetea el detector

**Síntoma:**
```bash
grep "Error detector reset" trajectories/
# No retorna nada
```

**Causa:** Los archivos `run_single.py` o `run_batch.py` no están llamando a `reset_global_error_detector()`

**Verificar:**
```bash
grep -n "reset_global_error_detector" sweagent/run/run_single.py
grep -n "reset_global_error_detector" sweagent/run/run_batch.py
```

Debe aparecer la función importada y llamada.

---

### ❌ Problema 2: ImportError

**Síntoma:**
```
ImportError: cannot import name 'reset_global_error_detector'
ModuleNotFoundError: No module named 'sweagent.agent.pattern_detector'
```

**Causa:** Los archivos modificados no están sincronizados o hay errores de importación

**Solución:**
```bash
# Verificar que todos los archivos están en su lugar
ls -la sweagent/agent/pattern_detector.py
ls -la sweagent/agent/history_processors.py

# Verificar sintaxis
python3 -m py_compile sweagent/agent/pattern_detector.py
python3 -m py_compile sweagent/agent/history_processors.py
```

---

### ❌ Problema 3: No se detectan errores

**Síntoma:**
```bash
grep "Error added:" trajectories/
# No retorna nada (pero el agente SÍ cometió errores)
```

**Causa:** El método `_extract_error_from_observation` no está funcionando

**Verificar:**
```bash
# Ver si hay errores en las observaciones
grep -r "SyntaxError\|IndentationError\|NameError" trajectories/*.traj

# Verificar que history_processors.py tiene el código correcto
grep -A 5 "_extract_error_from_observation" sweagent/agent/history_processors.py
```

---

### ❌ Problema 4: Contaminación entre instancias (batch)

**Síntoma:** En batch, la instancia 2 muestra errores de la instancia 1

**Verificar:**
```bash
# Buscar cuántas veces se resetea en una ejecución batch de 3 instancias
grep -c "Error detector reset for instance" trajectories/*/run_batch.log
# Debe retornar: 3
```

**Si retorna menos:** El reset no está funcionando en `run_batch.py`

---

## 5️⃣ COMANDOS DE DEBUGGING AVANZADO

### Ver estadísticas completas de una instancia

```bash
# Extraer todas las líneas relacionadas con el detector de errores
grep -E "Error detector|Error added:|Loop detectado|WARNING.*error" \
    trajectories/<path>/<instance>.debug.log > error_detector_analysis.txt

# Ver estadísticas
cat error_detector_analysis.txt
```

### Analizar tipos de errores detectados

```bash
# Contar errores por tipo
grep "Error added:" trajectories/*/debug.log | \
    sed 's/.*Error added: \([^ ]*\).*/\1/' | \
    sort | uniq -c | sort -rn
```

**Salida esperada:**
```
  15 syntax
   8 indentation
   5 undefined
   3 import
```

### Ver timeline de errores en una instancia

```bash
# Extraer timestamp + tipo de error
grep "Error added:" trajectories/<path>/<instance>.debug.log | \
    sed 's/\(.*\) Error added: \(.*\)/\1 | \2/'
```

---

## 6️⃣ PRUEBA RÁPIDA CON EJEMPLO MÍNIMO

### Crear un repo de prueba:

```bash
mkdir -p /tmp/test-error-recovery
cd /tmp/test-error-recovery
git init

# Crear un archivo con error intencional
cat > broken.py << 'EOF'
def hello()
    print("missing colon")
EOF

git add broken.py
git commit -m "Add broken file"
```

### Ejecutar SWE-agent:

```bash
sweagent run \
    --config config/default.yaml \
    --agent.model.name "azure/gpt-4o" \
    --env.repo.path /tmp/test-error-recovery \
    --problem_statement.text "Fix the syntax error in broken.py" \
    --output_dir /tmp/test-trajectories
```

### Verificar:

```bash
# 1. Reset del detector
grep "Error detector reset" /tmp/test-trajectories/*/debug.log

# 2. Errores detectados
grep "Error added:" /tmp/test-trajectories/*/debug.log

# 3. Sugerencias
grep -A 10 "SYNTAX ERROR" /tmp/test-trajectories/*/*.traj
```

---

## 7️⃣ CHECKLIST FINAL

Antes de considerar que el sistema funciona correctamente:

```bash
# Test 1: Reseteo
[ ] grep -r "Error detector reset" trajectories/ | wc -l  # > 0

# Test 2: Detección de errores
[ ] grep -r "Error added:" trajectories/ | wc -l  # > 0 (si hubo errores)

# Test 3: Sugerencias
[ ] grep -r "⚠️" trajectories/ | wc -l  # > 0 (si hubo loops)

# Test 4: Sin errores de importación
[ ] grep -r "ImportError.*pattern_detector" trajectories/ | wc -l  # = 0

# Test 5: Sin errores de importación (reset)
[ ] grep -r "ImportError.*reset_global_error_detector" trajectories/ | wc -l  # = 0
```

---

## 📞 SI TODO FALLA

Si después de seguir esta guía aún hay problemas:

1. **Verificar versión de los archivos:**
   ```bash
   git log --oneline -5
   # Debe incluir: "Fix: Critical error recovery system integration issues"
   ```

2. **Verificar que los archivos están actualizados:**
   ```bash
   git diff origin/main sweagent/agent/history_processors.py
   git diff origin/main sweagent/run/run_batch.py
   git diff origin/main sweagent/run/run_single.py
   ```

3. **Reinstalar dependencias:**
   ```bash
   pip install -e .
   ```

4. **Revisar el código manualmente:**
   - `sweagent/agent/history_processors.py` debe tener `_GLOBAL_ERROR_DETECTOR`
   - `sweagent/run/run_batch.py` debe llamar a `reset_global_error_detector()` en `_run_instance`
   - `sweagent/run/run_single.py` debe llamar a `reset_global_error_detector()` en `run`

---

## ✅ CONCLUSIÓN

Si ves estos 3 elementos en los logs, el sistema está funcionando:

1. ✅ `Error detector reset for instance <id>` al inicio
2. ✅ `Error added: <type> at <file>:<line>` cuando hay errores
3. ✅ Sugerencias con `⚠️` en las observaciones después de loops

**¡El sistema de recuperación de errores está funcionando correctamente! 🎉**
