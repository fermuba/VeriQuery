#!/usr/bin/env python3
"""
Test del Mapeo Semántico

Demuestra cómo el sistema mapea conceptos de negocio a tablas reales.
"""

from table_mapping import (
    SEMANTIC_MAPPING,
    COLUMN_MAPPING,
    map_domain_concept_to_table,
    get_columns_for_concept,
    enrich_system_prompt,
    remap_question,
    log_semantic_mapping,
)


def test_semantic_mapping():
    """Test básico de mapeo semántico"""
    print("=" * 80)
    print("TEST 1: Mapeo de Conceptos → Tablas")
    print("=" * 80)
    
    test_cases = [
        "beneficiarios",
        "familias",
        "asistencias",
        "entregas",
        "productos",
        "zona",
        "barrio",
    ]
    
    for concept in test_cases:
        table = map_domain_concept_to_table(concept)
        print(f"  '{concept}' → '{table}'")
    
    print()


def test_column_mapping():
    """Test de mapeo de columnas"""
    print("=" * 80)
    print("TEST 2: Mapeo de Conceptos → Columnas")
    print("=" * 80)
    
    test_cases = [
        "zona",
        "edad",
        "genero",
        "nombre",
        "fecha",
        "cantidad",
        "precio",
    ]
    
    for concept in test_cases:
        columns = get_columns_for_concept(concept)
        print(f"  '{concept}' → {columns}")
    
    print()


def test_remap_questions():
    """Test de remapeo de preguntas"""
    print("=" * 80)
    print("TEST 3: Remapeo de Preguntas del Usuario")
    print("=" * 80)
    
    questions = [
        "¿Cuántos beneficiarios tenemos?",
        "¿Cuáles son las asistencias del mes?",
        "¿Cuántas familias en la zona norte?",
        "¿Qué productos se entregaron más?",
    ]
    
    for q in questions:
        remapped, mappings = remap_question(q)
        print(f"\n  Original:  {q}")
        print(f"  Remapped:  {remapped}")
        if mappings:
            print(f"  Mapeos:")
            for domain, table in mappings.items():
                print(f"    - '{domain}' → '{table}'")
        else:
            print(f"  Mapeos: (ninguno)")
    
    print()


def test_system_prompt():
    """Mostrar el enriquecimiento del system prompt"""
    print("=" * 80)
    print("TEST 4: System Prompt Enriquecido")
    print("=" * 80)
    
    prompt = enrich_system_prompt()
    print(prompt)
    print()


def test_semantic_examples():
    """Ejemplos prácticos"""
    print("=" * 80)
    print("TEST 5: Ejemplos Prácticos")
    print("=" * 80)
    
    examples = [
        {
            "pregunta": "¿Cuántos beneficiarios hay en Nueva York?",
            "tabla_real": "Customer",
            "explicacion": "Beneficiarios se mapean a Customer, Nueva York es una ubicación"
        },
        {
            "pregunta": "¿Cuántas asistencias este mes?",
            "tabla_real": "Orders",
            "explicacion": "Asistencias se mapean a Orders, fecha en OrderDate"
        },
        {
            "pregunta": "¿Qué productos se entregaron más en Zona Sur?",
            "tabla_real": "Customer + Product + Orders",
            "explicacion": "JOIN entre tablas usando mapeo semántico"
        },
    ]
    
    for i, ex in enumerate(examples, 1):
        print(f"\n  Ejemplo {i}:")
        print(f"    Pregunta: {ex['pregunta']}")
        print(f"    Tabla Real: {ex['tabla_real']}")
        print(f"    Explicación: {ex['explicacion']}")
    
    print()


def show_mappings_stats():
    """Mostrar estadísticas de mapeos"""
    print("=" * 80)
    print("ESTADÍSTICAS")
    print("=" * 80)
    
    print(f"  Total conceptos semánticos mapeados: {len(SEMANTIC_MAPPING)}")
    print(f"  Total columnas mapeadas: {len(COLUMN_MAPPING)}")
    
    # Agrupar por tabla
    table_groups = {}
    for concept, table in SEMANTIC_MAPPING.items():
        if table not in table_groups:
            table_groups[table] = []
        table_groups[table].append(concept)
    
    print(f"\n  Distribución por tabla:")
    for table, concepts in sorted(table_groups.items()):
        print(f"    {table}: {len(concepts)} conceptos")
        print(f"      {', '.join(concepts[:5])}" + ("..." if len(concepts) > 5 else ""))
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  FORENSIC GUARDIAN - SEMANTIC MAPPING TEST".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    test_semantic_mapping()
    test_column_mapping()
    test_remap_questions()
    test_semantic_examples()
    test_system_prompt()
    show_mappings_stats()
    
    print("=" * 80)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 80)
    print()
