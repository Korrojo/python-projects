"""
MongoDB configuration utilities.

This module provides utilities for MongoDB configuration,
particularly for constructing connection URIs from environment variables.
"""

import logging
import os
from typing import Dict, Any

from src.utils.config_loader import generate_mongodb_uri

# Setup logger
logger = logging.getLogger(__name__)

def build_mongodb_config_from_env() -> Dict[str, Any]:
    """
    Build MongoDB configuration from environment variables.
    
    This function constructs MongoDB source and destination URIs
    from individual environment variables.
    
    Returns:
        Dictionary with MongoDB configuration
    """
    config = {"mongodb": {"source": {}, "destination": {}}}
    
    # Build source URI
    source_uri = os.environ.get("MONGO_SOURCE_URI")
    if not source_uri:
        # Build from components
        source_host = os.environ.get("MONGO_SOURCE_HOST", "localhost")
        source_port = os.environ.get("MONGO_SOURCE_PORT", "27017")
        source_username = os.environ.get("MONGO_SOURCE_USERNAME")
        source_password = os.environ.get("MONGO_SOURCE_PASSWORD")
        source_auth_db = os.environ.get("MONGO_SOURCE_AUTH_DB", "admin")
        source_use_srv = os.environ.get("MONGO_SOURCE_USE_SRV", "false").lower() == "true"
        source_use_ssl = os.environ.get("MONGO_SOURCE_USE_SSL", "false").lower() == "true"
        
        # Generate URI
        source_uri = generate_mongodb_uri(
            host=source_host,
            port=source_port,
            username=source_username,
            password=source_password,
            auth_source=source_auth_db,
            srv=source_use_srv,
            ssl=source_use_ssl
        )
        
        logger.info(f"Generated source MongoDB URI from environment variables")
    else:
        logger.info(f"Using source MongoDB URI from environment")
    
    # Build destination URI
    dest_uri = os.environ.get("MONGO_DEST_URI")
    if not dest_uri:
        # Build from components
        dest_host = os.environ.get("MONGO_DEST_HOST", "localhost")
        dest_port = os.environ.get("MONGO_DEST_PORT", "27017")
        dest_username = os.environ.get("MONGO_DEST_USERNAME")
        dest_password = os.environ.get("MONGO_DEST_PASSWORD")
        dest_auth_db = os.environ.get("MONGO_DEST_AUTH_DB", "admin")
        dest_use_srv = os.environ.get("MONGO_DEST_USE_SRV", "false").lower() == "true"
        dest_use_ssl = os.environ.get("MONGO_DEST_USE_SSL", "false").lower() == "true"
        
        # Generate URI
        dest_uri = generate_mongodb_uri(
            host=dest_host,
            port=dest_port,
            username=dest_username,
            password=dest_password,
            auth_source=dest_auth_db,
            srv=dest_use_srv,
            ssl=dest_use_ssl
        )
        
        logger.info(f"Generated destination MongoDB URI from environment variables")
    else:
        logger.info(f"Using destination MongoDB URI from environment")
    
    # Set database and collection
    source_db = os.environ.get("MONGO_SOURCE_DB")
    source_coll = os.environ.get("MONGO_SOURCE_COLL")
    dest_db = os.environ.get("MONGO_DEST_DB")
    dest_coll = os.environ.get("MONGO_DEST_COLL")
    
    # Build the complete config
    config["mongodb"]["source"]["uri"] = source_uri
    if source_db:
        config["mongodb"]["source"]["database"] = source_db
    if source_coll:
        config["mongodb"]["source"]["collection"] = source_coll
    
    config["mongodb"]["destination"]["uri"] = dest_uri
    if dest_db:
        config["mongodb"]["destination"]["database"] = dest_db
    if dest_coll:
        config["mongodb"]["destination"]["collection"] = dest_coll
    
    return config
