from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('core/analytics/google_analytics.html')
def google_analytics():
    return {'ga_measurement_id': settings.GA_MEASUREMENT_ID}

@register.inclusion_tag('core/analytics/meta_pixel.html')
def meta_pixel():
    return {'pixel_id': settings.META_PIXEL_ID}