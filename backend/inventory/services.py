"""
Service layer for business logic.
Handles serial number generation, bulk processing, and printing coordination.
"""

from django.db import transaction
from django.db.models import F
from .models import Product, SerialNumber, Config


class SerialNumberGenerator:
    """
    Handles atomic serial number generation with configurable leading zeros.
    """
    
    @staticmethod
    def get_config():
        """Get or create the configuration singleton."""
        config, created = Config.objects.get_or_create(
            pk=1,
            defaults={
                'serial_start': 500,
                'serial_digits': 6,
                'current_serial': 500
            }
        )
        return config
    
    @staticmethod
    def format_serial(number, digit_count):
        """Format a number with leading zeros based on digit count."""
        return str(number).zfill(digit_count)
    
    @staticmethod
    @transaction.atomic
    def generate_serials(part_number, quantity):
        """
        Generate a batch of serial numbers for a given part number.
        
        Args:
            part_number (str): The part number (e.g., "232-9983")
            quantity (int): How many serial numbers to generate
            
        Returns:
            dict: {
                'serials': [list of generated serial numbers],
                'start': first serial number,
                'end': last serial number,
                'part_number': part number instance,
                'upc': UPC code or None
            }
        """
        # Lock the config record to prevent race conditions
        config = Config.objects.select_for_update().get(pk=1)
        
        # Get or create the product
        product, created = Product.objects.get_or_create(
            part_number=part_number
        )
        
        # Calculate serial range
        start_serial = config.current_serial
        end_serial = start_serial + quantity - 1
        
        # Generate formatted serial numbers
        serials = []
        serial_records = []
        
        for i in range(quantity):
            serial_num = start_serial + i
            formatted_serial = SerialNumberGenerator.format_serial(
                serial_num, 
                config.serial_digits
            )
            serials.append(formatted_serial)
            
            # Prepare SerialNumber record
            serial_records.append(
                SerialNumber(
                    serial_number=formatted_serial,
                    part_number=product,
                    upc=product.upc  # Denormalized for fast label printing
                )
            )
        
        # Bulk create serial number records
        SerialNumber.objects.bulk_create(serial_records)
        
        # Update the config counter atomically
        config.current_serial = end_serial + 1
        config.save()
        
        return {
            'serials': serials,
            'start': serials[0],
            'end': serials[-1],
            'part_number': product,
            'upc': product.upc,
            'quantity': quantity
        }


class BulkScanParser:
    """
    Parses bulk barcode scan input and validates part/quantity pairs.
    """
    
    @staticmethod
    def parse_scan_input(scan_data):
        """
        Parse alternating Part Number and Quantity scans.
        
        Input format (each line is a separate scan):
        232-9983
        12
        243-0012
        1
        
        Args:
            scan_data (str): Multi-line string of scanned barcodes
            
        Returns:
            list: [{
                'part_number': str,
                'quantity': int,
                'valid': bool,
                'error': str or None
            }]
        """
        lines = [line.strip() for line in scan_data.strip().split('\n') if line.strip()]
        
        if len(lines) % 2 != 0:
            raise ValueError("Scan data must have an even number of lines (Part → Qty pairs)")
        
        pairs = []
        for i in range(0, len(lines), 2):
            part_number = lines[i]
            quantity_str = lines[i + 1]
            
            # Validate part number format (XXX-XXXX)
            part_valid = BulkScanParser.validate_part_number(part_number)
            
            # Validate quantity (positive integer)
            try:
                quantity = int(quantity_str)
                qty_valid = quantity > 0
                qty_error = None if qty_valid else "Quantity must be positive"
            except ValueError:
                quantity = None
                qty_valid = False
                qty_error = f"Invalid quantity: {quantity_str}"
            
            pairs.append({
                'part_number': part_number,
                'quantity': quantity,
                'valid': part_valid and qty_valid,
                'error': None if (part_valid and qty_valid) else (
                    f"Invalid part number format" if not part_valid else qty_error
                )
            })
        
        return pairs
    
    @staticmethod
    def validate_part_number(part_number):
        """
        Validate part number format (XXX-XXXX).
        Can be made more flexible if needed.
        """
        import re
        # Allow flexible format for now, just check it's not empty
        # Can uncomment regex for strict validation:
        # pattern = r'^\d{3}-\d{4}$'
        # return bool(re.match(pattern, part_number))
        return bool(part_number and len(part_number) > 0)


class BulkGenerationService:
    """
    Coordinates bulk serial number generation from scanned pairs.
    """
    
    @staticmethod
    def process_bulk_scans(pairs):
        """
        Process validated part/quantity pairs and generate serial numbers.
        
        Args:
            pairs (list): List of validated part/quantity dicts
            
        Returns:
            dict: {
                'results': [list of generation results per pair],
                'total_serials': int,
                'success_count': int,
                'error_count': int
            }
        """
        results = []
        total_serials = 0
        success_count = 0
        error_count = 0
        
        for pair in pairs:
            if not pair['valid']:
                results.append({
                    'part_number': pair['part_number'],
                    'quantity': pair['quantity'],
                    'success': False,
                    'error': pair['error']
                })
                error_count += 1
                continue
            
            try:
                result = SerialNumberGenerator.generate_serials(
                    pair['part_number'],
                    pair['quantity']
                )
                results.append({
                    'part_number': pair['part_number'],
                    'quantity': pair['quantity'],
                    'success': True,
                    'serial_range': f"{result['start']}-{result['end']}",
                    'serials': result['serials'],
                    'upc': result['upc']
                })
                total_serials += pair['quantity']
                success_count += 1
            except Exception as e:
                results.append({
                    'part_number': pair['part_number'],
                    'quantity': pair['quantity'],
                    'success': False,
                    'error': str(e)
                })
                error_count += 1
        
        return {
            'results': results,
            'total_serials': total_serials,
            'success_count': success_count,
            'error_count': error_count
        }
