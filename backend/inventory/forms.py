from django import forms
from .models import Config, Product
import csv
import io


class AdminLoginForm(forms.Form):
    """Login form for admin authentication."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input is-large',
            'placeholder': 'Enter admin password'
        }),
        label='Password'
    )


class ConfigForm(forms.ModelForm):
    class Meta:
        model = Config
        fields = ['serial_digits', 'current_serial']
        widgets = {
            'serial_digits': forms.NumberInput(attrs={'class': 'input'}),
            'current_serial': forms.NumberInput(attrs={'class': 'input'}),
        }
        labels = {
            'current_serial': 'Next Serial Number',
            'serial_digits': 'Serial Number Digit Count',
        }
        help_text = {
            'current_serial': 'The next serial number to be generated',
            'serial_digits': 'Number of digits with leading zeros (e.g., 6 = 000500)',
        }


class AdminPasswordChangeForm(forms.ModelForm):
    """Form for changing the admin password."""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Enter new password'}),
        label='New Admin Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirm password'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = Config
        fields = []
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data


class UPCUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with PartNumber,UPC format',
        widget=forms.FileInput(attrs={'class': 'file-input'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('File must be a CSV')
        return file
    
    def parse_csv(self):
        """Parse CSV and return list of (part_number, upc) tuples."""
        file = self.cleaned_data['csv_file']
        file.seek(0)
        decoded_file = file.read().decode('utf-8')
        csv_data = csv.reader(io.StringIO(decoded_file))
        
        results = []
        errors = []
        
        for row_num, row in enumerate(csv_data, start=1):
            # Skip header row if it exists
            if row_num == 1 and len(row) >= 2:
                if row[0].lower() in ['partnumber', 'part_number', 'part']:
                    continue
            
            if len(row) < 2:
                errors.append(f'Row {row_num}: Invalid format (needs at least 2 columns)')
                continue
            
            part_number = row[0].strip()
            upc = row[1].strip() if row[1].strip() else None
            
            if not part_number:
                errors.append(f'Row {row_num}: Part number is empty')
                continue
            
            results.append((part_number, upc))
        
        return results, errors


class LabelTemplateForm(forms.ModelForm):
    """Form for editing ZPL label templates."""
    class Meta:
        model = Config
        fields = [
            'serial_label_zpl', 'serial_label_width', 'serial_label_height',
            'box_label_zpl', 'box_label_width', 'box_label_height',
            'label_dpi'
        ]
        widgets = {
            'serial_label_zpl': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 10,
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'box_label_zpl': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 12,
                'style': 'font-family: monospace; font-size: 12px;'
            }),
            'serial_label_width': forms.NumberInput(attrs={'class': 'input'}),
            'serial_label_height': forms.NumberInput(attrs={'class': 'input'}),
            'box_label_width': forms.NumberInput(attrs={'class': 'input'}),
            'box_label_height': forms.NumberInput(attrs={'class': 'input'}),
            'label_dpi': forms.Select(attrs={'class': 'select'}),
        }


class ProductUPCForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['part_number', 'upc']
        widgets = {
            'part_number': forms.TextInput(attrs={
                'class': 'input',
                'readonly': 'readonly'
            }),
            'upc': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '12-digit UPC (optional)'
            }),
        }
