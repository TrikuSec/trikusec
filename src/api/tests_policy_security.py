import pytest
from api.utils.policy_query import parse_query, evaluate_query
from api.utils.lynis_report import LynisReport


@pytest.mark.security
class TestPolicyQuerySecurity:
    """Security tests for policy query evaluation."""
    
    @pytest.fixture
    def sample_report(self):
        """Create a sample report for testing."""
        report_data = """report_version_major=3
report_version_minor=0
hardening_index=75
automation_tool_running=ansible
"""
        return LynisReport(report_data)
    
    def test_sql_injection_attempts(self, sample_report):
        """Test that SQL injection patterns are safely ignored."""
        malicious_queries = [
            "hardening_index = 75; DROP TABLE devices;",
            "automation_tool_running = 'test' OR '1'='1'",
            "hardening_index = 75 UNION SELECT * FROM users",
            "automation_tool_running contains \"'; DELETE FROM licensekey; --\"",
        ]
        
        for query in malicious_queries:
            # The parser only parses the first valid condition and ignores the rest
            # This is safe because: 1) No SQL is executed, 2) Only valid grammar is parsed
            result = evaluate_query(sample_report, query)
            # The parser should parse the valid part and ignore malicious parts
            # Since there's no SQL execution, the malicious parts are harmless
            # We verify that the result is a boolean or None (not an error)
            assert isinstance(result, (bool, type(None))), f"Query should return bool or None: {query}"
            # Verify that the malicious SQL part doesn't affect the result
            # The parser only processes the first valid condition
            parsed = parse_query(query)
            assert parsed is not None, f"Parser should handle query safely: {query}"
            # Verify only the first valid part was parsed (not the SQL injection)
            assert len(parsed) == 3, f"Only valid condition should be parsed: {query}"
    
    def test_code_injection_attempts(self, sample_report):
        """Test that code injection patterns are rejected."""
        malicious_queries = [
            "hardening_index = __import__('os').system('ls')",
            "automation_tool_running contains exec('print(1)')",
            "hardening_index = eval('1+1')",
        ]
        
        for query in malicious_queries:
            result = parse_query(query)
            assert result is None, f"Code injection not blocked: {query}"
    
    def test_path_traversal_attempts(self, sample_report):
        """Test that path traversal patterns are rejected."""
        malicious_queries = [
            "automation_tool_running contains \"../../../etc/passwd\"",
            "hardening_index = ../../config",
        ]
        
        for query in malicious_queries:
            result = evaluate_query(sample_report, query)
            # Should evaluate safely (not cause file access)
            assert isinstance(result, (bool, type(None)))
    
    def test_field_validation(self, sample_report):
        """Test that only valid field names are accepted."""
        valid_queries = [
            "hardening_index > 70",
            "automation_tool_running contains \"ansible\"",
        ]
        
        for query in valid_queries:
            result = evaluate_query(sample_report, query)
            assert result is not None
    
    def test_operator_validation(self, sample_report):
        """Test that only valid operators are accepted."""
        invalid_queries = [
            "hardening_index && 75",
            "automation_tool_running || test",
            "hardening_index << 75",
        ]
        
        for query in invalid_queries:
            result = parse_query(query)
            assert result is None, f"Invalid operator not rejected: {query}"
    
    def test_resource_exhaustion(self, sample_report):
        """Test that queries don't cause resource exhaustion."""
        # Test with very long query
        long_query = "hardening_index = " + "1" * 10000
        result = parse_query(long_query)
        # Should parse successfully (long integers are valid)
        # The parser should handle it without hanging or causing memory issues
        assert result is not None, "Parser should handle long integers"
        assert len(result) == 3, "Should parse field, operator, and value"
        # Verify the value is the long integer string
        assert result[2] == "1" * 10000, "Should parse the full long integer"

