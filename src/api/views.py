from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from django.db import DatabaseError
from django.db.models import Q
from django.conf import settings
from .models import LicenseKey, Device, FullReport, DiffReport, DeviceEvent, EnrollmentSettings
from .forms import ReportUploadForm
from api.utils.lynis_report import LynisReport
from api.utils.error_responses import internal_error
from api.utils.license_utils import validate_license, check_license_capacity
#from utils.diff_utils import generate_diff, analyze_diff
import os
import logging
import re
from urllib.parse import urlparse

@csrf_exempt
@ratelimit(key='ip', rate='100/h', method='POST')
def upload_report(request):
    logging.debug('Uploading report...')
    if request.method == 'POST':
        form = ReportUploadForm(request.POST)
        if form.is_valid():
            report_data = form.cleaned_data['data']
            post_licensekey = form.cleaned_data['licensekey']
            post_hostid = form.cleaned_data['hostid']
            post_hostid2 = form.cleaned_data['hostid2']

            logging.debug(f'License key: {post_licensekey}')
            logging.debug(f'Host ID: {post_hostid}')

            # Check if the license key is valid
            # Keep original response format for Lynis compatibility
            try:
                is_valid, error_msg = validate_license(post_licensekey)
                if not is_valid:
                    logging.error(f'License validation failed: {error_msg}')
                    return HttpResponse(error_msg or 'Invalid license key', status=401)
                
                licensekey = LicenseKey.objects.get(licensekey=post_licensekey)
            except LicenseKey.DoesNotExist:
                logging.error('License key does not exist')
                return HttpResponse('Invalid license key', status=401)
            except DatabaseError as e:
                logging.error(f'Database error checking license key: {e}')
                return internal_error('Database error while checking license key')

            if not post_hostid or not post_hostid2:
                logging.error('Host ID not found')
                return HttpResponse('Host ID not found', status=400)
            
            # Check if the report has been correctly uploaded
            if not report_data:
                logging.error('No report found')
                return HttpResponse('No report found', status=400)

            # Parse the report FIRST to extract all identifiers for device matching
            try:
                report = LynisReport(report_data)
            except Exception as e:
                logging.error(f'Error parsing report: {e}')
                return internal_error('Error parsing report data')

            # Extract all 5 identifiers for device matching
            primary_ips = report.get('primary_ipv4_addresses') or []
            primary_ip = primary_ips[0] if isinstance(primary_ips, list) and len(primary_ips) > 0 and primary_ips[0] != '-' else None
            
            candidate_identifiers = {
                'hostid': post_hostid,
                'hostid2': post_hostid2,
                'hostname': report.get('hostname'),
                'ip_address': primary_ip,
                'mac_address': report.get('primary_mac_address'),
            }
            
            logging.debug(f'Device identification factors: {candidate_identifiers}')

            # 5-Factor Device Identification Algorithm
            # Find candidate devices that match ANY single identifier (scoped by license key)
            try:
                q_objects = Q()
                if candidate_identifiers['hostid']:
                    q_objects |= Q(hostid=candidate_identifiers['hostid'])
                if candidate_identifiers['hostid2']:
                    q_objects |= Q(hostid2=candidate_identifiers['hostid2'])
                if candidate_identifiers['hostname']:
                    q_objects |= Q(hostname=candidate_identifiers['hostname'])
                if candidate_identifiers['ip_address']:
                    q_objects |= Q(ip_address=candidate_identifiers['ip_address'])
                if candidate_identifiers['mac_address']:
                    q_objects |= Q(mac_address=candidate_identifiers['mac_address'])

                # Get all candidate devices (matching any identifier, same license)
                candidates = Device.objects.filter(licensekey=licensekey).filter(q_objects).distinct()

                # Score each candidate device by counting matching factors
                best_device = None
                best_score = 0
                
                for candidate in candidates:
                    score = 0
                    if candidate_identifiers['hostid'] and candidate.hostid == candidate_identifiers['hostid']:
                        score += 1
                    if candidate_identifiers['hostid2'] and candidate.hostid2 == candidate_identifiers['hostid2']:
                        score += 1
                    if candidate_identifiers['hostname'] and candidate.hostname == candidate_identifiers['hostname']:
                        score += 1
                    if candidate_identifiers['ip_address'] and candidate.ip_address == candidate_identifiers['ip_address']:
                        score += 1
                    if candidate_identifiers['mac_address'] and candidate.mac_address == candidate_identifiers['mac_address']:
                        score += 1
                    
                    logging.debug(f'Candidate device {candidate.id} ({candidate.hostname or candidate.hostid}): score {score}/5')
                    
                    if score > best_score:
                        best_score = score
                        best_device = candidate

                # Decision: Match if score >= 2 (at least 2 factors coincide)
                created = False
                license_changed = False
                
                if best_score >= 2:
                    device = best_device
                    created = False
                    logging.info(f'Device identified with score {best_score}/5. Device ID: {device.id}, Hostname: {device.hostname or device.hostid}')
                    
                    # Check if license changed (shouldn't happen since we filter by licensekey, but keep for safety)
                    old_license = device.licensekey
                    if old_license != licensekey:
                        license_changed = True
                        # Check license capacity before allowing license change
                        has_capacity, capacity_error = check_license_capacity(post_licensekey)
                        if not has_capacity:
                            logging.error(f'License capacity check failed: {capacity_error}')
                            return HttpResponse(capacity_error or 'License has reached maximum device limit', status=403)
                else:
                    # New device - no match found (score < 2)
                    created = True
                    logging.info(f'No matching device found (best score: {best_score}/5). Creating new device.')
                    
                    # Check license capacity before creating
                    has_capacity, capacity_error = check_license_capacity(post_licensekey)
                    if not has_capacity:
                        logging.error(f'License capacity check failed: {capacity_error}')
                        return HttpResponse(capacity_error or 'License has reached maximum device limit', status=403)
                    
                    # Create the new device
                    device = Device.objects.create(
                        hostid=post_hostid,
                        hostid2=post_hostid2,
                        licensekey=licensekey,
                        hostname=candidate_identifiers['hostname'],
                        ip_address=candidate_identifiers['ip_address'],
                        mac_address=candidate_identifiers['mac_address']
                    )
                    DeviceEvent.objects.create(device=device, event_type='enrolled')
                
                # Handle license change event
                if license_changed:
                    DeviceEvent.objects.create(
                        device=device,
                        event_type='license_changed',
                        metadata={
                            'old_license': old_license.licensekey if old_license else None,
                            'old_license_name': old_license.name if old_license else None,
                            'new_license': licensekey.licensekey,
                            'new_license_name': licensekey.name,
                        }
                    )
                    
            except DatabaseError as e:
                logging.error(f'Database error creating/retrieving device: {e}')
                return internal_error('Database error while processing device')
            
            try:
                latest_full_report = FullReport.objects.filter(device=device).order_by('-created_at').first()
            except DatabaseError as e:
                logging.error(f'Database error retrieving previous report: {e}')
                return internal_error('Database error while retrieving previous report')
            
            if latest_full_report:
                # Generate the diff and save it
                try:
                    latest_lynis = LynisReport(latest_full_report.full_report)
                    # Don't filter at diff creation time - filter only at display time
                    # This ensures all activities are stored and can be shown/hidden based on current rule state
                    # Filtering happens in the activity view (frontend/views.py) based on active silence rules
                    
                    # Generate structured diff (without ignore_keys - store all activities)
                    diff_data = latest_lynis.compare_reports(report_data, [])
                    # Store hostname to preserve it even if device is deleted
                    hostname = device.hostname or candidate_identifiers['hostname'] or device.hostid
                    DiffReport.objects.create(device=device, hostname=hostname, diff_report=diff_data)
                    logging.info(f'Diff created for device {post_hostid}')
                    logging.debug('Changed items: %s', diff_data)
                except DatabaseError as e:
                    logging.error(f'Database error creating diff report: {e}')
                    return internal_error('Database error while creating diff report')
            else:
                logging.info(f'No previous reports found for device {post_hostid}')
            
            # Save the new full report
            try:
                FullReport.objects.create(device=device, full_report=report_data)
            except DatabaseError as e:
                logging.error(f'Database error saving full report: {e}')
                return internal_error('Database error while saving report')
            
            # Update device information with latest values from report
            try:
                device.licensekey = licensekey
                # Update HostIDs in case they changed (e.g., re-enrollment)
                device.hostid = post_hostid
                device.hostid2 = post_hostid2
                # Update all identifiers
                device.hostname = candidate_identifiers['hostname']
                device.ip_address = candidate_identifiers['ip_address']
                device.mac_address = candidate_identifiers['mac_address']
                # Update other device attributes
                device.os = report.get('os')
                device.distro = report.get('os_fullname')
                device.distro_version = report.get('os_version')
                device.lynis_version = report.get('lynis_version')
                device.last_update = report.get('report_datetime_end')
                device.warnings = report.get('warning_count')
                device.save()
            except DatabaseError as e:
                logging.error(f'Database error updating device: {e}')
                return internal_error('Database error while updating device')

            logging.info(f'Device updated: {report.get("hostname")}')
            return HttpResponse('OK')
        return HttpResponse('Invalid form data', status=400)
    return HttpResponse('Invalid request method', status=405)

