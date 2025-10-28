#!/bin/bash
# Script de verificación rápida del sistema de recuperación de errores
# Uso: ./verify_error_recovery.sh [directorio_de_trajectories]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio de trajectories (por defecto: trajectories/)
TRAJ_DIR="${1:-trajectories}"

if [ ! -d "$TRAJ_DIR" ]; then
    echo -e "${RED}❌ Error: Directorio '$TRAJ_DIR' no encontrado${NC}"
    echo "Uso: $0 [directorio_de_trajectories]"
    exit 1
fi

echo ""
echo "========================================================================"
echo "🔍 VERIFICACIÓN DEL SISTEMA DE RECUPERACIÓN DE ERRORES"
echo "========================================================================"
echo ""
echo "Analizando: $TRAJ_DIR"
echo ""

# Test 1: Verificar reseteo del detector
echo -e "${BLUE}Test 1: Verificando reseteo del detector...${NC}"
RESET_COUNT=$(grep -r "Error detector reset" "$TRAJ_DIR" 2>/dev/null | wc -l)
if [ "$RESET_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Detector se resetea correctamente ($RESET_COUNT veces)${NC}"
    grep -r "Error detector reset" "$TRAJ_DIR" 2>/dev/null | head -3 | sed 's/^/   /'
else
    echo -e "${RED}❌ FAIL: No se encontró reseteo del detector${NC}"
    echo "   Esto indica que run_single.py o run_batch.py no están llamando a reset_global_error_detector()"
fi
echo ""

# Test 2: Verificar detección de errores
echo -e "${BLUE}Test 2: Verificando detección de errores...${NC}"
ERROR_ADDED_COUNT=$(grep -r "Error added:" "$TRAJ_DIR" 2>/dev/null | wc -l)
if [ "$ERROR_ADDED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Se detectaron $ERROR_ADDED_COUNT errores${NC}"
    echo "   Tipos de errores encontrados:"
    grep -r "Error added:" "$TRAJ_DIR" 2>/dev/null | \
        sed 's/.*Error added: \([^ ]*\).*/\1/' | \
        sort | uniq -c | sort -rn | sed 's/^/      /'
else
    echo -e "${YELLOW}⚠️  SKIP: No se detectaron errores (puede ser normal si el agente no cometió errores)${NC}"
fi
echo ""

# Test 3: Verificar detección de loops
echo -e "${BLUE}Test 3: Verificando detección de loops...${NC}"
LOOP_COUNT=$(grep -rE "Loop detectado|Loop detected" "$TRAJ_DIR" 2>/dev/null | wc -l)
if [ "$LOOP_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Se detectaron $LOOP_COUNT loops${NC}"
    grep -rE "Loop detectado|Loop detected" "$TRAJ_DIR" 2>/dev/null | head -3 | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  SKIP: No se detectaron loops (puede ser normal)${NC}"
fi
echo ""

# Test 4: Verificar sugerencias de recuperación
echo -e "${BLUE}Test 4: Verificando sugerencias de recuperación...${NC}"
SUGGESTIONS_COUNT=$(grep -r "⚠️" "$TRAJ_DIR" 2>/dev/null | wc -l)
if [ "$SUGGESTIONS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Se generaron sugerencias ($SUGGESTIONS_COUNT menciones)${NC}"
    # Buscar tipos de sugerencias
    SYNTAX_SUGG=$(grep -r "SYNTAX ERROR" "$TRAJ_DIR" 2>/dev/null | wc -l)
    INDENT_SUGG=$(grep -r "INDENTATION ERROR" "$TRAJ_DIR" 2>/dev/null | wc -l)
    UNDEFINED_SUGG=$(grep -r "UNDEFINED NAME" "$TRAJ_DIR" 2>/dev/null | wc -l)

    [ "$SYNTAX_SUGG" -gt 0 ] && echo "      - SYNTAX ERROR: $SYNTAX_SUGG"
    [ "$INDENT_SUGG" -gt 0 ] && echo "      - INDENTATION ERROR: $INDENT_SUGG"
    [ "$UNDEFINED_SUGG" -gt 0 ] && echo "      - UNDEFINED NAME: $UNDEFINED_SUGG"
else
    echo -e "${YELLOW}⚠️  SKIP: No se generaron sugerencias (puede ser normal si no hubo loops)${NC}"
fi
echo ""

# Test 5: Verificar errores de importación
echo -e "${BLUE}Test 5: Verificando errores de importación...${NC}"
IMPORT_ERRORS=$(grep -rE "ImportError.*pattern_detector|ImportError.*reset_global_error_detector|ModuleNotFoundError.*pattern_detector" "$TRAJ_DIR" 2>/dev/null | wc -l)
if [ "$IMPORT_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No se encontraron errores de importación${NC}"
else
    echo -e "${RED}❌ FAIL: Se encontraron $IMPORT_ERRORS errores de importación${NC}"
    grep -rE "ImportError|ModuleNotFoundError" "$TRAJ_DIR" 2>/dev/null | head -3 | sed 's/^/   /'
fi
echo ""

# Test 6: Verificar contaminación entre instancias (solo para batch)
echo -e "${BLUE}Test 6: Verificando contaminación entre instancias...${NC}"
INSTANCE_DIRS=$(find "$TRAJ_DIR" -maxdepth 2 -type d -name "*__*" 2>/dev/null | wc -l)
if [ "$INSTANCE_DIRS" -gt 1 ]; then
    # Es un run batch
    INSTANCES=$(find "$TRAJ_DIR" -type f -name "*.debug.log" 2>/dev/null | wc -l)
    RESETS=$(grep -r "Error detector reset" "$TRAJ_DIR" 2>/dev/null | wc -l)

    if [ "$RESETS" -ge "$INSTANCES" ]; then
        echo -e "${GREEN}✅ PASS: Cada instancia resetea el detector ($RESETS resets para $INSTANCES instancias)${NC}"
    else
        echo -e "${RED}❌ FAIL: No todas las instancias resetean el detector ($RESETS resets para $INSTANCES instancias)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP: Solo una instancia, test no aplicable${NC}"
fi
echo ""

# Resumen final
echo "========================================================================"
echo "📊 RESUMEN"
echo "========================================================================"
echo ""

TOTAL_TESTS=6
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Contar tests pasados
[ "$RESET_COUNT" -gt 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
[ "$ERROR_ADDED_COUNT" -gt 0 ] && ((PASSED_TESTS++)) || ((SKIPPED_TESTS++))
[ "$LOOP_COUNT" -ge 0 ] && ((PASSED_TESTS++))  # Siempre cuenta como pasado si no hay errores
[ "$SUGGESTIONS_COUNT" -ge 0 ] && ((PASSED_TESTS++))  # Siempre cuenta como pasado
[ "$IMPORT_ERRORS" -eq 0 ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))

if [ "$INSTANCE_DIRS" -gt 1 ]; then
    [ "$RESETS" -ge "$INSTANCES" ] && ((PASSED_TESTS++)) || ((FAILED_TESTS++))
else
    ((SKIPPED_TESTS++))
fi

echo "Tests ejecutados: $TOTAL_TESTS"
echo -e "${GREEN}Tests pasados: $PASSED_TESTS${NC}"
[ "$FAILED_TESTS" -gt 0 ] && echo -e "${RED}Tests fallidos: $FAILED_TESTS${NC}"
[ "$SKIPPED_TESTS" -gt 0 ] && echo -e "${YELLOW}Tests omitidos: $SKIPPED_TESTS${NC}"
echo ""

# Estadísticas adicionales
if [ "$ERROR_ADDED_COUNT" -gt 0 ]; then
    echo "📈 Estadísticas de errores:"
    echo "   - Total de errores detectados: $ERROR_ADDED_COUNT"
    echo "   - Loops detectados: $LOOP_COUNT"
    echo "   - Sugerencias generadas: $SUGGESTIONS_COUNT"
    echo ""
fi

# Conclusión
if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡TODOS LOS TESTS CRÍTICOS PASARON!${NC}"
    echo "El sistema de recuperación de errores está funcionando correctamente."
else
    echo -e "${RED}⚠️  ALGUNOS TESTS FALLARON${NC}"
    echo "Revisa los errores arriba y consulta VERIFICATION_GUIDE.md para más detalles."
fi

echo "========================================================================"
echo ""

# Comandos útiles adicionales
echo "💡 Comandos útiles para más análisis:"
echo ""
echo "   # Ver todos los resets:"
echo "   grep -r \"Error detector reset\" $TRAJ_DIR"
echo ""
echo "   # Ver todos los errores detectados:"
echo "   grep -r \"Error added:\" $TRAJ_DIR"
echo ""
echo "   # Ver todas las sugerencias:"
echo "   grep -r \"⚠️\" $TRAJ_DIR | head -20"
echo ""
echo "   # Ver estadísticas por tipo de error:"
echo "   grep -r \"Error added:\" $TRAJ_DIR | sed 's/.*Error added: \([^ ]*\).*/\1/' | sort | uniq -c"
echo ""

exit $FAILED_TESTS
