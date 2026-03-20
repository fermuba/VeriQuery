#!/usr/bin/env python3
"""
Test del Query Crafter
Valida que genera SQL correcto para Contoso Social
"""

import sys
import os

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.query_crafter import QueryCrafter
from dotenv import load_dotenv

load_dotenv()

def test_query_crafter():
    """Test del QueryCrafter"""
    
    print("\n" + "="*70)
    print("TEST: QUERY CRAFTER - CONTOSO SOCIAL")
    print("="*70 + "\n")
    
    # Conexión a SQL Server
    connection_string = (
        f"Driver={{ODBC Driver 17 for SQL Server}};"
        f"Server=localhost,1433;"
        f"Database=ContosoSocial;"
        f"UID=sa;"
        f"PWD=Admin@1234"
    )
    
    print("🔄 Inicializando QueryCrafter...")
    
    try:
        crafter = QueryCrafter(connection_string)
        print("✅ QueryCrafter inicializado\n")
    except Exception as e:
        print(f"❌ Error inicializando: {e}")
        return False
    
    # Test queries
    test_cases = [
        "¿Cuántos beneficiarios tenemos?",
        "¿Cuántas asistencias este mes?",
        "¿Qué tipos de asistencia hay más?",
        "¿Cuáles son los beneficiarios por zona?",
    ]
    
    passed = 0
    failed = 0
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n📌 TEST {i}: {question}")
        print("-" * 70)
        
        try:
            result = crafter.generate_sql(question)
            
            if "error" in result:
                print(f"❌ FAIL - {result['error']}")
                failed += 1
            else:
                sql = result["sql"]
                tables = result.get("tables_used", [])
                
                print(f"✅ PASS")
                print(f"   Tablas: {', '.join(tables) if tables else 'ninguna'}")
                print(f"   SQL: {sql[:100]}...")
                print(f"   Tokens: {result['tokens']}, Costo: ${result['cost_usd']:.6f}")
                passed += 1
        
        except Exception as e:
            print(f"❌ EXCEPTION - {str(e)[:80]}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTADOS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = test_query_crafter()
    sys.exit(0 if success else 1)
