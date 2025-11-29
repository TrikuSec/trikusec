
import pytest
from django.utils import timezone
from datetime import datetime, timedelta
from api.utils.lynis_report import LynisReport

class TestTimezoneIssue:
    def test_future_report_time_reproduction(self):
        """
        Reproduce the issue where a report with local time (e.g. CET) is interpreted as UTC,
        resulting in a future timestamp.
        """
        # 1. Setup: Assume Server is UTC (standard Django setting)
        # and current time is T.
        now_utc = timezone.now()
        
        # 2. Simulate a device in CET (UTC+1) sending a report.
        # If it's 12:00 UTC, it's 13:00 CET.
        # The device writes "2023-XX-XX 13:00:00" (naive) in the report.
        cet_offset = timedelta(hours=1)
        device_time_cet = now_utc + cet_offset
        naive_report_time_str = device_time_cet.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\nReal UTC Now: {now_utc}")
        print(f"Device Report Time (CET, Naive): {naive_report_time_str}")
        
        # 3. Parse the report
        report_content = f"report_datetime_end={naive_report_time_str}"
        report = LynisReport(report_content)
        parsed_dt = report.get('report_datetime_end')
        
        print(f"Parsed Datetime (Server interpreted): {parsed_dt}")
        
        # 4. Verification
        # The parsed time should be treated as UTC by default if naive.
        # So "13:00" becomes "13:00 UTC".
        # "13:00 UTC" is 1 hour ahead of "12:00 UTC" (Real Now).
        # So parsed_dt > now_utc
        
        # We expect this to PASS now that the fix is implemented.
        # The timestamp should be clamped to now_utc (or very close to it).
        
        # Allow a small delta for execution time (e.g. 1 second)
        time_diff = parsed_dt - now_utc
        print(f"Time Difference (parsed - now): {time_diff}")
        
        assert parsed_dt <= now_utc + timedelta(seconds=1), "Fix Failed: Parsed time is still significantly in the future!"
        
        # It should be clamped to "now", so it shouldn't be too far in the past either 
        # (unless "now" moved forward significantly during execution)
        assert parsed_dt >= now_utc - timedelta(seconds=5), "Fix Failed: Parsed time is too far in the past (clamping error?)"
        
        print("SUCCESS: Future timestamp was clamped to server time.")

