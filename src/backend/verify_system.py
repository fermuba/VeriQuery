#!/usr/bin/env python3
"""
Verificación completa del sistema sin consumir créditos de Azure
"""

import sys

def verify_system():
    print('\n' + '='*70)
    print('VERIFICACION COMPLETA DEL SISTEMA (SIN CONSUMIR CREDITOS)')
    print('='*70 + '\n')
    
    # Check 1: table_mapping.py
    print('1. Verificando table_mapping.py...')
    try:
        from table_mapping import (
            SEMANTIC_MAPPING,
            COLUMN_MAPPING,
            map_domain_concept_to_table,
            get_columns_for_concept,
            enrich_system_prompt
        )
        print(f'   OK - SEMANTIC_MAPPING: {len(SEMANTIC_MAPPING)} conceptos')
        print(f'   OK - COLUMN_MAPPING: {len(COLUMN_MAPPING)} conceptos')
        print(f'   OK - Funciones importadas correctamente')
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

    # Check 2: Verify key mappings
    print('\n2. Verificando mapeos clave...')
    critical_mappings = {
        'beneficiarios': 'Customer',
        'asistencias': 'Orders',
        'productos': 'Product',
        'zona': 'Customer'
    }
    all_good = True
    for concept, expected_table in critical_mappings.items():
        actual = map_domain_concept_to_table(concept)
        if actual == expected_table:
            print(f'   OK - {concept:15} -> {actual}')
        else:
            print(f'   ERROR - {concept:15} -> {actual} (esperaba {expected_table})')
            all_good = False

    if not all_good:
        return False

    # Check 3: NL2SQLGenerator
    print('\n3. Verificando nl2sql_generator.py...')
    try:
        from nl2sql_generator import NL2SQLGenerator
        print(f'   OK - NL2SQLGenerator importado')
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

    # Check 4: Verify semantic mapping in prompt
    print('\n4. Verificando que semantic mapping esta en prompt...')
    try:
        with open('nl2sql_generator.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'MAPEO SEMANTICO' in content or 'MAPEO SEMÁNTICO' in content:
                print(f'   OK - MAPEO SEMANTICO encontrado en prompt')
            else:
                print(f'   ERROR - MAPEO SEMANTICO NO ENCONTRADO')
                return False
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

    # Check 5: System prompt enrichment
    print('\n5. Verificando enrich_system_prompt()...')
    try:
        enriched = enrich_system_prompt()
        if 'MAPEO' in enriched.upper() and 'beneficiario' in enriched.lower():
            print(f'   OK - Prompt enriquecido ({len(enriched)} caracteres)')
        else:
            print(f'   ADVERTENCIA - Prompt generado pero sin contenido completo')
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

    print('\n' + '='*70)
    print('OK - TODAS LAS VERIFICACIONES PASARON')
    print('='*70)
    print('\nEstado: Sistema esta listo para pruebas reales con Azure.')
    print('Proximo: Ejecutar test real solo cuando sea critico.')
    return True

if __name__ == '__main__':
    success = verify_system()
    sys.exit(0 if success else 1)
