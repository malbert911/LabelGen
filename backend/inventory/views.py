from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import BulkScanParser, BulkGenerationService, SerialNumberGenerator
from .models import SerialNumber
import json


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
