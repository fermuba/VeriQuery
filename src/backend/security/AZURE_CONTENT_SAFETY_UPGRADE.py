"""
VeriQuery — Azure AI Content Safety Integration
================================================
UPGRADE DE SEGURIDAD — ACTIVACIÓN POSTERIOR AL HACKATHON

Este fragmento documenta cómo agregar Azure AI Content Safety
como Capa 2 de seguridad en prompt_shields.py.

ARQUITECTURA ACTUAL (regex local):
  Input → regex patterns → ValidationResult

ARQUITECTURA CON ESTE UPGRADE (dos capas):
  Input → regex patterns → Azure Content Safety API → ValidationResult

POR QUÉ ES UN UPGRADE Y NO UN REEMPLAZO:
  - Regex: ~0ms, gratis, sin dependencia de red → se mantiene como Capa 1
  - Azure Content Safety: ~50ms, ML enterprise → se agrega como Capa 2
  - Si Azure falla (timeout, cuota), el sistema sigue funcionando con regex
  - Para el hackathon se puede MENCIONAR en el pitch como "arquitectura
    preparada para enterprise" aunque no esté activado

PREREQUISITOS PARA ACTIVAR:
  1. Crear recurso en Azure Portal:
     → Crear recurso → buscar "Content Safety"
     → Misma región que Azure OpenAI (South Central US)
     → Free tier: 5000 análisis/mes gratis
     → Copiar endpoint y key al .env

  2. Instalar SDK:
     pip install azure-ai-contentsafety

  3. Agregar al .env:
     CONTENT_SAFETY_ENDPOINT=https://tu-resource.cognitiveservices.azure.com/
     CONTENT_SAFETY_KEY=tu_key_aqui
     CONTENT_SAFETY_ENABLED=false   # cambiar a true para activar

CÓMO APLICAR EL UPGRADE (3 pasos quirúrgicos en prompt_shields.py):
============================================================

PASO 1 — Agregar imports al inicio del archivo
(después de los imports existentes)
------------------------------------------------------------

# Agregado: Azure AI Content Safety — Capa 2 de seguridad
# Activar con CONTENT_SAFETY_ENABLED=true en .env
try:
    from azure.ai.contentsafety import ContentSafetyClient
    from azure.ai.contentsafety.models import (
        AnalyzeTextOptions,
        ShieldPromptOptions,
    )
    from azure.core.credentials import AzureKeyCredential
    CONTENT_SAFETY_SDK_AVAILABLE = True
except ImportError:
    CONTENT_SAFETY_SDK_AVAILABLE = False
    # SDK no instalado — el sistema sigue funcionando con regex

------------------------------------------------------------

PASO 2 — Agregar cliente en PromptShield.__init__()
(después de self.blocked_count = 0)
------------------------------------------------------------

        # Agregado: cliente Azure Content Safety (Capa 2)
        # Se inicializa solo si está habilitado y el SDK está instalado
        self._cs_client = None
        self._cs_enabled = (
            os.getenv("CONTENT_SAFETY_ENABLED", "false").lower() == "true"
            and CONTENT_SAFETY_SDK_AVAILABLE
        )

        if self._cs_enabled:
            try:
                endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")
                key = os.getenv("CONTENT_SAFETY_KEY")
                if endpoint and key:
                    self._cs_client = ContentSafetyClient(
                        endpoint=endpoint,
                        credential=AzureKeyCredential(key)
                    )
                    SECURITY_LOGGER.info(
                        "✅ Azure Content Safety activado (Capa 2)"
                    )
                else:
                    SECURITY_LOGGER.warning(
                        "⚠️ CONTENT_SAFETY_ENABLED=true pero "
                        "CONTENT_SAFETY_ENDPOINT o CONTENT_SAFETY_KEY vacíos"
                    )
                    self._cs_enabled = False
            except Exception as e:
                SECURITY_LOGGER.warning(
                    f"⚠️ No se pudo inicializar Azure Content Safety: {e}"
                )
                self._cs_enabled = False
        else:
            SECURITY_LOGGER.info(
                "ℹ️ Azure Content Safety desactivado "
                "(CONTENT_SAFETY_ENABLED=false)"
            )

------------------------------------------------------------

PASO 3 — Agregar llamada en validate_user_input()
(después del bloque de _check_prompt_injection, antes del return final)
------------------------------------------------------------

        # Agregado: Capa 2 — Azure Content Safety Prompt Shields
        # Solo se ejecuta si está habilitado y las capas de regex pasaron
        if self._cs_enabled and self._cs_client:
            cs_result = self._check_azure_content_safety(user_query)
            if not cs_result.is_safe:
                return cs_result

        # Todos los chequeos pasaron
        SECURITY_LOGGER.debug("✅ Input seguro")
        return ValidationResult(
            is_safe=True,
            threat_level=ThreatLevel.SAFE,
            message="Input validado exitosamente"
        )

------------------------------------------------------------

PASO 4 — Agregar método privado en PromptShield
(al final de los métodos privados, antes de get_security_stats)
------------------------------------------------------------

    def _check_azure_content_safety(self, text: str) -> ValidationResult:
        \"\"\"
        Capa 2: Azure AI Content Safety — Prompt Shields.
        Detecta ataques sofisticados que regex no puede capturar:
        - Jailbreak en cualquier idioma o variante creativa
        - Prompt injection indirecta (ataques en documentos adjuntos)
        - Intentos de extracción de información del sistema

        Documentación:
        https://learn.microsoft.com/azure/ai-services/content-safety/quickstart-jailbreak

        Returns:
            ValidationResult — si falla (timeout, cuota), devuelve SAFE
            para no bloquear el sistema (fail-open en errores de infraestructura)
        \"\"\"
        try:
            request = ShieldPromptOptions(user_prompt=text)
            response = self._cs_client.shield_prompt(request)

            analysis = response.user_prompt_analysis
            if analysis and analysis.attack_detected:
                event = SecurityEvent(
                    threat_type=ThreatType.JAILBREAK,
                    threat_level=ThreatLevel.HIGH,
                    user_input=text[:200],
                    detected_pattern="Azure Content Safety: ataque detectado",
                    message="Prompt Shield ML detectó ataque adversarial"
                )
                self._log_threat_event(event)
                return ValidationResult(
                    is_safe=False,
                    threat_level=ThreatLevel.HIGH,
                    threat_type=ThreatType.JAILBREAK,
                    message="Consulta bloqueada por Azure AI Content Safety",
                    event=event,
                    confidence=0.95
                )

            SECURITY_LOGGER.debug(
                "✅ Azure Content Safety: sin ataques detectados"
            )
            return ValidationResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                message="Azure Content Safety: input seguro"
            )

        except Exception as e:
            # Fail-open: si Azure falla, no bloqueamos el sistema
            # El regex de Capa 1 ya filtró los ataques obvios
            SECURITY_LOGGER.warning(
                f"⚠️ Azure Content Safety error (usando solo regex): {e}"
            )
            return ValidationResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                message="Azure Content Safety no disponible — usando regex"
            )

============================================================
FIN DEL UPGRADE
Una vez aplicados los 4 pasos:
1. pip install azure-ai-contentsafety
2. Crear recurso en Azure Portal
3. Agregar CONTENT_SAFETY_ENDPOINT y CONTENT_SAFETY_KEY al .env
4. Cambiar CONTENT_SAFETY_ENABLED=true en .env
5. Reiniciar el servidor — ver en logs: "✅ Azure Content Safety activado"
============================================================
"""

# Este archivo es solo documentación — no se importa ni ejecuta.
# Los fragmentos de código de arriba se copian manualmente
# en src/backend/security/prompt_shields.py cuando se quiera activar.
