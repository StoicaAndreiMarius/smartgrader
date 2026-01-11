import secrets
import string
from .models import Test


def generate_share_code(length=12):
    """Generate a unique alphanumeric share code.

    Excludes ambiguous characters: 0, O, I, 1 to avoid confusion.
    Checks database to ensure uniqueness.

    Args:
        length: Length of the share code (default: 12)

    Returns:
        str: A unique share code
    """
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters: 0, O, I, 1
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')

    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not Test.objects.filter(share_code=code).exists():
            return code


def format_share_code(code):
    """Format share code as XXX-XXX-XXX-XXX for display.

    Args:
        code: The share code to format

    Returns:
        str: Formatted share code with hyphens every 3 characters
    """
    if not code:
        return None
    return '-'.join([code[i:i+3] for i in range(0, len(code), 3)])
