from django.utils.text import slugify
from rest_framework import serializers


class AutoSlugModelSerializer(serializers.ModelSerializer):
    """Validate generated URL slugs before reaching the model's save hook."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance and self.instance.slug:
            return attrs
        model = self.Meta.model
        slug = slugify(attrs.get('name', ''))
        field = serializers.SlugField(max_length=model._meta.get_field('slug').max_length)
        try:
            slug = field.run_validation(slug)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({'name': exc.detail}) from None
        conflicts = model.objects.filter(slug=slug)
        if self.instance:
            conflicts = conflicts.exclude(pk=self.instance.pk)
        if conflicts.exists():
            raise serializers.ValidationError(
                {'name': 'This name produces an existing URL slug. Choose a different name.'}
            )
        attrs['slug'] = slug
        return attrs
