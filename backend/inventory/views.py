from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .services import BulkScanParser, BulkGenerationService, SerialNumberGenerator
from .models import SerialNumber, Product, Config
from .forms import AdminLoginForm, ConfigForm, UPCUploadForm, ProductUPCForm, AdminPasswordChangeForm, LabelTemplateForm
import json
import csv
import base64
import urllib.request
import urllib.error


def home(request):
    """Home page with links to all functionality."""
    return render(request, 'inventory/home.html')


def bulk_generate(request):
    """Bulk serial number generation page with hands-free scanning."""
    config = SerialNumberGenerator.get_config()
    context = {
        'config': config,
        'sample_serial': SerialNumberGenerator.format_serial(
            config.current_serial, 
            config.serial_digits
        )
    }
    return render(request, 'inventory/bulk_generate.html', context)


@require_http_methods(["POST"])
def process_bulk_scans(request):
    """
    API endpoint to process bulk scans and generate serial numbers.
    Expects JSON with list of part/quantity pairs.
    """
    try:
        data = json.loads(request.body)
        pairs = data.get('pairs', [])
        
        # Validate each pair
        validated_pairs = []
        for pair in pairs:
            part_number = pair.get('part_number', '').strip()
            quantity_str = pair.get('quantity', '')
            
            try:
                quantity = int(quantity_str)
                qty_valid = quantity > 0
            except (ValueError, TypeError):
                quantity = None
                qty_valid = False
            
            validated_pairs.append({
                'part_number': part_number,
                'quantity': quantity,
                'valid': bool(part_number) and qty_valid,
                'error': None if (bool(part_number) and qty_valid) else 'Invalid input'
            })
        
        # Process the scans
        result = BulkGenerationService.process_bulk_scans(validated_pairs)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def box_label(request):
    """Box label printing page for shipping."""
    return render(request, 'inventory/box_label.html')


@require_http_methods(["GET"])
def lookup_serial(request):
    """API endpoint to lookup a serial number."""
    serial = request.GET.get('serial', '').strip()
    
    try:
        serial_record = SerialNumber.objects.select_related('part_number').get(
            serial_number=serial
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'serial_number': serial_record.serial_number,
                'part_number': serial_record.part_number.part_number,
                'upc': serial_record.upc,
                'created_at': serial_record.created_at.isoformat()
            }
        })
    except SerialNumber.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Serial number not found'
        }, status=404)


def reprint(request):
    """Serial number reprint page."""
    return render(request, 'inventory/reprint.html')


def printer_settings(request):
    """Printer configuration page."""
    return render(request, 'inventory/printer_settings.html')


# Admin UPC Management Views

def admin_login(request):
    """Simple password-protected admin login."""
    if request.session.get('admin_authenticated'):
        return redirect('inventory:admin_upc')
    
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            # Get password from Config or use default
            config = SerialNumberGenerator.get_config()
            admin_password = getattr(config, 'admin_password', 'admin')
            
            if password == admin_password:
                request.session['admin_authenticated'] = True
                return redirect('inventory:admin_upc')
            else:
                form.add_error('password', 'Incorrect password')
    else:
        form = AdminLoginForm()
    
    return render(request, 'inventory/admin_login.html', {'form': form})


def admin_logout(request):
    """Logout from admin."""
    request.session.pop('admin_authenticated', None)
    return redirect('inventory:home')


def admin_upc(request):
    """Admin UPC management page."""
    if not request.session.get('admin_authenticated'):
        return redirect('inventory:admin_login')
    
    config = SerialNumberGenerator.get_config()
    products = Product.objects.all().order_by('part_number')
    
    # Handle config update
    config_updated = False
    if request.method == 'POST' and 'update_config' in request.POST:
        config_form = ConfigForm(request.POST, instance=config)
        if config_form.is_valid():
            config_form.save()
            config_updated = True
            config = SerialNumberGenerator.get_config()  # Reload config
    else:
        config_form = ConfigForm(instance=config)
    
    # Handle password change
    password_updated = False
    password_form = AdminPasswordChangeForm()
    if request.method == 'POST' and 'update_password' in request.POST:
        password_form = AdminPasswordChangeForm(request.POST)
        if password_form.is_valid():
            # Reload config to avoid stale data
            config = SerialNumberGenerator.get_config()
            config.admin_password = password_form.cleaned_data['new_password']
            config.save()
            password_updated = True
            password_form = AdminPasswordChangeForm()  # Reset form
    
    # Handle label template update
    template_updated = False
    if request.method == 'POST' and 'update_templates' in request.POST:
        template_form = LabelTemplateForm(request.POST, instance=config)
        if template_form.is_valid():
            template_form.save()
            template_updated = True
            config = SerialNumberGenerator.get_config()  # Reload config
    else:
        template_form = LabelTemplateForm(instance=config)
    
    # Handle CSV upload
    upload_form = UPCUploadForm()
    csv_results = None
    csv_errors = None
    
    context = {
        'config': config,
        'config_form': config_form,
        'config_updated': config_updated,
        'password_form': password_form,
        'password_updated': password_updated,
        'template_form': template_form,
        'template_updated': template_updated,
        'products': products,
        'upload_form': upload_form,
        'csv_results': csv_results,
        'csv_errors': csv_errors,
    }
    
    return render(request, 'inventory/admin_upc.html', context)


