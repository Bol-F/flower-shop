from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class AutoSlugAdminForm(forms.ModelForm):
    """Validate the same generated slug that the model will persist."""

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        name = self.cleaned_data.get('name')
        if not slug and name:
            slug = slugify(name)
            if not slug:
                raise forms.ValidationError(
                    _('Enter a slug using letters, numbers, hyphens, or underscores.')
                )
            slug = self.fields['slug'].clean(slug)
        return slug
