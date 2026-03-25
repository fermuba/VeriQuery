import pytest
from src.backend.agents.sql_normalizer import SQLNormalizer

def test_transpile_postgres_limit_to_tsql_top():
    normalizer = SQLNormalizer()
    sql_llm = "SELECT id FROM users LIMIT 10"
    
    result = normalizer.normalize(sql_llm, dialect_db_type="sqlserver")
    assert result["success"] is True
    assert result["target_dialect"] == "tsql"
    # sqlglot formats "TOP 10" correctly for sqlserver
    assert "TOP 10" in result["normalized_sql"].upper()
    assert "LIMIT" not in result["normalized_sql"].upper()

def test_transpile_tsql_top_to_postgres_limit():
    normalizer = SQLNormalizer()
    sql_llm = "SELECT TOP 5 name FROM [clients]"
    
    result = normalizer.normalize(sql_llm, dialect_db_type="postgresql")
    assert result["success"] is True
    assert result["target_dialect"] == "postgres"
    assert "LIMIT 5" in result["normalized_sql"].upper()
    assert "TOP" not in result["normalized_sql"].upper()

def test_parse_error_returns_false():
    normalizer = SQLNormalizer()
    sql_llm = "SELECT FROM WHERE" # clearly broken syntax
    
    result = normalizer.normalize(sql_llm, dialect_db_type="sqlserver")
    assert result["success"] is False
    assert "error" in result
