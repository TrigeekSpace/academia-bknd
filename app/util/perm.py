""" Permission management utilities. """
import functools
from types import FunctionType
from flask import g

from app.models import AbstractBaseGroup, User
from app.util.core import APIError

def __handle_perm_rule(rule, user, **kwargs):
    """
    Recursively handle permission rule.

    Args:
        rule: Generic permission rule.
        user: User of current request.
    Returns:
        Whether the user is authorized or not.
    """
    return __perm_rule_map[type(rule)](rule, user, **kwargs)

def __perm_rule_tuple(rules, user, **kwargs):
    """
    Handle tuple of permission rules.
    Authorized when at least one rule authorized.

    Args:
        user: User of current request.
        kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    authorized = True
    for rule in rules:
        authorized = authorized or __handle_perm_rule(rule, user, **kwargs)
    return authorized

def __perm_rule_list(rules, user, **kwargs):
    """
    Handle list of permission rules.
    Authorized only if all rules authorized.

    Args:
        user: User of current request.
        kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    authorized = True
    for rule in rules:
        authorized = authorized and __handle_perm_rule(rule, user, **kwargs)
    return authorized

def __perm_rule_user(rule_user, user, **kwargs):
    """
    Permit specific user for current operation.

    Args:
        rule_user: Specific user to be permitted.
        user: User of current request.
        kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    return rule_user==user

def __perm_rule_group(group, user, **kwargs):
    """
    Permit user if the user is in a specific group.

    Args:
        group: Specific group to be permitted.
        user: User of current request.
        kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    # TODO: Group authorization
    return True

def __perm_rule_func(func, user, **kwargs):
    """
    Custom permission rule as function.

    Args:
        func: Custom permission rule checker.
        user: User of current request.
        kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    return func(user, **kwargs)

# Permission rule type to handler mapping
__perm_rule_map = {
    tuple: __perm_rule_tuple,
    list: __perm_rule_list,
    FunctionType: __perm_rule_func,
    User: __perm_rule_user,
    AbstractBaseGroup: __perm_rule_group
}

def check_perm(*rules, **kwargs):
    """
    Check operation permission.

    Args:
        rules: Authorization rules. Each rule is handled by a corresponding rule handler.
            The rule handler will be looked up for in "__perm_rule_map" by its type.
            Use "tuple" type to describe "or" relationship, and "list" for "and" relationship.
        auth_kwargs: Additional context used by authentication rules.
    Returns:
        Whether the user is authorized or not.
    """
    throw = kwargs.get("throw", True)
    # Not logged in
    if not g.user and throw:
        raise APIError(401, "login_required")
    # Execute rules
    authorized = __handle_perm_rule(rules, g.user, **kwargs)
    if not authorized and throw:
        raise APIError(403, "perm_denied")
    return authorized

def auth_required(*rules, **auth_kwargs):
    """
    Decorate views that needs authorization.
    Must be invoked with brackets.

    Args:
        rules: Authorization rules. See "check_perm" for rules format.
        auth_kwargs: Additional context used by authentication rules.
    Returns:
        Decorator that adds permission control to view or handler.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_perm(*rules, **auth_kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator
