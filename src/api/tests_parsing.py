import pytest
from api.utils.lynis_report import LynisReport
from api.utils.policy_query import evaluate_query

class TestLynisReportParsing:
    """Tests for LynisReport parsing logic."""

    def test_parse_list_with_brackets_and_commas(self):
        """
        Test that fields with brackets (array) containing comma-separated values
        are flattened into a single list, not a list of lists.
        
        Regression test for issue where installed_packages_array[]=a,b,c became [['a', 'b', 'c']]
        instead of ['a', 'b', 'c'].
        """
        report_data = """
installed_packages_array[]=pkg1,1.0,fail2ban,0.11,pkg3,2.0
simple_list[]=item1
simple_list[]=item2
mixed_list[]=item3
mixed_list[]=item4,item5
        """.strip()
        
        report = LynisReport(report_data)
        parsed = report.get_parsed_report()
        
        # Verify installed_packages_array is a flat list
        assert isinstance(parsed['installed_packages_array'], list)
        assert len(parsed['installed_packages_array']) == 6
        assert parsed['installed_packages_array'][0] == 'pkg1'
        assert 'fail2ban' in parsed['installed_packages_array']
        
        # Verify evaluate_query works correctly on this flat list
        assert evaluate_query(parsed, "contains(installed_packages_array, 'fail2ban')") is True
        assert evaluate_query(parsed, "contains(installed_packages_array, 'pkg1')") is True
        assert evaluate_query(parsed, "contains(installed_packages_array, 'nonexistent')") is False

        # Verify simple lists still work
        assert len(parsed['simple_list']) == 2
        assert parsed['simple_list'] == ['item1', 'item2']
        
        # Verify mixed lists (single + comma-separated) are flattened correctly
        assert len(parsed['mixed_list']) == 3
        assert parsed['mixed_list'] == ['item3', 'item4', 'item5']

