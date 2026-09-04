from django import template
from django.utils.safestring import mark_safe
from apps.core.services.forex_service import ForexService
import json

register = template.Library()

@register.simple_tag(takes_context=True)
def currency_convert(context, amount, from_currency='USD'):
    """
    Converts and formats price based on user session currency.
    Usage: {% currency_convert tour.price_usd %}
    """
    if amount is None:
        return ""
        
    target_currency = context.get('current_currency', 'USD')
    forex = ForexService()
    
    try:
        converted = forex.convert(float(amount), target_currency, from_currency)
        symbols = context.get('currency_symbols', {})
        symbol = symbols.get(target_currency, target_currency)
        
        if target_currency == 'TZS':
            # Format TZS with no decimals and thousand separators
            return f"{symbol} {int(round(converted, -2)):,}"
        
        return f"{symbol}{converted:,.2f}"
    except Exception:
        return f"${amount:,.2f}"

@register.simple_tag(takes_context=True)
def currency_amount(context, amount, from_currency='USD'):
    """
    Converts a price and returns the numeric amount for client-side totals.
    Usage: {% currency_amount tour.price_usd as converted_price %}
    """
    if amount is None:
        return ""

    target_currency = context.get('current_currency', 'USD')
    forex = ForexService()

    try:
        return forex.convert(float(amount), target_currency, from_currency)
    except Exception:
        return amount

@register.simple_tag(takes_context=True)
def currency_symbol(context):
    """
    Returns the active currency symbol.
    Usage: {% currency_symbol as active_currency_symbol %}
    """
    target_currency = context.get('current_currency', 'USD')
    symbols = context.get('currency_symbols', {})
    return symbols.get(target_currency, target_currency)

@register.simple_tag
def safe_cloudinary_url(image_field, width=800, height=None, crop='fill', format='auto', quality='auto'):
    """
    Returns a Cloudinary URL with transformations.
    Usage: {% safe_cloudinary_url tour.image width=1200 %}
    """
    if not image_field:
        return ""

    options = {
        'width': width,
        'fetch_format': format,
        'quality': quality,
        'crop': crop,
    }
    if height:
        options['height'] = height

    try:
        return image_field.build_url(**options)
    except Exception:
        return getattr(image_field, 'url', '')

@register.simple_tag
def schema_json(schema_dict):
    """
    Outputs a dictionary as JSON-LD script tag.
    Usage: {% schema_json tour.get_schema %}
    """
    if not schema_dict:
        return ""

    if isinstance(schema_dict, str):
        try:
            schema_dict = json.loads(schema_dict)
        except json.JSONDecodeError:
            return ""

    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema_dict)}</script>')

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns the current URL with updated query parameters.
    Usage: <a href="?{% query_transform page=2 %}">Page 2</a>
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            query[k] = v
        else:
            query.pop(k, None)
    return query.urlencode()


@register.inclusion_tag('components/star_rating.html')
def star_rating(rating):
    """
    Renders 5 SVG stars based on rating.
    """
    rating = float(rating or 0)
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    return {
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),
        'rating': rating
    }

@register.filter
def split(value, arg):
    """
    Splits a string by the given separator.
    Usage: {{ "a,b,c"|split:"," }}
    """
    return value.split(arg)

@register.filter
def subtract(value, arg):
    """
    Subtracts the arg from the value.
    Usage: {{ 10|subtract:5 }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.simple_tag
def deposit_amount(tour, num_people=1):
    """
    Returns formatted deposit string.
    """
    if not tour:
        return ""

    # Use price_usd or final_price (which handles discounts)
    price = getattr(tour, 'final_price', getattr(tour, 'price_usd', 0))
    deposit_pct = getattr(tour, 'deposit_percentage', 10)

    amount = (float(price) * int(num_people)) * (float(deposit_pct) / 100)
    return f"${amount:,.2f} ({deposit_pct}%)"



@register.filter
def lt(value, arg):
    """{{ value|lt:5 }} → True if value < arg"""
    try:
        return int(value) < int(arg)
    except (TypeError, ValueError):
        return False

@register.filter  
def gt(value, arg):
    """{{ value|gt:0 }} → True if value > arg"""
    try:
        return int(value) > int(arg)
    except (TypeError, ValueError):
        return False