import os

class LynisReport:
    def __init__(self, report_file_or_content):
        self.keys = {}
        self.report = self.read_report(report_file_or_content)
        self.keys = self.parse_report()

    def read_report(self, report_file_or_content):
        """Read the report from a file or direct content."""
        if os.path.exists(report_file_or_content):
            with open(report_file_or_content, 'r') as file:
                return file.read()
        return report_file_or_content

    def get_full_report(self):
        """Return the full report content."""
        return self.report

    def parse_report(self):
        """Parse the report and count warnings and suggestions."""
        parsed_keys = {}
        
        for line in self.report.split('\n'):
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            
            # Check if the key indicates a list type (contains '[]')
            if '[]' in key:
                base_key = key.replace('[]', '')
                if base_key not in parsed_keys:
                    parsed_keys[base_key] = []
                parsed_keys[base_key].append(value)
            else:
                parsed_keys[key] = value
        
        # Optionally, you can count the warnings and suggestions if needed
        parsed_keys['count_warnings'] = len(parsed_keys.get('warning', []))
        parsed_keys['count_suggestions'] = len(parsed_keys.get('suggestion', []))
        
        return parsed_keys
    
    def get(self, key):
        """Get the value of a specific key."""
        return self.keys.get(key)
