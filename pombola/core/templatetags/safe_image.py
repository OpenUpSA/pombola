from django import template

register = template.Library()

@register.filter
def safe_image_width(image):
    if image and hasattr(image, 'width'):
        return image.width
    return None