@require_http_methods(["POST"])
def admin_upload_csv(request):
    """Handle CSV upload for bulk UPC updates."""
    if not request.session.get('admin_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=403)
    
    form = UPCUploadForm(request.POST, request.FILES)
    if form.is_valid():
        results, errors = form.parse_csv()
        
        updated_count = 0
        created_count = 0
        
        for part_number, upc in results:
            product, created = Product.objects.get_or_create(part_number=part_number)
            product.upc = upc
            product.save()
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'updated': updated_count,
            'created': created_count,
            'errors': errors
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid file',
            'form_errors': form.errors
        }, status=400)


@require_http_methods(["POST"])
def admin_update_upc(request):
    """Update a single product's UPC."""
    if not request.session.get('admin_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=403)
    
    try:
        data = json.loads(request.body)
        part_number = data.get('part_number')
        upc = data.get('upc', '').strip() or None
        
        product = get_object_or_404(Product, part_number=part_number)
        product.upc = upc
        product.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def admin_download_template(request):
    """Download CSV template for UPC upload."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="upc_upload_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['PartNumber', 'UPC'])
    writer.writerow(['232-9983', '012345678901'])
    writer.writerow(['243-0012', '098765432109'])
    writer.writerow(['343-0323', ''])
    
    return response


@require_http_methods(["POST"])
def preview_zpl(request):
    """Preview ZPL label using Labelary API."""
    if not request.session.get('admin_authenticated'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=403)
    
    try:
        data = json.loads(request.body)
        zpl_code = data.get('zpl', '')
        label_type = data.get('label_type', 'serial')  # 'serial' or 'box'
        
        # Get config to determine label size
        config = SerialNumberGenerator.get_config()
        
        # Get dimensions based on label type
        if label_type == 'box':
            width = config.box_label_width
            height = config.box_label_height
        else:  # serial
            width = config.serial_label_width
            height = config.serial_label_height
        
        dpi = config.label_dpi
        
        # Convert DPI to DPMM (dots per millimeter) for Labelary API
        # 203 DPI = 8 DPMM, 300 DPI = 12 DPMM, 600 DPI = 24 DPMM
        dpi_to_dpmm = {
            203: '8dpmm',
            300: '12dpmm',
            600: '24dpmm'
        }
        dpmm = dpi_to_dpmm.get(dpi, '8dpmm')  # Default to 8dpmm if DPI not recognized
        
        # Labelary API endpoint: POST http://api.labelary.com/v1/printers/{dpmm}/labels/{width}x{height}/0/
        url = f'http://api.labelary.com/v1/printers/{dpmm}/labels/{width}x{height}/0/'
        
        # Send POST request with ZPL in body
        req = urllib.request.Request(
            url,
            data=zpl_code.encode('utf-8'),
            headers={
                'Accept': 'image/png',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return JsonResponse({
            'success': True,
            'image': f'data:image/png;base64,{image_base64}'
        })
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'Unknown error'
        return JsonResponse({
            'success': False,
            'error': f'Labelary API error: {e.code} - {error_body}'
        }, status=400)
    except urllib.error.URLError as e:
        return JsonResponse({
            'success': False,
            'error': f'Network error: {str(e.reason)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
def generate_label_zpl(request):
    """Generate ZPL code for a label with actual data."""
    try:
        data = json.loads(request.body)
        label_type = data.get('label_type')  # 'serial' or 'box'
        serial_number = data.get('serial_number', '')
        part_number = data.get('part_number', '')
        upc = data.get('upc', '')
        
        config = SerialNumberGenerator.get_config()
        
        # Get the appropriate template
        if label_type == 'serial':
            zpl_template = config.serial_label_zpl
        elif label_type == 'box':
            zpl_template = config.box_label_zpl
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid label_type. Must be "serial" or "box"'
            }, status=400)
        
        # Substitute variables
        zpl_code = zpl_template.replace('{{serial}}', serial_number)
        zpl_code = zpl_code.replace('{{part}}', part_number)
        
        # Handle UPC variables (both full and 11-digit versions)
        if upc:
            upc_full = upc  # Full 12-digit UPC
            upc_11 = upc[:11] if len(upc) >= 11 else upc  # First 11 digits for UPC-A barcode
        else:
            upc_full = ''
            upc_11 = ''
        
        zpl_code = zpl_code.replace('{{upc_full}}', upc_full)
        zpl_code = zpl_code.replace('{{upc_11_digits}}', upc_11)
        
        return JsonResponse({
            'success': True,
            'zpl': zpl_code,
            'label_type': label_type
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
