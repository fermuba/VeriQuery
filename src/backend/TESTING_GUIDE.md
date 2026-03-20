# 🧪 Testing Guide - Semantic Mapping

## IMPORTANTE: Conservar Créditos de Azure

Este documento describe cómo probar el sistema SIN consumir créditos de Azure OpenAI innecesariamente.

---

## ✅ Testing Local (SIN Costo)

```bash
# Test 1: Verificar que semantic mapping está implementado
python -c "from table_mapping import SEMANTIC_MAPPING; print(f'✅ {len(SEMANTIC_MAPPING)} conceptos mapeados')"

# Test 2: Verificar mapeos específicos
python -c "
from table_mapping import map_domain_concept_to_table
tests = ['beneficiarios', 'asistencias', 'productos', 'zona']
for t in tests:
    result = map_domain_concept_to_table(t)
    print(f'{t} → {result}')
"

# Test 3: Verificar que el prompt está enriquecido
grep -n "MAPEO SEMÁNTICO" nl2sql_generator.py
```

**Resultado esperado:**
```
✅ 50+ conceptos mapeados
beneficiarios → Customer
asistencias → Orders
productos → Product
zona → Customer
MAPEO SEMÁNTICO aparece en nl2sql_generator.py
```

---

## 🚀 Testing en Producción (USA CRÉDITOS)

Usar SOLO cuando:
- ✅ Necesites validar comportamiento real
- ✅ Hayas pasado todos los tests locales
- ✅ Estés listo para demostración final

### Opción 1: Una sola query de prueba
```bash
# Ejecutar directamente en Python REPL
python

from nl2sql_generator import NL2SQLGenerator
gen = NL2SQLGenerator()

# UNA query para validar
result = gen.generate_sql("¿Cuántos beneficiarios tenemos?")
print(f"SQL generada:\n{result['sql']}")
print(f"Tablas usadas: {result['tables_used']}")
print(f"Válida: {result['valid']}")

exit()
```

### Opción 2: Test integrado con FastAPI
```bash
# Con el backend corriendo en puerto 8888
curl http://localhost:8888/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuántos beneficiarios?"}'
```

---

## 📊 Queries Recomendadas para Probar

Una vez que tengas creditos para gastar:

1. **Simple mapping:**
   - "¿Cuántos beneficiarios tenemos?"
   - Expected: `SELECT COUNT(DISTINCT CustomerKey) FROM Customer`

2. **Con filtro geográfico:**
   - "¿Cuántos beneficiarios en Nueva York?"
   - Expected: JOIN con Customer WHERE City = 'New York'

3. **JOIN complejo:**
   - "¿Qué productos se entregaron más?"
   - Expected: JOIN Product + Orders + OrderRows

4. **Temporal:**
   - "¿Cuántas asistencias este mes?"
   - Expected: SELECT COUNT(*) FROM Orders WHERE MONTH(OrderDate) = ...

---

## 🎯 Validar Sin Llamar a Azure

**Checklist de verificación sin consumir créditos:**

- [ ] `table_mapping.py` existe y tiene SEMANTIC_MAPPING
- [ ] `nl2sql_generator.py` incluye "MAPEO SEMÁNTICO" en el prompt (línea ~130)
- [ ] `test_semantic_mapping.py` pasó todos los tests ✅
- [ ] 50+ conceptos mapeados (beneficiarios, asistencias, etc.)
- [ ] 20+ columnas semánticas mapeadas

**Si todo esto ✅, el sistema está listo.**

---

## 💰 Presupuesto Estimado de Créditos

Por query a gpt-4o-mini (con semantic mapping):
- **~0.0003 USD por query** (basado en token count observado: ~1,940 tokens)

Para 5 queries de prueba:
- **~0.0015 USD** (1.5 centavos)

Para 100 queries de demostración:
- **~0.03 USD** (3 centavos)

---

## 🚨 Si Necesitas Revisar Prompts Sin Llamar a Azure

```bash
# Ver el prompt que se envía a Azure (SIN hacer la llamada)
python -c "
from src.backend.core.schema import get_schema_prompt
print(get_schema_prompt()[:500])
"

# Ver el system prompt con semantic mapping
grep -A 30 'MAPEO SEMÁNTICO' nl2sql_generator.py
```

---

## ✅ Estado Actual

- ✅ **Semantic Mapping:** 100% implementado
- ✅ **Test Local:** 100% pasado (sin Azure)
- ✅ **Integración:** Lista en nl2sql_generator.py
- ✅ **Documentación:** Este archivo

**Próximo paso:** Decidir cuándo ejecutar queries reales (cuando sea necesario para hackathon)
