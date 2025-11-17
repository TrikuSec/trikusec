from django import forms
from django.contrib.auth import get_user_model
from api.models import Device, PolicyRuleset, PolicyRule, LicenseKey

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['rulesets']
        widgets = {
            'rulesets': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
            }),
        }

class PolicyRulesetForm(forms.ModelForm):
    class Meta:
        model = PolicyRuleset
        fields = ['name', 'description', 'rules']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Enter ruleset name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full h-20 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Enter description',
            }),
            'rules': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        read_only = kwargs.pop('read_only', False)
        super().__init__(*args, **kwargs)
        # Make description optional (it's optional in the UI)
        self.fields['description'].required = False
        if read_only:
            for field in self.fields.values():
                field.widget.attrs['disabled'] = 'disabled'


class PolicyRuleForm(forms.ModelForm):
    class Meta:
        model = PolicyRule
        fields = ['enabled', 'name', 'description', 'rule_query']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={
                'class': 'mt-1 block border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
            }),
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Enter rule name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full h-20 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Enter description',
            }),
            'rule_query': forms.Textarea(attrs={
                'class': 'mt-1 block w-full h-20 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': "e.g., os == 'Linux' && hardening_index > `70`",
            }),
        }


class LicenseKeyForm(forms.ModelForm):
    class Meta:
        model = LicenseKey
        fields = ['name', 'max_devices', 'expires_at', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Enter license name (e.g., "Production servers" or "web-01")',
            }),
            'max_devices': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Leave empty for unlimited',
                'min': 1,
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'type': 'datetime-local',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'mt-1 block border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make max_devices optional (null means unlimited)
        self.fields['max_devices'].required = False
        self.fields['expires_at'].required = False


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
            'placeholder': 'name@example.com',
        })
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-100 text-gray-500 cursor-not-allowed',
                'readonly': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-gray-800',
                'placeholder': 'Last name',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = True
        self.fields['username'].help_text = 'Usernames cannot be changed.'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        User = get_user_model()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError('This email address is already being used by another account.')
        return email