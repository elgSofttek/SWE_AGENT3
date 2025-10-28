#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de recuperación de errores.

Este script verifica que:
1. El detector global se inicializa correctamente
2. Los errores se registran con toda la información
3. La detección de loops funciona
4. Las sugerencias se generan correctamente
5. El reset funciona entre instancias
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from sweagent.agent.pattern_detector import ErrorPatternDetector, create_error_info
from sweagent.agent.history_processors import _GLOBAL_ERROR_DETECTOR, reset_global_error_detector


def test_1_initialization():
    """Test 1: Verificar que el detector global se inicializa"""
    print("\n" + "="*70)
    print("TEST 1: Inicialización del detector global")
    print("="*70)

    assert _GLOBAL_ERROR_DETECTOR is not None, "❌ Detector global no inicializado"
    assert isinstance(_GLOBAL_ERROR_DETECTOR, ErrorPatternDetector), "❌ Tipo incorrecto"

    print("✅ Detector global inicializado correctamente")
    print(f"   Tipo: {type(_GLOBAL_ERROR_DETECTOR)}")
    print(f"   Errores en historial: {len(_GLOBAL_ERROR_DETECTOR.error_history)}")
    return True


def test_2_error_registration():
    """Test 2: Verificar que los errores se registran con información completa"""
    print("\n" + "="*70)
    print("TEST 2: Registro de errores con información completa")
    print("="*70)

    # Limpiar historial
    reset_global_error_detector()

    # Registrar un error completo
    error_info = create_error_info(
        message="SyntaxError: invalid syntax",
        file="test_file.py",
        line=42,
        action="str_replace",
        code_snippet="def foo(",
        traceback="Traceback (most recent call last)..."
    )

    _GLOBAL_ERROR_DETECTOR.add_error(error_info)

    assert len(_GLOBAL_ERROR_DETECTOR.error_history) == 1, "❌ Error no registrado"

    last_error = _GLOBAL_ERROR_DETECTOR.error_history[-1]
    print("✅ Error registrado correctamente")
    print(f"   Tipo: {last_error['error_type']}")
    print(f"   Archivo: {last_error['file']}")
    print(f"   Línea: {last_error['line']}")
    print(f"   Acción: {last_error['action']}")
    print(f"   Mensaje: {last_error['message'][:50]}...")

    assert last_error['error_type'] == 'syntax', f"❌ Tipo incorrecto: {last_error['error_type']}"
    assert last_error['file'] == 'test_file.py', "❌ Archivo incorrecto"
    assert last_error['line'] == 42, "❌ Línea incorrecta"

    return True


def test_3_loop_detection():
    """Test 3: Verificar detección de loops"""
    print("\n" + "="*70)
    print("TEST 3: Detección de loops")
    print("="*70)

    reset_global_error_detector()

    # Simular 5 errores del mismo tipo (debería detectar loop)
    for i in range(5):
        _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
            message=f"IndentationError: unexpected indent #{i}",
            file="test.py",
            line=10 + i,
            action="edit"
        ))

    is_loop, reason = _GLOBAL_ERROR_DETECTOR.detect_loop()

    print(f"   Errores registrados: {len(_GLOBAL_ERROR_DETECTOR.error_history)}")
    print(f"   Loop detectado: {is_loop}")
    print(f"   Razón: {reason}")

    assert is_loop, "❌ Loop no detectado (debería detectar 5 errores del mismo tipo)"
    assert "indentation" in reason.lower(), f"❌ Razón incorrecta: {reason}"

    print("✅ Detección de loops funciona correctamente")
    return True


def test_4_recovery_suggestions():
    """Test 4: Verificar generación de sugerencias"""
    print("\n" + "="*70)
    print("TEST 4: Generación de sugerencias de recuperación")
    print("="*70)

    reset_global_error_detector()

    # Agregar 3 errores de sintaxis
    for i in range(3):
        _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
            message="SyntaxError: invalid syntax",
            file="script.py",
            line=20
        ))

    suggestion = _GLOBAL_ERROR_DETECTOR.get_recovery_suggestion()

    assert suggestion is not None, "❌ No se generó sugerencia"
    assert "SYNTAX ERROR" in suggestion, "❌ Sugerencia incorrecta para error de sintaxis"
    assert "3th syntax error" in suggestion or "3rd syntax error" in suggestion, "❌ No menciona frecuencia"

    print("✅ Sugerencias generadas correctamente")
    print(f"   Longitud: {len(suggestion)} caracteres")
    print(f"   Incluye advertencia de frecuencia: {'✅' if '3' in suggestion else '❌'}")
    print("\n   Vista previa:")
    print("   " + "\n   ".join(suggestion.split("\n")[:5]))

    return True


