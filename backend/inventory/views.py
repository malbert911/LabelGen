from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .services import BulkScanParser, BulkGenerationService, SerialNumberGenerator
from .models import SerialNumber, Product, Config
from .forms import AdminLoginForm, ConfigForm, UPCUploadForm, ProductUPCForm, AdminPasswordChangeForm
import json
import csv


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
