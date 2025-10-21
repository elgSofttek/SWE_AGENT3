"""
Error Pattern Detector for SWE-agent
Detecta patrones recurrentes en errores del agente y sugiere recuperación

Basado en el paper SWE-agent (Sección B.3.3, págs. 31-32)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
import logging

# Configurar logger
logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """Representa un patrón de error detectado"""
    error_type: str
    frequency: int
    affected_lines: List[int]
    error_messages: List[str]
    

class ErrorPatternDetector:
    """
    Detecta patrones recurrentes en errores del agente
    
    Esta clase analiza el historial de errores para:
    - Identificar tipos de errores comunes
    - Detectar loops de errores repetitivos
    - Generar sugerencias contextuales de recuperación
    - Proporcionar estadísticas útiles
    
    Basado en los hallazgos del paper SWE-agent:
    - 51.7% de trayectorias tienen ≥1 edición fallida
    - 57.2% de probabilidad de recuperación después del 1er error
    - ~40% de probabilidad después del 2do error
    """
    
    def __init__(self):
        self.error_history: List[Dict] = []
        self.pattern_counters = defaultdict(int)
        
        # Patrones comunes del paper (Tabla 9, pág. 35)
        # Expandidos con variaciones reales observadas
        self.known_patterns = {
            'indentation': r'IndentationError|unexpected indent|expected an indented block|unindent does not match',
            'syntax': r'SyntaxError|invalid syntax|EOF while scanning|unterminated string|unexpected EOF|invalid character',
            'undefined': r'NameError|undefined|not defined|name .* is not defined',
            'import': r'ImportError|ModuleNotFoundError|cannot import|No module named',
            'type': r'TypeError|AttributeError|object has no attribute|takes .* positional argument',
            'logic': r'IndexError|KeyError|ValueError|list index out of range|dictionary key error'
        }
        
        logger.info("ErrorPatternDetector initialized")
    
    def add_error(self, error_info: Dict) -> None:
        """
        Registra un nuevo error en el historial
        
        Args:
            error_info: Diccionario con información del error
                - message (str, requerido): Mensaje del error
                - file (str, opcional): Archivo donde ocurrió
                - line (int, opcional): Línea del error
                - action (str, opcional): Acción que causó el error (edit, search, etc.)
                - code_snippet (str, opcional): Código relacionado
                - traceback (str, opcional): Stack trace completo
        
        Raises:
            ValueError: Si 'message' no está presente en error_info
        """
        # Validación de entrada
        if 'message' not in error_info:
            logger.error("Attempted to add error without 'message' field")
            raise ValueError("error_info debe contener el campo 'message'")
        
        error_type = self._classify_error(error_info['message'])
        
        # Crear entrada de error estructurada
        error_entry = {
            'timestamp': len(self.error_history),
            'error_type': error_type,
            'message': error_info['message'],
            'file': error_info.get('file', ''),
            'line': error_info.get('line', 0),
            'action': error_info.get('action', ''),
            'code_snippet': error_info.get('code_snippet', ''),
            'traceback': error_info.get('traceback', '')
        }
        
        self.error_history.append(error_entry)
        
        # Actualizar contador de patrones
        self.pattern_counters[error_type] += 1
        
        logger.debug(f"Error added: {error_type} at {error_entry['file']}:{error_entry['line']}")
    
    def _classify_error(self, error_message: str) -> str:
        """
        Clasifica el error según patrones conocidos
        
        Args:
            error_message: Mensaje de error a clasificar
            
        Returns:
            Tipo de error ('indentation', 'syntax', etc.) o 'unknown'
        """
        # Protección contra valores None o vacíos
        if not error_message:
            logger.warning("Empty error message received")
            return 'unknown'
        
        # Buscar coincidencias con patrones conocidos
        for pattern_name, pattern_regex in self.known_patterns.items():
            try:
                if re.search(pattern_regex, error_message, re.IGNORECASE):
                    return pattern_name
            except re.error as e:
                logger.error(f"Regex error in pattern '{pattern_name}': {e}")
                continue
        
        return 'unknown'
    
    def detect_loop(self, window_size: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Detecta si el agente está en un loop de errores
        
        Implementa 4 estrategias de detección basadas en el paper (Figura 20, pág. 31):
        1. Mismo tipo de error repetido
        2. Misma línea editada múltiples veces
        3. Alternancia entre 2 tipos de error (patrón A-B-A-B)
        4. Múltiples errores en el mismo archivo
        
        Args:
            window_size: Número de errores recientes a analizar (default: 5)
            
        Returns:
            Tupla (is_loop, reason):
                - is_loop (bool): True si se detectó un loop
                - reason (str): Descripción del loop detectado, None si no hay loop
        """
        if len(self.error_history) < window_size:
            return False, None
        
        recent_errors = self.error_history[-window_size:]
        
        # 1. Mismo tipo de error repetido
        error_types = [e['error_type'] for e in recent_errors]
        if len(set(error_types)) == 1 and error_types[0] != 'unknown':
            logger.warning(f"Loop detectado: Repetitive {error_types[0]} errors")
            return True, f"Repetitive {error_types[0]} errors detected"
        
        # 2. Misma línea editada múltiples veces
        lines = [e['line'] for e in recent_errors if e['line'] > 0]
        if len(lines) >= 3 and len(set(lines)) == 1:
            logger.warning(f"Loop detectado: Repeatedly failing at line {lines[0]}")
            return True, f"Repeatedly failing at line {lines[0]}"
        
        # 3. Alternancia entre 2 errores (A-B-A-B pattern)
        if len(set(error_types)) == 2:
            pattern = ''.join([t[0] for t in error_types])
            if self._is_alternating(pattern):
                logger.warning(f"Loop detectado: Alternating between {set(error_types)}")
                return True, f"Alternating between {set(error_types)}"
        
        # 4. Múltiples errores en el mismo archivo
        files = [e['file'] for e in recent_errors if e['file']]
        if len(set(files)) == 1 and len(files) >= 4:
            error_count = len([e for e in recent_errors if e['file'] == files[0]])
            if error_count >= 4:
                logger.warning(f"Loop detectado: Multiple errors in {files[0]}")
                return True, f"Multiple errors in same file: {files[0]}"
        
        return False, None
    
    def _is_alternating(self, pattern: str) -> bool:
        """
        Verifica si hay patrón alternante (ABABAB...)
        
        Args:
            pattern: String con secuencia de caracteres a verificar
            
        Returns:
            True si el patrón alterna consistentemente
        """
        if len(pattern) < 4:
            return False
        
        # Verificar que cada elemento difiere del siguiente
        return all(pattern[i] != pattern[i+1] for i in range(len(pattern)-1))
    
    def get_recovery_suggestion(self) -> Optional[str]:
        """
        Genera sugerencia basada en el historial
        
        Inspirado en las categorías de fallas (Tabla 9, pág. 35):
        - Incorrect Implementation
        - Failed Edit Recovery
        - Failed to Find Edit Location
        - etc.
        
        Returns:
            String con sugerencia formateada o None si no hay errores
        """
        if not self.error_history:
            return None
        
        recent_error = self.error_history[-1]
        error_type = recent_error['error_type']
        frequency = self.pattern_counters[error_type]
        
        # Sugerencias específicas por tipo de error
        suggestions = {
            'indentation': (
                "⚠️  INDENTATION ERROR - Common fixes:\n"
                "1. Check that all lines use consistent spacing (4 spaces or 1 tab)\n"
                "2. Verify the indentation matches the surrounding code\n"
                "3. Use the 'goto' command to see context around your edit\n"
                "4. Compare with neighboring functions for proper indentation level"
            ),
            'syntax': (
                "⚠️  SYNTAX ERROR - Try these steps:\n"
                "1. Check for missing/extra parentheses, brackets, or quotes\n"
                "2. Verify the line before/after your edit for completion\n"
                "3. Review the original code structure before editing\n"
                "4. Look for unclosed strings, lists, or function calls"
            ),
            'undefined': (
                "⚠️  UNDEFINED NAME - Likely causes:\n"
                "1. Missing import statement at the top of the file\n"
                "2. Variable defined in a different scope\n"
                "3. Typo in variable/function name\n"
                "4. Variable defined after it's used\n"
                "→ Use 'search_file' to find where this name is defined\n"
                "→ Use 'search_dir' to search across the entire codebase"
            ),
            'import': (
                "⚠️  IMPORT ERROR - Solutions:\n"
                "1. Check if the module is available in this environment\n"
                "2. Verify the import path is correct (relative vs absolute)\n"
                "3. Look for similar imports elsewhere in the codebase\n"
                "4. Check if the module needs to be installed\n"
                "→ Use 'search_dir' to find existing import patterns"
            ),
            'type': (
                "⚠️  TYPE/ATTRIBUTE ERROR - Check:\n"
                "1. Variable types match expected operations\n"
                "2. Object has the attribute/method you're calling\n"
                "3. Review the object's class definition\n"
                "4. Check function signatures and argument types\n"
                "→ Use 'search_file' to find the class/function definition"
            ),
            'logic': (
                "⚠️  LOGIC ERROR (Index/Key/Value) - Verify:\n"
                "1. List/dict indices are within bounds\n"
                "2. Keys exist before accessing them (use .get() or 'in')\n"
                "3. Check for empty collections before accessing\n"
                "4. Verify loop ranges and conditions"
            ),
        }
        
        base_suggestion = suggestions.get(error_type, 
            "⚠️  ERROR DETECTED - Consider a different approach\n"
            "1. Re-read the error message carefully\n"
            "2. Review the surrounding code for context\n"
            "3. Try a simpler, incremental change")
        
        # Añadir advertencia si hay muchos fallos del mismo tipo
        if frequency >= 3:
            base_suggestion += (
                f"\n\n🚨 WARNING: This is your {frequency}th {error_type} error.\n"
                f"Consider:\n"
                f"- Taking a completely different approach to solve this issue\n"
                f"- Re-reading the file to understand the context better\n"
                f"- Starting with a simpler change first\n"
                f"- Searching for similar code patterns in the repository"
            )
        
        # Advertencia adicional si hay muchos errores totales
        total_errors = len(self.error_history)
        if total_errors >= 7:
            base_suggestion += (
                f"\n\n⚠️  TOTAL ERRORS: {total_errors}\n"
                f"You may be approaching this problem incorrectly.\n"
                f"Consider requesting human assistance or trying a different strategy."
            )
        
        return base_suggestion
    
    def should_suggest_alternative_approach(self) -> bool:
        """
        Determina si se debe sugerir un enfoque completamente diferente
        
        Basado en los datos de recuperación del paper (Figura 20):
        - 90.5% de probabilidad de éxito al primer intento
        - 57.2% después de 1 fallo
        - ~40% después de 2 fallos
        - Significativamente menor después de 3+ fallos
        
        Returns:
            True si se debe recomendar cambio de estrategia
        """
        if len(self.error_history) < 3:
            return False
        
        # Si hay muchos errores recientes (4+ en los últimos 5)
        if len(self.error_history) >= 5:
            recent_5 = self.error_history[-5:]
            # Contar cuántos de los últimos 5 intentos fueron errores
            # (En este contexto, todos en error_history son errores)
            if len(recent_5) >= 4:
                logger.info("Suggesting alternative approach: 4+ errors in last 5 attempts")
                return True
        
        # Si el mismo tipo de error ocurre 3+ veces consecutivas
        if len(self.error_history) >= 3:
            last_3_types = [e['error_type'] for e in self.error_history[-3:]]
            if len(set(last_3_types)) == 1 and last_3_types[0] != 'unknown':
                logger.info(f"Suggesting alternative approach: 3 consecutive {last_3_types[0]} errors")
                return True
        
        # Si hay más de 8 errores totales
        if len(self.error_history) >= 8:
            logger.info(f"Suggesting alternative approach: {len(self.error_history)} total errors")
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Retorna estadísticas completas del historial de errores
        
        Útil para:
        - Debugging del sistema de recuperación
        - Análisis post-mortem de trayectorias
        - Decidir cuándo abortar un intento
        
        Returns:
            Diccionario con métricas detalladas
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_type': {},
                'recent_errors': 0,
                'recovery_attempts': 0,
                'most_common_error': None,
                'unique_files_affected': 0,
                'avg_errors_per_file': 0.0
            }
        
        unique_files = set(e['file'] for e in self.error_history if e['file'])
        
        return {
            'total_errors': len(self.error_history),
            'by_type': dict(self.pattern_counters),
            'recent_errors': len([e for e in self.error_history[-5:]]),
            'recovery_attempts': self._count_recovery_attempts(),
            'most_common_error': max(self.pattern_counters.items(), 
                                    key=lambda x: x[1])[0] if self.pattern_counters else None,
            'unique_files_affected': len(unique_files),
            'avg_errors_per_file': (
                len(self.error_history) / max(1, len(unique_files))
            ),
            'error_rate': self.get_error_rate(),
            'consecutive_same_type': self._count_consecutive_same_type()
        }
    
    def _count_recovery_attempts(self) -> int:
        """
        Cuenta cuántas veces se ha intentado recuperar
        
        Define "intento de recuperación" como:
        - Errores consecutivos en la misma línea exacta, O
        - Errores en líneas cercanas (±10) del mismo archivo
        
        Returns:
            Número de intentos de recuperación detectados
        """
        attempts = 0
        
        for i in range(1, len(self.error_history)):
            curr_error = self.error_history[i]
            prev_error = self.error_history[i-1]
            
            # Misma línea exacta
            if (curr_error['line'] == prev_error['line'] and 
                curr_error['line'] > 0):
                attempts += 1
            # Líneas cercanas en el mismo archivo
            elif (curr_error['file'] == prev_error['file'] and 
                  curr_error['file'] and 
                  curr_error['line'] > 0 and prev_error['line'] > 0 and
                  abs(curr_error['line'] - prev_error['line']) <= 10):
                attempts += 1
        
        return attempts
    
    def _count_consecutive_same_type(self) -> int:
        """
        Cuenta la racha actual de errores del mismo tipo
        
        Returns:
            Número de errores consecutivos del mismo tipo al final del historial
        """
        if not self.error_history:
            return 0
        
        last_type = self.error_history[-1]['error_type']
        count = 1
        
        for i in range(len(self.error_history) - 2, -1, -1):
            if self.error_history[i]['error_type'] == last_type:
                count += 1
            else:
                break
        
        return count
    
    def reset(self) -> None:
        """
        Reinicia el detector (útil para nueva tarea)
        
        Debe llamarse al iniciar una nueva instancia de SWE-bench
        para evitar contaminación entre tareas
        """
        logger.info(f"Resetting detector. Previous stats: {self.get_statistics()}")
        self.error_history.clear()
        self.pattern_counters.clear()
    
    # ========== MÉTODOS DE UTILIDAD ADICIONALES ==========
    
    def get_last_n_errors(self, n: int = 3) -> List[Dict]:
        """
        Retorna los últimos N errores
        
        Args:
            n: Número de errores a retornar
            
        Returns:
            Lista de los últimos N errores (o menos si no hay suficientes)
        """
        return self.error_history[-n:] if len(self.error_history) >= n else self.error_history.copy()
    
    def has_error_in_file(self, filename: str) -> bool:
        """
        Verifica si hay errores previos en un archivo específico
        
        Args:
            filename: Nombre del archivo a verificar
            
        Returns:
            True si hay al menos un error registrado en ese archivo
        """
        return any(e['file'] == filename for e in self.error_history)
    
    def get_errors_by_type(self, error_type: str) -> List[Dict]:
        """
        Retorna todos los errores de un tipo específico
        
        Args:
            error_type: Tipo de error a filtrar (e.g., 'indentation', 'syntax')
            
        Returns:
            Lista de errores que coinciden con el tipo especificado
        """
        return [e for e in self.error_history if e['error_type'] == error_type]
    
    def get_errors_by_file(self, filename: str) -> List[Dict]:
        """
        Retorna todos los errores de un archivo específico
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Lista de errores en ese archivo
        """
        return [e for e in self.error_history if e['file'] == filename]
    
    def get_error_rate(self) -> float:
        """
        Retorna la tasa de error reciente (últimos 5 intentos)
        
        En el contexto actual, todos los eventos en error_history son errores,
        por lo que esto retorna el número de errores en la ventana reciente.
        
        Útil para determinar si el agente está mejorando o empeorando.
        
        Returns:
            Número entre 0.0 y 1.0 (proporción de errores)
        """
        if not self.error_history:
            return 0.0
        
        # En ventana de 5
        window_size = 5
        recent_count = min(len(self.error_history), window_size)
        
        return recent_count / window_size
    
    def get_most_problematic_file(self) -> Optional[str]:
        """
        Identifica el archivo con más errores
        
        Returns:
            Nombre del archivo con más errores, o None si no hay errores
        """
        if not self.error_history:
            return None
        
        file_counts = defaultdict(int)
        for error in self.error_history:
            if error['file']:
                file_counts[error['file']] += 1
        
        if not file_counts:
            return None
        
        return max(file_counts.items(), key=lambda x: x[1])[0]
    
    def get_problematic_lines(self, filename: str, threshold: int = 2) -> List[int]:
        """
        Identifica líneas problemáticas en un archivo
        
        Args:
            filename: Archivo a analizar
            threshold: Número mínimo de errores para considerar una línea problemática
            
        Returns:
            Lista de números de línea con ≥threshold errores
        """
        line_counts = defaultdict(int)
        
        for error in self.error_history:
            if error['file'] == filename and error['line'] > 0:
                line_counts[error['line']] += 1
        
        return [line for line, count in line_counts.items() if count >= threshold]
    
    def summary(self) -> str:
        """
        Genera un resumen legible del estado actual
        
        Returns:
            String formateado con resumen del detector
        """
        stats = self.get_statistics()
        
        summary = f"""
╔══════════════════════════════════════════════════════════╗
║           ERROR PATTERN DETECTOR SUMMARY                 ║
╚══════════════════════════════════════════════════════════╝

📊 Total Errors: {stats['total_errors']}
📈 Recent Errors (last 5): {stats['recent_errors']}
🔄 Recovery Attempts: {stats['recovery_attempts']}

📁 Files Affected: {stats['unique_files_affected']}
📝 Avg Errors per File: {stats['avg_errors_per_file']:.2f}

🏷️  Errors by Type:
"""
        
        for error_type, count in sorted(stats['by_type'].items(), 
                                       key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_errors'] * 100) if stats['total_errors'] > 0 else 0
            summary += f"   - {error_type}: {count} ({percentage:.1f}%)\n"
        
        if stats['most_common_error']:
            summary += f"\n⚠️  Most Common: {stats['most_common_error']}\n"
        
        most_problematic = self.get_most_problematic_file()
        if most_problematic:
            summary += f"🎯 Most Problematic File: {most_problematic}\n"
        
        # Estado actual
        is_loop, loop_reason = self.detect_loop()
        if is_loop:
            summary += f"\n🔴 LOOP DETECTED: {loop_reason}\n"
        
        if self.should_suggest_alternative_approach():
            summary += "\n🚨 RECOMMENDATION: Try a different approach!\n"
        
        return summary


# ========== FUNCIONES DE UTILIDAD ==========

def create_error_info(message: str, 
                     file: str = '', 
                     line: int = 0,
                     action: str = '',
                     code_snippet: str = '',
                     traceback: str = '') -> Dict:
    """
    Helper function para crear diccionario de error_info estructurado
    
    Args:
        message: Mensaje de error (requerido)
        file: Archivo donde ocurrió el error
        line: Número de línea
        action: Comando que causó el error
        code_snippet: Código relacionado
        traceback: Stack trace completo
        
    Returns:
        Diccionario formateado para ErrorPatternDetector.add_error()
    """
    return {
        'message': message,
        'file': file,
        'line': line,
        'action': action,
        'code_snippet': code_snippet,
        'traceback': traceback
    }
