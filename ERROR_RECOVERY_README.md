# 🔧 Sistema de Recuperación de Errores - Guía Rápida

Esta es una guía rápida para verificar que el sistema de recuperación de errores está funcionando correctamente después de ejecutar SWE-agent.

---

## 🚀 VERIFICACIÓN RÁPIDA (30 SEGUNDOS)

Después de ejecutar SWE-agent, ejecuta este comando:

```bash
./verify_error_recovery.sh trajectories/
```

**Salida esperada:**
```
✅ PASS: Detector se resetea correctamente
✅ PASS: Se detectaron N errores
✅ PASS: No se encontraron errores de importación
🎉 ¡TODOS LOS TESTS CRÍTICOS PASARON!
```

---

## 📁 ARCHIVOS DE DOCUMENTACIÓN

| Archivo | Propósito |
|---------|-----------|
| **VERIFICATION_GUIDE.md** | Guía completa de verificación manual |
| **EXAMPLE_LOGS.md** | Ejemplos visuales de logs correctos vs incorrectos |
| **verify_error_recovery.sh** | Script automatizado de verificación |
| **test_error_recovery.py** | Tests unitarios (requiere dependencias instaladas) |

---

## ✅ 3 SEÑALES DE QUE TODO FUNCIONA

Después de ejecutar SWE-agent, busca estos 3 elementos en los logs:

### 1️⃣ Reset del Detector (CRÍTICO)

```bash
grep -r "Error detector reset" trajectories/
```

**Debe mostrar:**
```
trajectories/.../instance.debug.log:Error detector reset for new instance
```

### 2️⃣ Detección de Errores

```bash
grep -r "Error added:" trajectories/
```

**Debe mostrar (si el agente cometió errores):**
```
trajectories/.../instance.debug.log:Error added: syntax at main.py:42
trajectories/.../instance.debug.log:Error added: indentation at script.py:15
```

### 3️⃣ Sugerencias de Recuperación

```bash
grep -r "⚠️" trajectories/
```

**Debe mostrar (si hubo loops de errores):**
```
⚠️  SYNTAX ERROR - Try these steps:
⚠️  INDENTATION ERROR - Common fixes:
🚨 WARNING: This is your 3th syntax error.
```

---

## 🔍 QUÉ REVISAR EN LOS LOGS

### Ubicación de los logs:

```
trajectories/<user>/<config>__<model>___<instance_id>/
├── <instance_id>/
│   ├── <instance_id>.traj         # Trajectory completa (contiene sugerencias)
│   ├── <instance_id>.debug.log    # ⭐ Información del detector
│   └── <instance_id>.info.log     # Info general
```

### Buscar en `.debug.log`:

1. **Al inicio:**
   ```
   Error detector reset for new instance
   ```

2. **Cuando hay errores:**
   ```
   Error added: <tipo> at <archivo>:<línea>
   ```

3. **Cuando hay loops:**
   ```
   Loop detectado: <razón>
   ```

### Buscar en `.traj`:

Las sugerencias aparecen en las observaciones:
```
======================================================================
⚠️  SYNTAX ERROR - Try these steps:
1. Check for missing/extra parentheses...
======================================================================
```

---

## 🚨 SEÑALES DE PROBLEMAS

| Problema | Síntoma | Causa |
|----------|---------|-------|
| **No se resetea** | `grep "Error detector reset" trajectories/` retorna vacío | run_single.py o run_batch.py no llaman a reset_global_error_detector() |
| **No detecta errores** | `grep "Error added:" trajectories/` retorna vacío (pero el agente SÍ falló) | _extract_error_from_observation() no funciona |
| **ImportError** | Logs muestran "ImportError: cannot import name 'reset_global_error_detector'" | history_processors.py no tiene la función |
| **Contaminación batch** | En batch, reset count < instance count | run_batch.py no resetea entre instancias |

---

## 🛠️ SOLUCIÓN DE PROBLEMAS

### Problema: "Error detector reset" no aparece

**Verificar:**
```bash
# ¿Está la función en el archivo?
grep -n "def reset_global_error_detector" sweagent/agent/history_processors.py

# ¿Se importa en run_single.py?
grep -n "reset_global_error_detector" sweagent/run/run_single.py

# ¿Se importa en run_batch.py?
grep -n "reset_global_error_detector" sweagent/run/run_batch.py
```

