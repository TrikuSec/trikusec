from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from django.db import DatabaseError
from .models import LicenseKey, Device, FullReport, DiffReport
from .forms import ReportUploadForm
from api.utils.lynis_report import LynisReport
from api.utils.error_responses import internal_error
#from utils.diff_utils import generate_diff, analyze_diff
import os
import logging

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
                if not LicenseKey.objects.filter(licensekey=post_licensekey).exists():
                    return HttpResponse('Invalid license key', status=401)
                else:
                    licensekey = LicenseKey.objects.get(licensekey=post_licensekey)
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

            # Check if the device already exists. If not, create it
            try:
                device, created = Device.objects.get_or_create(hostid=post_hostid, hostid2=post_hostid2, licensekey=licensekey)
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
                    latest_full_report = LynisReport(latest_full_report.full_report)
                    diff = latest_full_report.diff(report_data)
                    DiffReport.objects.create(device=device, diff_report=diff)
                    logging.info(f'Diff created for device {post_hostid}')

                    # Analyze the diff (debugging purposes)
                    lynis_diff = LynisReport.Diff(diff)
                    changed_items = lynis_diff.analyze()
                    logging.debug('Changed items: %s', changed_items)
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

            # Parse the new report
            try:
                report = LynisReport(report_data)
            except Exception as e:
                logging.error(f'Error parsing report: {e}')
                return internal_error('Error parsing report data')
            
            # Update device information (get most important keys)
            try:
                device.licensekey = licensekey
                device.hostname = report.get('hostname')    
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
            if LicenseKey.objects.filter(licensekey=post_licensekey).exists():
                logging.info('License key is valid')
                return HttpResponse('Response 100')
            else:
                logging.error('License key is invalid')
                return HttpResponse('Response 500', status=401)
        except DatabaseError as e:
            logging.error(f'Database error checking license: {e}')
            return internal_error('Database error while checking license')
    return HttpResponse('Invalid request method', status=405)

def index(request):
    return HttpResponse('Hello, world. You\'re at the Compleasy index.')