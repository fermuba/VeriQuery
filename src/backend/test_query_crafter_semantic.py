#!/usr/bin/env python3
"""
Test del Query Crafter con Mapeo Semántico
===========================================

Valida que el QueryCrafter genera SQL correcto usando:
1. Mapeo semántico (beneficiarios → Dim_Beneficiario)
2. Schema dinámico de Contoso Social
3. Azure OpenAI con temperatura baja
"""

import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.query_crafter import QueryCrafter

load_dotenv()

def main():
    """Test principal"""
    
    print("\n" + "=" * 80)
    print("TEST: QUERY CRAFTER CON MAPEO SEMÁNTICO")
    print("=" * 80 + "\n")
    
    # Configurar Azure OpenAI
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        print("✅ Cliente Azure OpenAI inicializado\n")
    except Exception as e:
        print(f"❌ Error inicializando Azure OpenAI: {e}")
        return False
    
    # Configurar connection string
    conn_string = os.getenv("DATABASE_URL")
    
    if not conn_string:
        print("❌ DATABASE_URL no configurada en .env")
        return False
    
    print(f"📊 Conexión: {conn_string[:50]}...\n")
    
    # Crear Query Crafter
    print("🔄 Inicializando QueryCrafter...")
    try:
        crafter = QueryCrafter(conn_string, client)
        print("✅ QueryCrafter inicializado\n")
    except Exception as e:
        print(f"❌ Error inicializando QueryCrafter: {e}")
        return False
    
    # Test queries con mapeo semántico
    test_questions = [
        "¿Cuántos beneficiarios tenemos?",
        "¿Cuántas asistencias este mes?",
        "¿Beneficiarios por zona?",
        "¿Qué tipos de ayuda se entregan más?",
        "¿Cuántas familias de la Zona Norte recibieron alimentos?",
    ]
    
    passed = 0
    failed = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"📝 QUERY {i}: {question}")
        print('='*80)
        
        try:
            result = crafter.generate_sql(question)
            
            if "error" in result:
                print(f"❌ ERROR: {result['error']}")
                failed += 1
            else:
                sql = result["sql"]
                tables = result.get("tables_used", [])
                tokens = result.get("tokens", 0)
                cost = result.get("cost_usd", 0)
                
                print(f"\n✅ SQL GENERADA:")
                print(f"{sql}\n")
                print(f"📊 Metadata:")
                print(f"  • Tablas usadas: {', '.join(tables) if tables else 'ninguna'}")
                print(f"  • Tokens: {tokens}")
                print(f"  • Costo: ${cost:.6f}")
                
                passed += 1
        
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            failed += 1
    
    # Resumen
    print(f"\n\n{'='*80}")
    print(f"📊 RESULTADOS FINALES")
    print('='*80)
    print(f"✅ Queries exitosas: {passed}")
    print(f"❌ Queries fallidas: {failed}")
    print(f"Total: {passed + failed}")
    print('='*80 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
