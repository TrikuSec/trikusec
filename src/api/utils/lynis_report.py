import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any

from django.utils import timezone

class LynisReport:
    """
    Class to represent a Lynis report.

    = About Lynis Reports =

    Lynis report 1.0 is formatted as key-value pairs separated by '=', each pair on a new line.

    Example:

    # Lynis Report
    report_version_major=1
    report_version_minor=0
    linux_version=Ubuntu

    == Keys ==

    The report contains the following types of keys:
    - Single key-value pairs
    - List key-value pairs (indicated by '[]' in the key)
    - Comments (lines starting with '#')

    == Values ==
    
    The value can be a simple value or a delimiter-separated value ('|' or ',').
    """

    class LynisData:
        """
        Class to represent a Lynis value string, present in list key-value pairs.

        The following types are supported:
        - Single value
        - Multiple values delimited by '|' or by ','

        This class will parse the raw string and return a list of lists containing the values.
        """
        class SimpleValue:
            def __init__(self, raw_value: str):
                self.value = raw_value

            def get (self) -> str:
                return self.value

        class SimpleList:
            def __init__(self, raw_value: str, delimiter: str = '|'):
                self.raw_value = raw_value
                self.delimiter = delimiter
                self.values = self._parse_values()
                self.values = self._remove_empty_values()

            def _parse_values(self) -> List[str]:
                return self.raw_value.split(self.delimiter)
            
            def _remove_empty_values(self) -> List[str]:
                # Remove empty values or values with only '-' character or whitespaces
                return [value.strip() for value in self.values if value and value.strip() not in ['-', '']]
            
            def get(self) -> List[str]:
                return self.values
            
        def __init__(self, raw_value: str):
            self.raw_value = raw_value
            # Detect the type of value and assign the correct class
            if '|' in raw_value:
                self.value = self.SimpleList(raw_value, '|')
            elif ',' in raw_value:
                self.value = self.SimpleList(raw_value, ',')
            else:
                self.value = self.SimpleValue(raw_value)
            
        def get(self) -> Any:
            return self.value.get()


    def __init__(self, full_report: str):
        self.report = full_report
        self.keys = {}

        try:
            self.report = self._clean_full_report()
            self.keys = self._parse_report()
            self._generate_custom_variables()
        except Exception as e:
            logging.error(f'Error initializing LynisReport: {e}')
    
    def compare_reports(self, new_report_str: str, ignore_keys: List[str] = []) -> Dict[str, Any]:
        """
        Compare current report with new report, return structured changes.
        
        :param new_report_str: Raw report string to compare against
        :param ignore_keys: List of keys to ignore in comparison
        :return: Dict with 'added', 'removed', and 'changed' keys
        """
        new_report = LynisReport(new_report_str)
        old_keys = self.keys
        new_keys = new_report.keys
        
        changes = {'added': {}, 'removed': {}, 'changed': []}
        
        all_keys = set(old_keys.keys()) | set(new_keys.keys())
        
        for key in all_keys:
            if key in ignore_keys:
                continue
                
            old_val = old_keys.get(key)
            new_val = new_keys.get(key)
            
            # Serialize datetime objects to string for JSON compatibility
            if isinstance(old_val, datetime):
                old_val = old_val.isoformat()
            if isinstance(new_val, datetime):
                new_val = new_val.isoformat()
            
            if old_val is None and new_val is not None:
                changes['added'][key] = new_val
            elif old_val is not None and new_val is None:
                changes['removed'][key] = old_val
            elif old_val != new_val:
                changes['changed'].append({key: {'old': old_val, 'new': new_val}})
        
        logging.debug('Compared reports: %s changes found', len(changes['added']) + len(changes['removed']) + len(changes['changed']))
        return changes
    
    def apply_diff(self, diff: str) -> str:
        """
        Apply a diff to a Lynis report
        :param diff: diff string
        :return: patched report
        """
        logging.debug('Original report size: %d bytes', len(self.get_full_report()))
        logging.debug('Diff size: %d bytes', len(diff))

        original_lines = self.get_full_report().splitlines(keepends=True)
        diff_lines = diff.splitlines(keepends=True)

        # Combine original lines and diff lines
        full_diff = list(difflib.unified_diff(original_lines, original_lines)) + diff_lines

        # Apply the full diff to reconstruct the report
        patched_lines = list(difflib.restore(full_diff, 1))
        return ''.join(patched_lines)

    def _clean_full_report(self) -> str:
        """
        Clean invalid keys from the report
        - Remove invalid tests from the report (deprecated or not relevant)
        More info: https://cisofy.com/lynis/controls/
        """
        invalid_tests = ['DEB-0280', 'DEB-0285', 'DEB-0520', 'DEB-0870', 'DEB-0880']

        # Remove lines with invalid tests
        report_lines = self.report.split('\n')
        cleaned_lines = [line for line in report_lines if not any(test in line for test in invalid_tests)]
        return '\n'.join(cleaned_lines)

    def get_full_report(self) -> str:
        """Return the full report content."""
        return self.report

    def _parse_report(self) -> Dict[str, Any]:
        """Parse the report"""
        parsed_keys = {}
        
        for line in self.report.split('\n'):
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            # Parse the value using the LynisData class
            value = self.LynisData(value).get()
            
            # Check if the key indicates a list type (contains '[]')
            if '[]' in key:
                base_key = key.replace('[]', '')
                if base_key not in parsed_keys:
                    parsed_keys[base_key] = []
                parsed_keys[base_key].append(value)
            else:
                # Convert numeric strings to integers for proper JMESPath comparisons
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                parsed_keys[key] = value
        
        return parsed_keys

    def _generate_custom_variables(self) -> None:
        """Add custom variables to the report."""

        # Generate count variables
        count_keys = self._generate_count_variables()
        for key, value in count_keys.items():
            self.set(key, value)
        
        # Generate filtered IPv4 addresses
        # The one(s) connected to the default gateway(s)
        self.set('primary_ipv4_addresses', self._get_filtered_ipv4_addresses())
        
        # Extract primary MAC address (corresponding to primary IP on gateway network)
        self.set('primary_mac_address', self._get_primary_mac_address())

        # Parse and store report_datetime_end as datetime object (timezone-aware)
        raw_datetime_end = self.get('report_datetime_end')
        if raw_datetime_end:
            parsed_datetime = self._parse_report_datetime(raw_datetime_end)
            if parsed_datetime:
                self.set('report_datetime_end', parsed_datetime)

        # Generate dynamic audit timing helper
        self._add_days_since_audit_variable()
        
        # Generate installed package names list for easier rule evaluation
        self._generate_installed_package_names()

    def get_parsed_report(self) -> Dict[str, Any]:
        """Return the parsed report."""
        return self.keys

    def _generate_count_variables(self) -> Dict[str, int]:
        """Generate count variables for lists."""
        
        count_keys = {}
        for key, value in self.keys.items():
            if isinstance(value, list):
                count_keys[f'{key}_count'] = len(value)
                #logging.debug(f'Generated count key: {key}_count with value: {len(value)}')
        #self.keys.update(count_keys)
        return count_keys
    
    def get(self, key: str) -> Any:
        """Get the value of a specific key."""
        return self.keys.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set the value of a specific key."""
        self.keys[key] = value
    
    def _get_filtered_ipv4_addresses(self) -> List[str]:
        """Filter IPv4 addresses connected to default gateway(s)"""
        default_gateways = self.get('default_gateway')
        ipv4_addresses = self.get('network_ipv4_address')
        filtered_addresses = []

        if not ipv4_addresses:
            return ['-']

        # If default_gateways is empty return all network_ipv4_addresses
        if not default_gateways:
            return ipv4_addresses

        for default_gateway in default_gateways:
            # We assume network prefix is /24
            # Example: default gateway 192.168.1.1
            # network prefix: 192.168.1
            gateway_network_prefix = '.'.join(default_gateway.split('.')[:3])
            for ipv4_address in ipv4_addresses:
                if gateway_network_prefix in ipv4_address:
                    filtered_addresses.append(ipv4_address)
        # Convert list to string
        logging.debug(f'Filtered IPv4 addresses: {filtered_addresses}')
        return filtered_addresses

    def _get_primary_mac_address(self) -> str:
        """
        Get the MAC address corresponding to the primary IP address (on gateway network).
        
        The MAC address arrays are parallel to IP address arrays in Lynis reports.
        We find the primary IP (on gateway network) and return its corresponding MAC.
        """
        mac_addresses = self.get('network_mac_address')
        ipv4_addresses = self.get('network_ipv4_address')
        primary_ips = self.get('primary_ipv4_addresses')
        
        if not mac_addresses or not isinstance(mac_addresses, list) or len(mac_addresses) == 0:
            return None
        
        if not ipv4_addresses or not isinstance(ipv4_addresses, list) or len(ipv4_addresses) == 0:
            return None
        
        if not primary_ips or primary_ips == ['-']:
            # No primary IP found, return first non-loopback MAC if available
            # Skip loopback interface (usually first)
            for i, mac in enumerate(mac_addresses):
                if i < len(ipv4_addresses):
                    ip = ipv4_addresses[i]
                    # Skip loopback addresses
                    if ip and ip != '127.0.0.1' and not ip.startswith('127.'):
                        return mac
            # Fallback to first MAC if no non-loopback found
            return mac_addresses[0] if mac_addresses else None
        
        # Find the index of the primary IP in the IP addresses array
        # Use the first primary IP if multiple exist
        primary_ip = primary_ips[0] if isinstance(primary_ips, list) else primary_ips
        
        try:
            ip_index = ipv4_addresses.index(primary_ip)
            # Return MAC at the same index
            if ip_index < len(mac_addresses):
                mac = mac_addresses[ip_index]
                logging.debug(f'Primary MAC address: {mac} (for IP {primary_ip})')
                return mac
        except ValueError:
            # Primary IP not found in IP addresses array (shouldn't happen)
            logging.warning(f'Primary IP {primary_ip} not found in network_ipv4_address array')
        
        # Fallback: return first non-loopback MAC
        for i, mac in enumerate(mac_addresses):
            if i < len(ipv4_addresses):
                ip = ipv4_addresses[i]
                if ip and ip != '127.0.0.1' and not ip.startswith('127.'):
                    return mac
        
        return mac_addresses[0] if mac_addresses else None

    def _add_days_since_audit_variable(self) -> None:
        """Add days_since_audit key calculated from report_datetime_end."""
        report_end = self.get('report_datetime_end')
        if not report_end:
            self.set('days_since_audit', None)
            return

        parsed_end = self._parse_report_datetime(report_end)

        if not parsed_end:
            self.set('days_since_audit', None)
            return

        now = timezone.now()

        # If parsed_end is naive, assume current timezone
        if timezone.is_naive(parsed_end):
            parsed_end = timezone.make_aware(parsed_end, timezone.get_current_timezone())

        diff = now - parsed_end
        # Prevent negative values if report is from the future (clock skew)
        days = diff.days
        if diff.total_seconds() < 0:
            days = 0
        self.set('days_since_audit', days)

    def _parse_report_datetime(self, value: Any) -> Any:
        """Parse report datetime strings into datetime objects."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return None
            # Normalize trailing Z to +00:00 to support ISO 8601
            if candidate.endswith('Z'):
                candidate = candidate[:-1] + '+00:00'
            try:
                parsed_datetime = datetime.fromisoformat(candidate)
            except ValueError:
                # Fallback to common Lynis format (space separated)
                try:
                    parsed_datetime = datetime.strptime(candidate, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    logging.debug('Unable to parse report_datetime_end value: %s', value)
                    return None
            
            # Make timezone-aware if naive
            if timezone.is_naive(parsed_datetime):
                parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
            
            return parsed_datetime

        logging.debug('Unsupported report_datetime_end type: %s', type(value))
        return None

    def _generate_installed_package_names(self) -> None:
        """
        Generate a flat list of installed package names for easier rule evaluation.
        
        The installed_packages_array contains strings like 'package_name,version'
        (e.g., 'fail2ban,0.11.1-1', 'apache2,2.4.41-4ubuntu3.23').
        
        This method creates installed_package_names as a simple list of package names:
        ['fail2ban', 'apache2', ...]
        
        This allows simpler policy rules like:
            contains(installed_package_names, 'fail2ban')
        
        Instead of the more complex:
            installed_packages_array[?starts_with(@, 'fail2ban,')] | length(@) > `0`
        """
        packages_array = self.get('installed_packages_array')
        if not packages_array:
            self.set('installed_package_names', [])
            return
        
        package_names = []
        for entry in packages_array:
            if isinstance(entry, str) and ',' in entry:
                # Entry is 'package_name,version', extract package name
                package_name = entry.split(',', 1)[0]
                package_names.append(package_name)
            elif isinstance(entry, str):
                # Entry is a simple string (no version), use as-is
                package_names.append(entry)
        
        self.set('installed_package_names', package_names)
        logging.debug(f'Generated installed_package_names with {len(package_names)} entries')

