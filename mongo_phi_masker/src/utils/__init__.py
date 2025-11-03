"""
Utility modules for the PHI masking application.
"""

# Import only what's needed and avoid circular imports
# from src.core.connector import MongoConnector - Remove this line to break the circular import
from src.utils.verification_clean import MaskingVerifier

# Other imports if needed
# from src.utils.config_loader import ConfigLoader
# from src.utils.logger import setup_logging

# Only export what's necessary
__all__ = [
    "MaskingVerifier",
    # Other exports
]
