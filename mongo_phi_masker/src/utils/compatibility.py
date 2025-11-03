#!/usr/bin/env python3
"""
Compatibility layer for MongoPHIMasker.

This module provides compatibility wrappers and utilities to ensure
backward compatibility with older versions of the code, especially for tests.
"""

import functools
import inspect
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def deprecated(message: str) -> Callable:
    """Decorator to mark functions as deprecated.

    Args:
        message: Message to display when the function is used

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(f"DEPRECATED: {func.__name__} is deprecated. {message}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def param_adapter(old_params: list[str], new_params: list[str]) -> Callable:
    """Decorator to adapt parameter names.

    Args:
        old_params: List of old parameter names
        new_params: List of corresponding new parameter names

    Returns:
        Decorated function that adapts old parameter names to new ones
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Map old parameter names to new ones
            for old, new in zip(old_params, new_params, strict=False):
                if old in kwargs and new not in kwargs:
                    kwargs[new] = kwargs.pop(old)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def adapt_masking_processor_args(func: Callable) -> Callable:
    """Adapts arguments for MaskingProcessor.__init__.

    This function specifically handles the transition from:
    - Old: MaskingProcessor(document_masker, batch_size, min_batch_size, max_batch_size)
    - New: MaskingProcessor(rules_path, default_rules_path, collection_rules, initial_batch_size, min_batch_size, max_batch_size)

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get parameter info from signature
        inspect.signature(func)

        # If document_masker is provided as a positional arg and rules_path isn't,
        # we're using the old API - no change needed

        # If rules_path is provided but document_masker isn't,
        # we're using the new API - ensure proper mapping
        if "rules_path" in kwargs and "document_masker" not in kwargs:
            # Map initial_batch_size to batch_size if needed
            if "initial_batch_size" in kwargs and "batch_size" not in kwargs:
                kwargs["batch_size"] = kwargs.pop("initial_batch_size")

        return func(*args, **kwargs)

    return wrapper


def monkeypatch_backwards_compatibility():
    """Apply monkey patches for backward compatibility.

    This function should be called early in the application startup.
    """
    # Import modules only when needed to avoid circular imports
    from src.core.masker import MaskingProcessor
    from src.models.masking_rule import MaskingRule, RuleEngine

    # Store original methods
    original_masking_processor_init = MaskingProcessor.__init__
    original_rule_engine_init = RuleEngine.__init__

    # Patch RuleEngine initialization for backward compatibility
    def patched_rule_engine_init(self, rules=None):
        """Patched initialization for RuleEngine to handle different rule formats."""
        # Ensure rules is a list
        rules_list = [] if rules is None else rules

        # Ensure each rule is a proper MaskingRule object
        processed_rules = []
        for rule in rules_list:
            if isinstance(rule, dict):
                # Convert dictionary to MaskingRule object
                field = rule.get("field", "")
                rule_type = rule.get("rule", "")
                params = rule.get("params", {})
                processed_rules.append(MaskingRule(field, rule_type, params))
            else:
                processed_rules.append(rule)

        # Call original init
        original_rule_engine_init(self, processed_rules)

    # Apply decorators
    MaskingProcessor.__init__ = adapt_masking_processor_args(original_masking_processor_init)
    RuleEngine.__init__ = patched_rule_engine_init

    logger.debug("Applied backward compatibility monkey patches")