@csrf_exempt
@ratelimit(key='ip', rate='50/h', method='POST')
def check_license(request):
    if request.method == 'POST':
        post_licensekey = request.POST.get('licensekey')
        post_collector_version = request.POST.get('collector_version')

        if not post_licensekey:
            logging.error('No license key provided')
            return HttpResponse('No license key provided', status=400)

        if not post_collector_version:
            logging.error('No collector version provided')
            return HttpResponse('No collector version provided', status=400)

        # Keep original response format for Lynis compatibility
        try:
            is_valid, error_msg = validate_license(post_licensekey)
            if is_valid:
                logging.info('License key is valid')
                return HttpResponse('Response 100')
            else:
                logging.error(f'License key is invalid: {error_msg}')
                return HttpResponse('Response 500', status=401)
        except DatabaseError as e:
            logging.error(f'Database error checking license: {e}')
            return internal_error('Database error while checking license')
    return HttpResponse('Invalid request method', status=405)

@csrf_exempt
def enroll_sh(request):
    """Generate enroll bash script to install the agent on a new device."""
    licensekey = request.GET.get('licensekey', '').strip()
    if not licensekey:
        return HttpResponse('No license key provided', status=400)
    if not re.match(r'^[a-zA-Z0-9_-]+$', licensekey) or len(licensekey) > 255:
        return HttpResponse('Invalid license key format', status=400)
    if not LicenseKey.objects.filter(licensekey=licensekey).exists():
        return HttpResponse('Invalid license key', status=401)

    trikusec_lynis_api_url = settings.TRIKUSEC_LYNIS_API_URL
    parsed_lynis_api_url = urlparse(trikusec_lynis_api_url)
    # Extract netloc (hostname:port) for certificate operations
    trikusec_lynis_upload_server = parsed_lynis_api_url.netloc
    # Full URL with scheme for Lynis upload-server configuration
    trikusec_lynis_upload_url = f"{parsed_lynis_api_url.scheme}://{parsed_lynis_api_url.netloc}"
    enrollment_settings = EnrollmentSettings.get_settings()
    additional_packages = ' '.join(enrollment_settings.additional_package_names)
    skip_tests = ','.join(enrollment_settings.skip_test_ids)
    plugin_urls = [url.strip() for url in enrollment_settings.plugin_urls if url.strip()]

    context = {
        'trikusec_lynis_upload_server': trikusec_lynis_upload_server,
        'trikusec_lynis_upload_url': trikusec_lynis_upload_url,
        'licensekey': licensekey,
        'ignore_ssl_errors': enrollment_settings.ignore_ssl_errors,
        'overwrite_lynis_profile': enrollment_settings.overwrite_lynis_profile,
        'use_cisofy_repo': enrollment_settings.use_cisofy_repo,
        'enable_daily_reports': enrollment_settings.enable_daily_reports,
        'additional_packages': additional_packages,
        'skip_tests': skip_tests,
        'plugin_urls': plugin_urls,
    }
    return render(request, 'api/enroll.sh', context, content_type='text/x-shellscript')

def index(request):
    return HttpResponse('Hello, world. You\'re at the TrikuSec index.')