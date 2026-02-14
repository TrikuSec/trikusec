from django.core.management.base import BaseCommand
from api.models import Device, FullReport, ComplianceSnapshot, DeviceEvent
from api.utils.lynis_report import LynisReport
from api.utils.compliance import check_device_compliance


class Command(BaseCommand):
    help = 'Backfill ComplianceSnapshot records from existing device data and reports'

    def handle(self, *args, **options):
        devices = Device.objects.all()
        created_count = 0

        for device in devices:
            # Skip if device already has snapshots
            if device.compliance_snapshots.exists():
                self.stdout.write(f'  Skipping {device.hostname or device.hostid} (already has snapshots)')
                continue

            # Try to create snapshots from historical compliance_changed events
            events = (
                DeviceEvent.objects
                .filter(device=device, event_type='compliance_changed')
                .order_by('created_at')
            )
            for event in events:
                new_status = event.metadata.get('new_status', '')
                compliant = new_status == 'Compliant'
                ComplianceSnapshot.objects.create(
                    device=device,
                    compliant=compliant,
                    hardening_index=None,
                    warning_count=device.warnings or 0,
                    created_at=event.created_at,
                )
                created_count += 1

            # Always create a snapshot from the current device state + latest report
            latest_report = FullReport.objects.filter(device=device).order_by('-created_at').first()
            hi = None
            wc = device.warnings or 0
            if latest_report:
                try:
                    parsed = LynisReport(latest_report.full_report).get_parsed_report()
                    hi_raw = parsed.get('hardening_index')
                    if hi_raw is not None:
                        hi = int(hi_raw)
                    wc_raw = parsed.get('warning_count')
                    if wc_raw is not None:
                        wc = int(wc_raw)
                except Exception:
                    pass

            ComplianceSnapshot.objects.create(
                device=device,
                compliant=device.compliant,
                hardening_index=hi,
                warning_count=wc,
            )
            created_count += 1
            self.stdout.write(f'  Backfilled {device.hostname or device.hostid}')

        self.stdout.write(self.style.SUCCESS(f'Done. Created {created_count} snapshot(s) for {devices.count()} device(s).'))