**Todos deben retornar líneas. Si no:**
```bash
git status  # Ver si los archivos fueron modificados
git diff origin/main  # Ver diferencias con main
```

---

### Problema: ImportError

**Error típico:**
```
ImportError: cannot import name 'reset_global_error_detector'
```

**Solución:**
```bash
# 1. Verificar que estás en la rama correcta
git branch
# Debe mostrar: * claude/session-011CUZvzwm96Krkg27q5ABq9 o main

# 2. Verificar último commit
git log --oneline -1
# Debe incluir: "Fix: Critical error recovery system integration issues"

# 3. Reinstalar
pip install -e .
```

---

### Problema: No detecta errores

**Si el agente cometió errores pero no aparecen en los logs:**

```bash
# 1. Verificar que _GLOBAL_ERROR_DETECTOR existe
grep -n "_GLOBAL_ERROR_DETECTOR" sweagent/agent/history_processors.py

# 2. Verificar que _extract_error_from_observation tiene el código mejorado
grep -A 10 "def _extract_error_from_observation" sweagent/agent/history_processors.py
```

---

## 📊 ESTADÍSTICAS ÚTILES

### Ver distribución de errores:

```bash
grep -r "Error added:" trajectories/ | \
  sed 's/.*Error added: \([^ ]*\).*/\1/' | \
  sort | uniq -c | sort -rn
```

**Ejemplo de salida:**
```
  15 syntax
   8 indentation
   5 undefined
   3 import
   2 type
```

### Ver timeline de una instancia:

```bash
grep -E "Error detector reset|Error added:|Loop detectado" \
  trajectories/<path>/<instance>.debug.log
```

---

## 🎯 CHECKLIST DE VERIFICACIÓN MANUAL

Marca cada item después de ejecutar SWE-agent:

```
[ ] El script verify_error_recovery.sh pasa todos los tests críticos
[ ] grep "Error detector reset" encuentra al menos 1 resultado
[ ] No hay ImportError en los logs
[ ] Si hubo errores del agente, aparecen como "Error added:"
[ ] Si hubo loops, aparecen sugerencias con ⚠️
[ ] En batch, cada instancia tiene su propio reset
```

**Si todos están marcados:** ✅ El sistema funciona correctamente

---

## 📞 RECURSOS ADICIONALES

- **VERIFICATION_GUIDE.md** - Guía detallada con comandos específicos
- **EXAMPLE_LOGS.md** - Ejemplos visuales de logs correctos
- **verify_error_recovery.sh** - Script automatizado de verificación

---

## 💡 EJEMPLOS RÁPIDOS

### Verificar una ejecución específica:

```bash
# Si acabas de ejecutar:
./verify_error_recovery.sh trajectories/<user>/<config>__<model>___<instance>

# Ver solo el resumen:
./verify_error_recovery.sh trajectories/ | grep -A 20 "RESUMEN"
```

### Ver sugerencias generadas:

```bash
# En trajectories
cat trajectories/*/instance_1/instance_1.traj | \
  python3 -m json.tool | \
  grep -A 15 "⚠️"
```

### Verificar batch completo:

```bash
# Contar resets (debe = número de instancias)
find trajectories/ -name "*.debug.log" -exec grep -l "Error detector reset" {} \; | wc -l

# Contar instancias
find trajectories/ -name "*.debug.log" | wc -l
```

---

## 🎉 CONCLUSIÓN

**El sistema está funcionando si:**

1. ✅ `./verify_error_recovery.sh` pasa los tests críticos
2. ✅ Los logs muestran "Error detector reset"
3. ✅ Los errores se detectan y clasifican
4. ✅ Las sugerencias aparecen cuando hay loops
5. ✅ No hay errores de importación

**Si alguno falla, consulta VERIFICATION_GUIDE.md para troubleshooting detallado.**

---

**¿Todo funcionando?** 🚀 ¡Perfecto! El sistema de recuperación de errores está operativo.

**¿Problemas?** 📖 Consulta VERIFICATION_GUIDE.md para soluciones paso a paso.