def test_5_reset_functionality():
    """Test 5: Verificar que el reset funciona"""
    print("\n" + "="*70)
    print("TEST 5: Funcionalidad de reset")
    print("="*70)

    # Agregar errores
    for i in range(5):
        _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
            message=f"Error {i}",
            file="test.py"
        ))

    errors_before = len(_GLOBAL_ERROR_DETECTOR.error_history)
    print(f"   Errores antes del reset: {errors_before}")

    # Reset
    reset_global_error_detector()

    errors_after = len(_GLOBAL_ERROR_DETECTOR.error_history)
    print(f"   Errores después del reset: {errors_after}")

    assert errors_after == 0, f"❌ Reset no funcionó: {errors_after} errores restantes"

    stats = _GLOBAL_ERROR_DETECTOR.get_statistics()
    assert stats['total_errors'] == 0, "❌ Estadísticas no reseteadas"

    print("✅ Reset funciona correctamente")
    return True


def test_6_alternative_approach_suggestion():
    """Test 6: Verificar sugerencia de enfoque alternativo"""
    print("\n" + "="*70)
    print("TEST 6: Sugerencia de enfoque alternativo")
    print("="*70)

    reset_global_error_detector()

    # Agregar 8 errores (debería sugerir enfoque alternativo)
    for i in range(8):
        _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
            message=f"Error {i}",
            file="test.py"
        ))

    should_suggest = _GLOBAL_ERROR_DETECTOR.should_suggest_alternative_approach()

    print(f"   Total de errores: {len(_GLOBAL_ERROR_DETECTOR.error_history)}")
    print(f"   Sugiere enfoque alternativo: {should_suggest}")

    assert should_suggest, "❌ Debería sugerir enfoque alternativo después de 8 errores"

    print("✅ Sugerencia de enfoque alternativo funciona")
    return True


def test_7_statistics():
    """Test 7: Verificar estadísticas"""
    print("\n" + "="*70)
    print("TEST 7: Estadísticas del detector")
    print("="*70)

    reset_global_error_detector()

    # Agregar varios tipos de errores
    _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
        message="SyntaxError: invalid syntax",
        file="file1.py",
        line=10
    ))
    _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
        message="IndentationError: unexpected indent",
        file="file1.py",
        line=20
    ))
    _GLOBAL_ERROR_DETECTOR.add_error(create_error_info(
        message="SyntaxError: EOL while scanning",
        file="file2.py",
        line=5
    ))

    stats = _GLOBAL_ERROR_DETECTOR.get_statistics()

    print(f"   Total de errores: {stats['total_errors']}")
    print(f"   Por tipo: {stats['by_type']}")
    print(f"   Archivos afectados: {stats['unique_files_affected']}")
    print(f"   Error más común: {stats['most_common_error']}")

    assert stats['total_errors'] == 3, f"❌ Total incorrecto: {stats['total_errors']}"
    assert 'syntax' in stats['by_type'], "❌ Tipo 'syntax' no registrado"
    assert stats['by_type']['syntax'] == 2, "❌ Contador de syntax incorrecto"
    assert stats['unique_files_affected'] == 2, "❌ Archivos afectados incorrecto"

    print("✅ Estadísticas funcionan correctamente")
    return True


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🧪" * 35)
    print("VERIFICACIÓN DEL SISTEMA DE RECUPERACIÓN DE ERRORES")
    print("🧪" * 35)

    tests = [
        test_1_initialization,
        test_2_error_registration,
        test_3_loop_detection,
        test_4_recovery_suggestions,
        test_5_reset_functionality,
        test_6_alternative_approach_suggestion,
        test_7_statistics,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FALLÓ: {e}")
            failed += 1
        except Exception as e:
            print(f"\n💥 ERROR INESPERADO: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"✅ Tests pasados: {passed}/{len(tests)}")
    print(f"❌ Tests fallidos: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 TODOS LOS TESTS PASARON 🎉")
        print("El sistema de recuperación de errores está funcionando correctamente.")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON ⚠️")
        print("Revisa los errores arriba para más detalles.")

    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
