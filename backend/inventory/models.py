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
