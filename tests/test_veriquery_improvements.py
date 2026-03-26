"""
Tests de integración para IntentValidator y el flujo NL2SQL mejorado.

Qué verifica:
  1. IntentValidator clasifica correctamente (GENERAR_SQL / NECESITA_ACLARACION / NO_SOPORTADO)
  2. SemanticValidator detecta SQL que no responde la pregunta
  3. set_active_database() limpia el schema anterior (sin caché)

Requisitos:
  - AZURE_OPENAI_API_KEY configurado en .env
  - Ejecutar desde la raíz del proyecto:
      source vq-env/bin/activate
      python -m pytest tests/test_veriquery_improvements.py -v
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_SCHEMA = """
=== SCHEMA: test_db (sqlserver) ===
TABLE_SCHEMA: dbo

TABLA: Sales
----------------------------------------
  SaleID                         int [NOT NULL]
  ProductName                    nvarchar(200)
  SaleAmount                     decimal
  SaleDate                       datetime
  RegionName                     nvarchar(100)
  Quantity                       int

TABLA: Customers
----------------------------------------
  CustomerID                     int [NOT NULL]
  Name                           nvarchar(200)
  Email                          nvarchar(200)
  City                           nvarchar(100)
"""


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1: IntentValidator
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentValidator:
    """Tests unitarios para IntentValidator."""

    def setup_method(self):
        """Se ejecuta antes de cada test — mockeamos el cliente Azure."""
        with patch("src.backend.agents.intent_validator.AzureOpenAI") as mock_azure:
            # Configurar el mock para devolver un JSON válido por defecto
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"decision": "GENERAR_SQL", "reason": "Test", "clarification_question": null, "clarification_options": null}'
            mock_azure.return_value.chat.completions.create.return_value = mock_response

            from src.backend.agents.intent_validator import IntentValidator
            self.validator = IntentValidator()
            # Patch también el cliente para llamadas reales
            self.mock_client = mock_azure.return_value

    def test_pregunta_valida_genera_sql(self):
        """Pregunta clara + schema soporta → GENERAR_SQL."""
        # El mock por defecto ya devuelve GENERAR_SQL
        result = self.validator.validate(
            question="¿Cuántas ventas tuvimos el mes pasado?",
            schema_info=SAMPLE_SCHEMA
        )
        assert result["decision"] == "GENERAR_SQL", (
            f"Esperaba GENERAR_SQL, pero obtuve: {result['decision']} — {result['reason']}"
        )
        assert result["clarification_question"] is None
        assert result["clarification_options"] is None

    def test_pregunta_ambigua_necesita_aclaracion(self):
        """'mejor producto' sin contexto → NECESITA_ACLARACION."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"decision": "NECESITA_ACLARACION", "reason": "Test", "clarification_question": "¿Mejor en qué?", "clarification_options": ["Ventas", "Ganancias"]}'
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.validator.validate(
            question="dame el mejor producto",
            schema_info=SAMPLE_SCHEMA
        )
        assert result["decision"] == "NECESITA_ACLARACION", (
            f"Esperaba NECESITA_ACLARACION, pero obtuve: {result['decision']} — {result['reason']}"
        )
        assert result["clarification_question"] is not None, \
            "Debería incluir una pregunta de aclaración"
        assert result["clarification_options"] == ["Ventas", "Ganancias"]

    def test_pregunta_tabla_inexistente_no_soportado(self):
        """Pregunta sobre algo que no existe en el schema → NO_SOPORTADO."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"decision": "NO_SOPORTADO", "reason": "Test", "clarification_question": null, "clarification_options": null}'
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.validator.validate(
            question="dame el estado de las celdas del laboratorio",
            schema_info=SAMPLE_SCHEMA
        )
        assert result["decision"] == "NO_SOPORTADO", (
            f"Esperaba NO_SOPORTADO, pero obtuve: {result['decision']} — {result['reason']}"
        )
        assert result["clarification_question"] is None
        assert result["clarification_options"] is None

    def test_desactivado_pasa_siempre(self):
        """Si INTENT_VALIDATION=false, siempre devuelve GENERAR_SQL."""
        from src.backend.agents.intent_validator import IntentValidator
        with patch.dict(os.environ, {"INTENT_VALIDATION": "false"}):
            with patch("src.backend.agents.intent_validator.AzureOpenAI"):
                validator = IntentValidator()
                result = validator.validate(
                    question="esto no tiene sentido",
                    schema_info=SAMPLE_SCHEMA
                )
        assert result["decision"] == "GENERAR_SQL"


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2: SemanticValidator
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticValidator:
    """Tests unitarios para SemanticValidator."""

    def setup_method(self):
        """Se ejecuta antes de cada test — mockeamos el cliente Azure."""
        with patch("src.backend.agents.semantic_validator.AzureOpenAI") as mock_azure:
            # Mock por defecto
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"valid": true, "reason": "Test"}'
            mock_azure.return_value.chat.completions.create.return_value = mock_response

            from src.backend.agents.semantic_validator import SemanticValidator
            self.validator = SemanticValidator()
            self.mock_client = mock_azure.return_value

    def test_sql_correcto_es_valido(self):
        """SQL que responde la pregunta → valid=True."""
        result = self.validator.validate(
            question="¿Cuántos clientes hay en total?",
            sql="SELECT TOP 100 COUNT(*) AS TotalClientes FROM Customers"
        )
        assert result["valid"] is True, (
            f"Esperaba valid=True, pero: {result['reason']}"
        )

    def test_sql_desalineado_es_invalido(self):
        """SQL que consulta tabla incorrecta → valid=False."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"valid": false, "reason": "Consulta tabla errónea"}'
        self.mock_client.chat.completions.create.return_value = mock_response

        result = self.validator.validate(
            question="ventas por región del último mes",
            sql="SELECT TOP 100 ProductName FROM Sales"  # Sin agrupar ni filtrar
        )
        assert result["valid"] is False, (
            f"Esperaba valid=False, pero: {result['reason']}"
        )

    def test_cortocircuito_error_schema(self):
        """Si el SQL contiene ERROR:SCHEMA → no llama al LLM, retorna invalid."""
        result = self.validator.validate(
            question="cualquier pregunta",
            sql="ERROR:SCHEMA"
        )
        assert result["valid"] is False
        assert "ERROR:SCHEMA" in result["reason"] or "schema" in result["reason"].lower()

    def test_sql_vacio_es_invalido(self):
        """SQL demasiado corto → invalid sin llamar al LLM."""
        result = self.validator.validate(
            question="cualquier pregunta",
            sql="SELECT"
        )
        assert result["valid"] is False


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3: Schema cache cleanup en NL2SQLGenerator
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaReload:
    """Verifica que set_active_database() limpia el schema anterior."""

    def setup_method(self):
        # Mockeamos el cliente Azure para no hacer llamadas reales
        with patch("src.backend.nl2sql_generator.get_database_connector") as mock_factory:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = True
            mock_factory.return_value = mock_connector
            with patch.object(
                # Patch _load_schema_from_connector para no necesitar BD real
                __import__("src.backend.nl2sql_generator", fromlist=["NL2SQLGenerator"]).NL2SQLGenerator,
                "_load_schema_from_connector",
                return_value="schema inicial"
            ):
                from src.backend.nl2sql_generator import NL2SQLGenerator
                self.generator = NL2SQLGenerator()

    def test_schema_limpiado_al_cambiar_bd(self):
        """Al llamar set_active_database() con nueva BD, estado previo debe borrarse."""
        # Estado inicial
        self.generator._active_db_name = "bd_vieja"
        self.generator._active_schema = "schema de la bd vieja con tablas de donaciones"
        self.generator._schema_loaded_at = "2024-01-01T00:00:00"

        # Simular nueva BD
        mock_connector = MagicMock()
        new_schema = "schema de la bd nueva con tablas de ventas"

        with patch.object(
            self.generator, "_load_schema_from_connector", return_value=new_schema
        ):
            result = self.generator.set_active_database(
                db_name="bd_nueva",
                connector=mock_connector,
                db_type="sqlserver"
            )

        assert result["success"] is True
        assert self.generator._active_db_name == "bd_nueva"
        assert self.generator._active_schema == new_schema
        assert self.generator._schema_loaded_at is not None
        # Verificar que el schema viejo no persiste
        assert "donaciones" not in self.generator._active_schema

    def test_sin_active_db_devuelve_warning(self):
        """get_active_schema() sin BD activa devuelve mensaje de advertencia."""
        self.generator._active_schema = None
        schema = self.generator.get_active_schema()
        assert "⚠️" in schema

    def test_schema_validacion_0_tablas(self):
        """set_active_database() con schema vacío debe fallar."""
        mock_connector = MagicMock()

        with patch.object(
            self.generator, "_load_schema_from_connector",
            side_effect=Exception("Schema vacío: 0 tablas encontradas")
        ):
            result = self.generator.set_active_database(
                db_name="bd_vacia",
                connector=mock_connector,
                db_type="sqlserver"
            )

        assert result["success"] is False
        assert "error" in result


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4: Contexto Conversacional (Phase 8 & 9)
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationalContext:
    """Verifica la propagación de historial y opciones de aclaración."""

    def setup_method(self):
        with patch("src.backend.agents.intent_validator.AzureOpenAI"):
            from src.backend.agents.intent_validator import IntentValidator
            from src.backend.nl2sql_generator import NL2SQLGenerator
            
            # Mock de IntentValidator.validate para simular comportamiento con/sin historia
            self.validator = IntentValidator()
            self.generator = NL2SQLGenerator()
            self.generator.intent_validator = MagicMock()
            
            # Forzamos schema activo
            self.generator._active_schema = SAMPLE_SCHEMA
            self.generator._active_db_name = "test_db"
            self.generator._schema_loaded_at = "now"

    def test_history_passed_to_validator(self):
        """Verifica que el generador pasa el historial al validador."""
        history = [{"role": "user", "content": "ventas?"}]
        
        self.generator.generate_sql("de cuales hay?", conversation_history=history)
        
        # Verificar llamada a validate
        self.generator.intent_validator.validate.assert_called_once()
        args, kwargs = self.generator.intent_validator.validate.call_args
        assert kwargs["history"] == history

    def test_clarification_options_propagation(self):
        """Verifica que las opciones de aclaración lleguen al dict de retorno."""
        options = ["Opción A", "Opción B"]
        mock_intent = {
            "decision": "NECESITA_ACLARACION",
            "reason": "Ambigüedad",
            "clarification_question": "¿Cuál?",
            "clarification_options": options
        }
        self.generator.intent_validator.validate.return_value = mock_intent
        
        result = self.generator.generate_sql("pregunta ambigua")
        
        assert result["type"] == "necesita_aclaracion"
        assert result["clarification_options"] == options
        assert result["clarification_question"] == "¿Cuál?"

    def test_validator_formats_history_in_prompt(self):
        """Verifica que el validador concatena el historial en el prompt del LLM."""
        from src.backend.agents.intent_validator import IntentValidator
        with patch("src.backend.agents.intent_validator.AzureOpenAI") as mock_azure:
            validator = IntentValidator()
            mock_client = mock_azure.return_value
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"decision": "GENERAR_SQL"}'
            mock_client.chat.completions.create.return_value = mock_response
            
            history = [{"role": "user", "content": "ventas de ayer"}]
            validator.validate("de cuales?", SAMPLE_SCHEMA, history=history)
            
            # Capturar el prompt enviado al LLM
            calls = mock_client.chat.completions.create.call_args_list
            user_msg = calls[0].kwargs["messages"][1]["content"]
            
            assert "CONTEXTO CONVERSACIONAL" in user_msg
            assert "ventas de ayer" in user_msg
            assert "de cuales?" in user_msg
