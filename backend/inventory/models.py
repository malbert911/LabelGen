from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    """
    Product table with PartNumber as primary key.
    UPC is optional and can be added later via admin interface.
    """
    part_number = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Part Number",
        help_text="Format: XXX-XXXX (e.g., 232-9983)"
    )
    upc = models.CharField(
        max_length=12,
        null=True,
        blank=True,
        verbose_name="UPC",
        help_text="12-digit Universal Product Code (optional)"
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['part_number']

    def __str__(self):
        return self.part_number


class SerialNumber(models.Model):
    """
    SerialNumber table with sequential serial number as primary key.
    UPC is denormalized from Product for fast label printing.
    """
    serial_number = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="Serial Number",
        help_text="Sequential number with leading zeros (e.g., 000500)"
    )
    part_number = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Part Number",
        related_name='serial_numbers'
    )
    upc = models.CharField(
        max_length=12,
        null=True,
        blank=True,
        verbose_name="UPC",
        help_text="Denormalized UPC for quick label printing"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        verbose_name = "Serial Number"
        verbose_name_plural = "Serial Numbers"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.serial_number} ({self.part_number})"


class Config(models.Model):
    """
    Configuration table for serial number generation settings.
    Should contain only one record.
    """
    serial_start = models.IntegerField(
        default=500,
        validators=[MinValueValidator(0)],
        verbose_name="Serial Start Position",
        help_text="Starting number for serial generation (default: 500, becomes 000500)"
    )
    serial_digits = models.IntegerField(
        default=6,
        validators=[MinValueValidator(1)],
        verbose_name="Serial Digit Count",
        help_text="Number of digits for serial numbers with leading zeros (default: 6)"
    )
    current_serial = models.IntegerField(
        default=500,
        validators=[MinValueValidator(0)],
        verbose_name="Current Serial Counter",
        help_text="Auto-incrementing counter for next serial number"
    )
    admin_password = models.CharField(
        max_length=100,
        default='admin',
        verbose_name="Admin Password",
        help_text="Password for UPC management admin interface"
    )
    
    # ZPL Label Templates
    serial_label_zpl = models.TextField(
        default="""^XA
^MTT
^PW406
^LL176
^LH0,20
^FO12,10^A0,18^FDNe pas enlever (Garantie)/Do not remove (Warranty)^FS
{{branding_zone_start}}
^FO12,30^A0,25^FDdcalltech.com^FS
{{branding_zone_end}}
^FO170,30^A0N,25,30^FD{{part}}^FS
^FO20,60^BY4^BCN,60,N,N,N,A^FD{{serial}}^FS
^FO90,130^A0N,20,30^FDSER.#: {{serial}}^FS
^XZ""",
        verbose_name="Serial Label ZPL Template",
        help_text="ZPL template for inventory serial number labels. Use {{serial}} for serial number, {{branding_zone_start}} and {{branding_zone_end}} for optional branding."
    )
    
    box_label_zpl = models.TextField(
        default="""^XA
^MTT
^PW812
^LL607
^LH0,0
^CI28
 
^FO20,190^A0N,30,30^FDNuméro de pièce:^FS
^FO20,220^A0N,30,20^FDPart Number:^FS
^FO20,255^A0N,45,45^FD{{part}}^FS
^FO310,220^BY3^BCN,70,Y,N,N^FD{{part}}^FS
 
^FO20,330^A0N,30,30^FDNuméro de série:^FS
^FO20,360^A0N,30,20^FDSerial Number:^FS
^FO20,395^A0N,45,45^FD{{serial}}^FS
^FO310,360^BY3^BCN,70,Y,N,N^FD{{serial}}^FS
 
{{upc_zone_start}}
^FO50,460^BY3^BUN,80,Y,N,Y^FD{{upc_11_digits}}^FS
{{upc_zone_end}}
 
^XZ""",
        verbose_name="Box Label ZPL Template",
        help_text="ZPL template for shipping box labels. Use {{part}}, {{serial}}, {{upc_full}}, {{upc_11_digits}} as placeholders."
    )
    
    label_dpi = models.IntegerField(
        default=203,
        validators=[MinValueValidator(1)],
        verbose_name="Printer DPI",
        help_text="Printer resolution in dots per inch (common: 203, 300, 600)"
    )

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configuration"

    def __str__(self):
        return f"Serial Config (Current: {str(self.current_serial).zfill(self.serial_digits)})"

    def save(self, *args, **kwargs):
        # Ensure only one config record exists
        if not self.pk and Config.objects.exists():
            raise ValueError("Only one configuration record is allowed")
        return super().save(*args, **kwargs)
