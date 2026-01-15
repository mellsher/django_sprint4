from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def bootstrap_form(form):
    """Render a form simply as paragraphs (compatible replacement)."""
    try:
        return mark_safe(form.as_p())
    except Exception:
        return ""


@register.simple_tag
def bootstrap_button(button_type="submit", content="Submit"):
    return mark_safe(f"<button type=\"{button_type}\" class=\"btn btn-primary\">{content}</button>")


@register.simple_tag
def bootstrap_field(field):
    try:
        return mark_safe(str(field))
    except Exception:
        return ""


@register.simple_tag
def bootstrap_css():
    return mark_safe(
        '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
    )


@register.simple_tag
def bootstrap_javascript():
    return mark_safe(
        '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>'
    )
