""" Permission management utilities. """
import functools
from types import FunctionType

from app.models import AbstractBaseGroup, User
from app.util.core import APIError

def __handle_perm_rule(rule, user, **kwargs):
    """ Handle permission rule. """
    return __perm_rule_map[type(rule)](user, **kwargs)

def __perm_rule_tuple(rules, user, **kwargs):
    """
    Handle tuple of permission rules.
    Authorized when at least one rule authorized.
    """
    authorized = True
    for rule in rules:
        authorized = authorized or __handle_perm_rule(rule, user, **kwargs)
    return authorized

def __perm_rule_list(rules, user, **kwargs):
    """
    Handle list of permission rules.
    Authorized only if all rules authorized.
    """
    authorized = True
    for rule in rules:
        authorized = authorized and __handle_perm_rule(rule, user, **kwargs)
    return authorized

def __perm_rule_user(rule_user, user, **kwargs):
    """ Permit specific user for current operation. """
    return rule_user==user

def __perm_rule_group(group, user, **kwargs):
    """ Permit user if the user is in a specific group. """
    # TODO: Finish here
    return True

def __perm_rule_func(func, user, **kwargs):
    """ Custom permission rule as function. """
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
    """ Check operation permission. """
    throw = kwargs.get("throw", True)
    # Not logged in
    if not request.user and throw:
        raise APIError(401, "login_required")
    # Execute rules
    authorized = __handle_perm_rule(rules, **kwargs)
    if not authorized and throw:
        raise APIError(403, "perm_denied")
    return authorized

def auth_required(*rules, **auth_kwargs):
    """ Decorate views that needs authorization. """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_perm(*rules, **auth_kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator
