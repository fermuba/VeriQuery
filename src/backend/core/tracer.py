"""
VeriQuery — Query Tracer
========================
Trazabilidad completa del flujo NL2SQL con tres salidas configurables.

Salidas disponibles (configurar en .env):
  TRACE_TERMINAL=true/false  → resumen en terminal (logger.info)
  TRACE_JSON_LOG=true/false  → archivo JSON en logs/queries/ (auditoría permanente)
  TRACE_RESPONSE=true/false  → campo trace_steps en JSON de respuesta al front
  TRACE_LEVEL=full/summary   → full: todos los pasos | summary: solo entrada/salida final

Formato de cada paso:
  [TRACE][archivo][paso] ENTRADA: dato recibido
  [TRACE][archivo][paso] ACCION:  qué hace este paso
  [TRACE][archivo][paso] SALIDA:  resultado → enviado a siguiente paso
  [TRACE][archivo][paso] ERROR:   qué falló y por qué

Archivos de log:
  logs/queries/YYYY-MM-DD.jsonl   → un JSON por línea, un archivo por día
  logs/queries/errors_YYYY-MM-DD.jsonl → solo errores, para monitoreo rápido

Uso:
  tracer = QueryTracer(question="¿Cuántos clientes hay?")

  tracer.step(
      archivo="prompt_shields",
      paso="validar_input",
      entrada="¿Cuántos clientes hay?",
      accion="Buscando patrones jailbreak, injection, PII",
      salida="SAFE → pasa a nl2sql_generator"
  )

  tracer.error("query_crafter", "generar_sql", "Schema no disponible")

  # Al finalizar la request:
  steps = tracer.finalize()   # escribe log JSON, imprime terminal, devuelve dict
"""

import os
import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN DESDE .env
# ============================================================================

def _bool_env(key: str, default: bool = True) -> bool:
    """Lee variable de entorno como bool."""
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


class TracerConfig:
    """
    Lee la configuración del tracer desde variables de entorno.
    Se evalúa una vez al iniciar el módulo.
    """
    TERMINAL: bool = _bool_env("TRACE_TERMINAL", True)
    JSON_LOG: bool = _bool_env("TRACE_JSON_LOG", True)
    RESPONSE: bool = _bool_env("TRACE_RESPONSE", True)
    LEVEL: str = os.getenv("TRACE_LEVEL", "full").lower()  # "full" | "summary"

    LOG_DIR: Path = Path("logs/queries")

    @classmethod
    def is_full(cls) -> bool:
        return cls.LEVEL == "full"

    @classmethod
    def any_enabled(cls) -> bool:
        return cls.TERMINAL or cls.JSON_LOG or cls.RESPONSE

    @classmethod
    def summary(cls) -> dict:
        return {
            "TRACE_TERMINAL": cls.TERMINAL,
            "TRACE_JSON_LOG": cls.JSON_LOG,
            "TRACE_RESPONSE": cls.RESPONSE,
            "TRACE_LEVEL": cls.LEVEL,
            "LOG_DIR": str(cls.LOG_DIR)
        }


# ============================================================================
# MODELOS
# ============================================================================

@dataclass
class TraceStep:
    """Un paso individual de la traza."""
    archivo: str
    paso: str
    entrada: str
    accion: str
    salida: str
    es_error: bool = False
    duracion_ms: Optional[float] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "archivo": self.archivo,
            "paso": self.paso,
            "entrada": self.entrada,
            "accion": self.accion,
            "salida": self.salida,
            "es_error": self.es_error,
            "duracion_ms": self.duracion_ms,
            "timestamp": self.timestamp
        }


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class QueryTracer:
    """
    Registra el flujo completo de una consulta paso a paso.
    Se instancia una vez por request y se pasa entre agentes.

    Ciclo de vida:
      tracer = QueryTracer(question)   → inicia cronómetro
      tracer.step(...)                 → registra paso
      tracer.error(...)                → registra error
      result = tracer.finalize()       → escribe logs, devuelve dict para response
    """

    def __init__(self, question: str, user_id: str = "anonymous"):
        self.question = question
        self.user_id = user_id
        self.steps: List[TraceStep] = []
        self._start_time = time.time()
        self._step_start: Optional[float] = None
        self._query_id = f"{int(self._start_time)}_{abs(hash(question)) % 9999:04d}"
        self._finalized = False
        # Campos de trazabilidad adicionales (v2)
        self.decision_type: Optional[str] = None        # "SQL" | "ACLARACION" | "RECHAZO"
        self.schema_loaded_at: Optional[str] = None    # timestamp del schema usado

        # Crear directorio de logs si está habilitado
        if TracerConfig.JSON_LOG:
            try:
                TracerConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"⚠️ No se pudo crear {TracerConfig.LOG_DIR}: {e}")

    def step(
        self,
        archivo: str,
        paso: str,
        entrada: str,
        accion: str,
        salida: str
    ) -> None:
        """
        Registra un paso exitoso.

        Args:
            archivo: nombre corto del archivo (ej: "prompt_shields")
            paso:    nombre de la acción   (ej: "validar_input")
            entrada: dato que recibe este paso
            accion:  qué hace internamente
            salida:  qué devuelve y a dónde va
        """
        # Calcular duración del paso anterior
        duracion = None
        if self._step_start is not None:
            duracion = round((time.time() - self._step_start) * 1000, 1)
        self._step_start = time.time()

        trace = TraceStep(
            archivo=archivo,
            paso=paso,
            entrada=self._truncar(entrada),
            accion=self._truncar(accion),
            salida=self._truncar(salida),
            es_error=False,
            duracion_ms=duracion
        )
        self.steps.append(trace)

        # Salida terminal inmediata si está habilitado y es nivel full
        if TracerConfig.TERMINAL and TracerConfig.is_full():
            dur_str = f" ({duracion}ms)" if duracion else ""
            logger.info(
                f"[TRACE][{archivo}][{paso}]{dur_str}\n"
                f"  ENTRADA: {trace.entrada}\n"
                f"  ACCION:  {trace.accion}\n"
                f"  SALIDA:  {trace.salida}"
            )

    def error(
        self,
        archivo: str,
        paso: str,
        mensaje_error: str,
        entrada: str = ""
    ) -> None:
        """
        Registra un paso que falló.
        Los errores se escriben siempre al log JSON de errores,
        independientemente del flag TRACE_JSON_LOG.
        """
        trace = TraceStep(
            archivo=archivo,
            paso=paso,
            entrada=self._truncar(entrada),
            accion="ERROR",
            salida=self._truncar(mensaje_error),
            es_error=True
        )
        self.steps.append(trace)

        # Errores siempre van a terminal
        logger.error(
            f"[TRACE][{archivo}][{paso}] ERROR\n"
            f"  ENTRADA: {trace.entrada}\n"
            f"  ERROR:   {trace.salida}"
        )

        # Errores siempre van al log de errores (independiente de TRACE_JSON_LOG)
        self._write_error_log(trace)

    def set_decision(self, decision: str) -> None:
        """
        Registra el tipo de decisión final del pipeline.

        Args:
            decision: "SQL" | "ACLARACION" | "RECHAZO"
        """
        self.decision_type = decision
        if TracerConfig.TERMINAL:
            logger.info(f"[TRACE][DECISION] {decision}")

    def finalize(self) -> Optional[Dict[str, Any]]:
        """
        Finaliza la traza: escribe logs, imprime resumen terminal.

        Returns:
            dict con la traza completa si TRACE_RESPONSE=true, else None
        """
        if self._finalized:
            return self._build_response_dict()

        total_ms = round((time.time() - self._start_time) * 1000, 1)
        errores = sum(1 for s in self.steps if s.es_error)

        # ── Resumen terminal ──────────────────────────────────────────────
        if TracerConfig.TERMINAL:
            status = "✅" if errores == 0 else f"⚠️ {errores} errores"
            logger.info(
                f"[TRACE][RESUMEN] {status} | "
                f"'{self.question[:50]}' | "
                f"{len(self.steps)} pasos | "
                f"{total_ms}ms | "
                f"ID: {self._query_id}"
            )

        # ── Log JSON ──────────────────────────────────────────────────────
        if TracerConfig.JSON_LOG:
            self._write_query_log(total_ms, errores)

        self._finalized = True

        # ── Respuesta al front ────────────────────────────────────────────
        if TracerConfig.RESPONSE:
            return self._build_response_dict(total_ms, errores)

        return None

    # ── MÉTODOS PRIVADOS ──────────────────────────────────────────────────

    def _build_response_dict(
        self,
        total_ms: float = 0,
        errores: int = 0
    ) -> Dict[str, Any]:
        """Construye el dict para incluir en la respuesta JSON al front."""
        if TracerConfig.is_full():
            # Nivel full: todos los pasos con detalle
            steps_data = [s.to_dict() for s in self.steps]
        else:
            # Nivel summary: solo primer y último paso + errores
            steps_data = []
            if self.steps:
                steps_data.append(self.steps[0].to_dict())
            errors = [s.to_dict() for s in self.steps if s.es_error]
            steps_data.extend(errors)
            if len(self.steps) > 1:
                steps_data.append(self.steps[-1].to_dict())

        return {
            "query_id": self._query_id,
            "question": self.question,
            "total_ms": total_ms or round((time.time() - self._start_time) * 1000, 1),
            "step_count": len(self.steps),
            "error_count": errores,
            "level": TracerConfig.LEVEL,
            # v2: campos de trazabilidad adicionales
            "decision_type": self.decision_type,
            "schema_loaded_at": self.schema_loaded_at,
            "steps": steps_data
        }

    def _write_query_log(self, total_ms: float, errores: int) -> None:
        """
        Escribe el log completo en logs/queries/YYYY-MM-DD.jsonl
        Formato JSONL: un objeto JSON por línea, fácil de parsear y consultar.
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = TracerConfig.LOG_DIR / f"{date_str}.jsonl"

            record = {
                "query_id": self._query_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "question": self.question,
                "total_ms": total_ms,
                "step_count": len(self.steps),
                "error_count": errores,
                "level": TracerConfig.LEVEL,
                # v2: campos de trazabilidad adicionales
                "decision_type": self.decision_type,
                "schema_loaded_at": self.schema_loaded_at,
                "steps": [s.to_dict() for s in self.steps]
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"⚠️ No se pudo escribir log de query: {e}")

    def _write_error_log(self, trace: TraceStep) -> None:
        """
        Escribe errores en logs/queries/errors_YYYY-MM-DD.jsonl
        Archivo separado para monitoreo rápido de errores.
        Siempre activo, independiente de TRACE_JSON_LOG.
        """
        try:
            TracerConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            error_file = TracerConfig.LOG_DIR / f"errors_{date_str}.jsonl"

            record = {
                "query_id": self._query_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id,
                "question": self.question,
                "archivo": trace.archivo,
                "paso": trace.paso,
                "entrada": trace.entrada,
                "error": trace.salida
            }

            with open(error_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"⚠️ No se pudo escribir log de error: {e}")

    @staticmethod
    def _truncar(texto: str, max_len: int = 300) -> str:
        texto = str(texto)
        if len(texto) > max_len:
            return texto[:max_len] + "..."
        return texto


# ============================================================================
# UTILIDADES DE LOG
# ============================================================================

def get_tracer_status() -> dict:
    """
    Devuelve el estado actual de la configuración del tracer.
    Útil para mostrar en /api/health o en el panel de admin.
    """
    log_dir = TracerConfig.LOG_DIR
    log_files = []
    total_size_kb = 0

    if log_dir.exists():
        files = sorted(log_dir.glob("*.jsonl"))
        for f in files[-5:]:  # últimos 5 archivos
            size_kb = round(f.stat().st_size / 1024, 1)
            total_size_kb += size_kb
            log_files.append({
                "file": f.name,
                "size_kb": size_kb
            })

    return {
        "config": TracerConfig.summary(),
        "log_dir": str(log_dir),
        "log_dir_exists": log_dir.exists(),
        "recent_files": log_files,
        "total_size_kb": round(total_size_kb, 1)
    }


def count_queries_today() -> int:
    """Cuenta cuántas queries se registraron hoy en el log."""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = TracerConfig.LOG_DIR / f"{date_str}.jsonl"
        if not log_file.exists():
            return 0
        with open(log_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def count_errors_today() -> int:
    """Cuenta cuántos errores se registraron hoy."""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        error_file = TracerConfig.LOG_DIR / f"errors_{date_str}.jsonl"
        if not error_file.exists():
            return 0
        with open(error_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0
