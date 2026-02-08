from django.contrib import admin
from .models import Product, SerialNumber, Config


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['part_number', 'upc', 'serial_count']
    search_fields = ['part_number', 'upc']
    list_filter = []
    fields = ['part_number', 'upc']

    def serial_count(self, obj):
        return obj.serial_numbers.count()
    serial_count.short_description = 'Serial Count'


@admin.register(SerialNumber)
class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'part_number', 'upc', 'created_at']
    search_fields = ['serial_number', 'part_number__part_number', 'upc']
    list_filter = ['created_at', 'part_number']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        # Prevent manual creation via admin (should use bulk generation)
        return False


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['serial_start', 'serial_digits', 'current_serial', 'formatted_current']
    fields = ['serial_start', 'serial_digits', 'current_serial']
    
    def formatted_current(self, obj):
        return str(obj.current_serial).zfill(obj.serial_digits)
    formatted_current.short_description = 'Current Serial (Formatted)'
    
    def has_add_permission(self, request):
        # Only allow one config record
        return not Config.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of config
        return False
