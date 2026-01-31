"""
Rate Limiting - Schutz vor Missbrauch.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter-Instanz erstellen
limiter = Limiter(key_func=get_remote_address)

# Rate Limit Konstanten
RATE_LIMIT_REGISTER = "5/minute"
RATE_LIMIT_LOGIN = "10/minute"
RATE_LIMIT_APPLICATION = "10/minute"
RATE_LIMIT_BOOKING = "10/minute"
RATE_LIMIT_RESEND = "3/minute"

# User Management Rate Limits
RATE_LIMIT_FORGOT_PASSWORD = "3/minute"
RATE_LIMIT_RESET_PASSWORD = "5/minute"
RATE_LIMIT_CHANGE_EMAIL = "3/hour"
RATE_LIMIT_CHANGE_PASSWORD = "5/hour"
RATE_LIMIT_DELETE_ACCOUNT = "3/hour"
