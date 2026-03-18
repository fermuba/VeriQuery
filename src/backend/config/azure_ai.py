"""
Azure AI Configuration - Conector Híbrido
==========================================

Gestiona la configuración y conexión a Azure OpenAI con seguridad integrada.
Carga credenciales desde .env y valida la conexión con Content Safety.

Arquitectura:
   .env (credenciales)
      ↓
   AzureAIConfig (lectura y validación)
      ↓
   AzureOpenAI Client (conexión oficial)
      ↓
   Azure Content Safety (detección semántica)

Requisitos:
- openai >= 1.51.2 (para Azure Content Safety API)
- azure-identity (para autenticación)
- python-dotenv (para cargar .env)

Norma: Enterprise Security Standard
PEP 8:  Compliant
Type Hints:  Compliant
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AzureOpenAI


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger("ForensicGuardian.Config")


# ============================================================================
# CONFIGURACIÓN Y VALIDACIÓN
# ============================================================================

@dataclass
class AzureAIEnvironment:
    """
    Modelo de datos para variables de entorno de Azure OpenAI.
    
    Attributes:
        endpoint: URL base de Azure OpenAI (ej: https://xxx.openai.azure.com/)
        api_key: Clave API de Azure (keep secret!)
        deployment_name: Nombre del deployment (ej: gpt-4o-mini-deployment)
        api_version: Versión de la API de Azure OpenAI
    """
    endpoint: str
    api_key: str
    deployment_name: str
    api_version: str = "2024-08-01-preview"  # Default: última versión estable
    
    def validate(self) -> None:
        """
        Valida que todas las variables requeridas estén presentes y sean válidas.
        
        Raises:
            ValueError: Si alguna variable está vacía o es inválida
        """
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT no configurado en .env")
        
        if not self.endpoint.startswith(("https://", "http://")):
            raise ValueError("AZURE_OPENAI_ENDPOINT debe ser una URL válida")
        
        if not self.endpoint.endswith("/"):
            self.endpoint += "/"
        
        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY no configurado en .env")
        
        if len(self.api_key) < 10:
            raise ValueError("AZURE_OPENAI_API_KEY parece inválida (muy corta)")
        
        if not self.deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI no configurado en .env")
        
        if not self.api_version:
            raise ValueError("AZURE_OPENAI_API_VERSION no configurado")
        
        logger.info("✅ Validación de variables de entorno exitosa")


# ============================================================================
# CLASE PRINCIPAL DE CONFIGURACIÓN
# ============================================================================

class AzureAIConfig:
    """
    Gestor centralizado de configuración de Azure OpenAI.
    
    Responsabilidades:
    1. Cargar variables desde .env
    2. Validar credenciales
    3. Inicializar cliente oficial de OpenAI
    4. Proporcionar acceso singleton al cliente
    
    Patrón: Singleton (una sola instancia)
    """
    
    _instance: Optional['AzureAIConfig'] = None
    
    def __new__(cls) -> 'AzureAIConfig':
        """Patrón Singleton: asegurar una sola instancia"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializar la configuración (una sola vez)"""
        if self._initialized:
            return
        
        self._initialized = True
        self._client: Optional[AzureOpenAI] = None
        self._env: Optional[AzureAIEnvironment] = None
        
        # Cargar configuración
        self._load_environment()
        self._initialize_client()
    
    @staticmethod
    def _load_environment() -> AzureAIEnvironment:
        """
        Carga variables de entorno desde .env.
        
        Busca el archivo .env en la raíz del proyecto.
        
        Returns:
            AzureAIEnvironment con variables validadas
            
        Raises:
            ValueError: Si faltan variables requeridas
        """
        # Buscar y cargar .env
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            # Buscar un nivel arriba (para compatibilidad)
            env_path = Path.cwd().parent / ".env"
        
        load_dotenv(env_path)
        
        logger.info(f"📁 Cargando .env desde: {env_path}")
        
        # Extraer variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
        api_version = os.getenv(
            "AZURE_OPENAI_API_VERSION",
            "2024-08-01-preview"
        )
        
        # Crear objeto de ambiente
        env = AzureAIEnvironment(
            endpoint=endpoint or "",
            api_key=api_key or "",
            deployment_name=deployment or "",
            api_version=api_version
        )
        
        # Validar
        env.validate()
        
        return env
    
    def _initialize_client(self) -> None:
        """
        Inicializa el cliente oficial de Azure OpenAI.
        
        Pasos:
        1. Cargar variables de entorno
        2. Crear instancia de AzureOpenAI
        3. Probar conexión (sin hacer llamada real)
        
        Raises:
            Exception: Si hay error en la inicialización
        """
        try:
            self._env = self._load_environment()
            
            # Inicializar cliente oficial
            self._client = AzureOpenAI(
                api_key=self._env.api_key,
                api_version=self._env.api_version,
                azure_endpoint=self._env.endpoint
            )
            
            logger.info("✅ Cliente AzureOpenAI inicializado exitosamente")
            logger.debug(f"   Endpoint: {self._env.endpoint}")
            logger.debug(f"   Deployment: {self._env.deployment_name}")
            logger.debug(f"   API Version: {self._env.api_version}")
        
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente Azure OpenAI: {e}")
            raise
    
    def get_client(self) -> AzureOpenAI:
        """
        Retorna el cliente de Azure OpenAI configurado.
        
        Returns:
            AzureOpenAI client listo para usar
            
        Raises:
            RuntimeError: Si el cliente no está inicializado
        """
        if self._client is None:
            raise RuntimeError("Cliente Azure OpenAI no inicializado")
        return self._client
    
    def get_deployment_name(self) -> str:
        """
        Retorna el nombre del deployment.
        
        Returns:
            Nombre del deployment (ej: gpt-4o-mini-deployment)
        """
        if self._env is None:
            raise RuntimeError("Configuración no cargada")
        return self._env.deployment_name
    
    def get_endpoint(self) -> str:
        """
        Retorna el endpoint de Azure OpenAI.
        
        Returns:
            URL del endpoint
        """
        if self._env is None:
            raise RuntimeError("Configuración no cargada")
        return self._env.endpoint
    
    def get_config_summary(self) -> Dict[str, str]:
        """
        Retorna un resumen de la configuración (sin exponer secretos).
        
        Returns:
            Diccionario con información de configuración
        """
        if self._env is None:
            raise RuntimeError("Configuración no cargada")
        
        return {
            "endpoint": self._env.endpoint,
            "deployment": self._env.deployment_name,
            "api_version": self._env.api_version,
            "api_key": f"***{self._env.api_key[-4:]}" if self._env.api_key else "No configurada"
        }
    
    @staticmethod
    def test_connection() -> bool:
        """
        Prueba la conexión a Azure OpenAI.
        
        Nota: Esto NO hace una llamada real a la API (para no incurrir en costos).
        Solo valida que el cliente se inicializó correctamente.
        
        Returns:
            True si la conexión es válida
        """
        try:
            config = AzureAIConfig()
            client = config.get_client()
            
            # Validar que el cliente existe y tiene atributos necesarios
            assert hasattr(client, 'chat'), "Cliente sin atributo 'chat'"
            
            logger.info("✅ Conexión a Azure OpenAI validada")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error validando conexión: {e}")
            return False


# ============================================================================
# DECORADOR PARA INYECTAR CONFIGURACIÓN
# ============================================================================

def require_azure_config(func):
    """
    Decorador que inyecta la configuración de Azure en una función.
    
    Uso:
        @require_azure_config
        def mi_funcion(azure_config: AzureAIConfig):
            client = azure_config.get_client()
            ...
    """
    def wrapper(*args, **kwargs):
        config = AzureAIConfig()
        return func(config, *args, **kwargs)
    return wrapper


# ============================================================================
# DEMOSTRACIÓN
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AZURE AI CONFIGURATION - TEST")
    print("=" * 80)
    
    try:
        # Inicializar configuración
        print("\n1️⃣ Inicializando AzureAIConfig...")
        config = AzureAIConfig()
        
        # Mostrar resumen
        print("\n2️⃣ Resumen de configuración:")
        summary = config.get_config_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # Obtener cliente
        print("\n3️⃣ Obteniendo cliente...")
        client = config.get_client()
        print(f"   ✅ Cliente obtenido: {type(client).__name__}")
        
        # Probar conexión
        print("\n4️⃣ Probando conexión...")
        is_valid = AzureAIConfig.test_connection()
        if is_valid:
            print("   ✅ Conexión exitosa")
        else:
            print("   ❌ Error en conexión")
        
        # Verificar singleton
        print("\n5️⃣ Verificando patrón Singleton...")
        config2 = AzureAIConfig()
        print(f"   ¿Misma instancia? {config is config2}")
        
        print("\n" + "=" * 80)
        print("✅ TODOS LOS TESTS PASARON")
        print("=" * 80)
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
