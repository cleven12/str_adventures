import requests
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class ForexService:
    """
    Handles live exchange rates for USD, EUR, GBP, and TZS.
    Uses ExchangeRate-API (Free tier) with caching for performance.
    """
    CACHE_KEY = 'forex_rates'
    CACHE_TIMEOUT = 86400  # 24 hours
    SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'TZS']
    BASE_CURRENCY = 'USD'

    def __init__(self):
        # Using a public free API that doesn't strictly require a key for some endpoints,
        # but ExchangeRate-API is more reliable.
        # Fallback rates if API fails
        self.default_rates = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'TZS': 2600.0
        }

    def get_rates(self):
        """
        Fetch rates from cache or API.
        """
        rates = cache.get(self.CACHE_KEY)
        if rates:
            return rates

        try:
            # Using ExchangeRate-API (Standard Free endpoint)
            # You can also use https://open.er-api.com/v6/latest/USD (Free, no key)
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('result') == 'success':
                all_rates = data.get('rates', {})
                rates = {curr: all_rates.get(curr) for curr in self.SUPPORTED_CURRENCIES if curr in all_rates}
                
                # Verify we got what we need
                if all(curr in rates for curr in self.SUPPORTED_CURRENCIES):
                    cache.set(self.CACHE_KEY, rates, self.CACHE_TIMEOUT)
                    return rates
            
            logger.error(f"Forex API error: {data.get('error-type', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Forex fetch failure: {e}")

        # Final fallback to hardcoded defaults (better than 0 or error)
        return self.default_rates

    def convert(self, amount, to_currency, from_currency='USD'):
        """
        Convert amount from one currency to another.
        """
        rates = self.get_rates()
        if from_currency == to_currency:
            return amount
        
        # Convert to USD first if not already
        if from_currency != 'USD':
            amount_in_usd = amount / rates.get(from_currency, 1.0)
        else:
            amount_in_usd = amount
            
        return amount_in_usd * rates.get(to_currency, 1.0)
