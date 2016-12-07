""" Core utility functions and classes. """
import re, json
from importlib import import_module
from base64 import b64decode
from contextlib import contextmanager
from types import FunctionType
from traceback import format_exc, print_exc
from base64 import b64decode
from urllib.parse import unquote
from flask import Response, request, g, jsonify
from flask.views import MethodView
from marshmallow import Schema
from marshmallow.schema import SchemaMeta

from app import app, db
from app.config import AUTH_TOKEN_HEADER, CORS_MAX_AGE

# Object metadata key
METADATA_KEY = "__metadata__"
# API data and action handler types
HANDLER_TYPES = ["res_data", "res_action", "inst_data", "inst_action"]
# Success response
SUCCESS_RESP = {"status": "success"}

class APIError(Exception):
    """ API error class. """
    def __init__(self, status, type, **kwargs):
        """ Constructor. """
        self.data = dict(status="failed", type=type, **kwargs)
        self.status = status

def assert_logic(value, description, status=400):
    """
    API logic assert.

    Args:
        value: Boolean value for assertion.
        description: Description of the logic error.
        status: Response status.
    Returns:
        The value asserted.
    """
    if not value:
        raise APIError(status, "logic", reason=description)
    return value

class APIView(MethodView):
    """ Backend API view class. """
    # Session class (Used to break reference circle)
    session_class = None
    # Get by primary key
    get_pk = None
    def __init__(self, *args, **kwargs):
        """ Constructor. """
        super(APIView, self).__init__(*args, **kwargs)
        # Session class
        if not self.session_class:
            self.session_class = import_module("app.models").Session
        # Gen by primary key
        if not self.get_pk:
            self.get_pk = import_module("app.util.data").get_pk
    def dispatch_request(self, *args, **kwargs):
        """ Cross-origin request support. Authentication. """
        try:
            raw_json_params = request.args.get("json_params")
            # Parse raw user filters
            if raw_json_params:
                with map_error(APIError(400, "bad_json_params")):
                    g.json_params = json.loads(b64decode(unquote(raw_json_params).encode()).decode())
            else:
                g.json_params = {}
            # Authentication
            with map_error(APIError(401, "auth_failed")):
                token = b64decode(request.headers.get(AUTH_TOKEN_HEADER, b""))
                g.user = self.get_pk(self.session_class, token).user if token else None
            # Call base class method
            response = super(APIView, self).dispatch_request(*args, **kwargs)
        except APIError as e:
            response = jsonify(e.data)
            response.status_code = e.status
        except Exception as e:
            response = jsonify(
                status="failed",
                type="exception",
                exception_type=type(e).__name__,
                backtrace=format_exc()
            )
            response.status_code = 400
            # Print exception backtrace
            print_exc()
        # Cross-origin request
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    def get(self, ph1, ph2):
        """ HTTP GET method. """
        # List elements
        if ph1==None:
            return self.list()
        # Resource data
        elif isinstance(ph1, str):
            return self._res_data_handlers[ph1](self)
        # Get resource
        elif ph2==None:
            return self.retrieve(ph1)
        # Instance data
        else:
            return self._inst_data_handlers[ph2](self, ph1)
    def post(self, ph1, ph2):
        """ HTTP POST method. """
        # Create
        if ph1==None:
            return self.create()
        # Resource operation
        elif isinstance(ph1, str):
            return self._res_action_handlers[ph1](self)
        # Instance operation
        else:
            return self._inst_action_handlers[ph2](self, ph1)
    def delete(self, ph1):
        """ HTTP DELETE method. """
        return self.destroy(ph1)
    def patch(self, ph1):
        """ HTTP PATCH method. """
        return self.partial_update(ph1)
    def option(self, ph1, ph2):
        """ HTTP OPTION method. Used for cross-origin request. """
        return Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Max-Age": str(CORS_MAX_AGE),
                "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE",
                "Access-Control-Allow-Headers": AUTH_TOKEN_HEADER
            }
        )

def register_view(url, endpoint=None, view=None):
    """
    Register view with given URL.
    Usually used as decorator.

    Args:
        url: Base URL for given view.
        endpoint: Name of the endpoint. Same with view class name by default.
        view: View class.
    Returns:
        View class.
    """
    # Use as decorator
    if view==None:
        return lambda view: register_view(url, endpoint, view)
    # Process action or data handlers
    for handler_type in HANDLER_TYPES:
        handlers = {}
        setattr(view, "_%s_handlers" % handler_type, handlers)
        # Search for handlers
        for _, value in view.__dict__.items():
            target = get_metadata(value, handler_type)
            if target:
                handlers[target] = value
    # Register routes
    view_func = view.as_view(endpoint or view.__name__)
    app.add_url_rule(url, view_func=view_func, methods=["GET", "POST", "OPTION"], defaults={"ph1": None, "ph2": None})
    app.add_url_rule("%s/<int:ph1>" % url, view_func=view_func, methods=["GET", "OPTION"], defaults={"ph2": None})
    app.add_url_rule("%s/<string:ph1>" % url, view_func=view_func, methods=["GET", "POST", "OPTION"], defaults={"ph2": None})
    app.add_url_rule("%s/<int:ph1>/<string:ph2>" % url, view_func=view_func, methods=["GET", "POST", "OPTION"])
    app.add_url_rule("%s/<int:ph1>" % url, view_func=view_func, methods=["PATCH", "DELETE"])
    return view

def set_metadata(obj, name, value):
    """
    Set metadata for object.

    Args:
        name: Metadata key.
        value: Metadata value.
    """
    metadata = getattr(obj, METADATA_KEY, {})
    metadata[name] = value
    setattr(obj, METADATA_KEY, metadata)

def has_metadata(obj, name):
    """
    Check if an object has given metadata.

    Args:
        name: Name of the metadata key.
    Returns:
        Boolean value indicating the existance of given metadata.
    """
    return name in getattr(obj, METADATA_KEY, {})

def get_metadata(obj, name, default=None):
    """
    Get metadata of an object.

    Args:
        name: Name of the metadata key.
        default: Fallback value if given type of metadata is not found.
    Returns:
        Value of given type of metadata.
    """
    return getattr(obj, METADATA_KEY, {}).get(name, default)

def res_data(name, view=None, handler=None):
    """
    Declare resouce data handler that handles 'GET /<res>/<name>' route.
    Usually used as decorator.

    Args:
        name: Data name.
        view: APIView class to apply. Usually not needed.
        handler: Route handler.
    Returns:
        Handler function.
    """
    if handler==None:
        return lambda handler: res_data(name, view, handler)
    if view==None:
        set_metadata(handler, "res_data", name)
    else:
        view._res_data_handlers[name] = handler
    return handler

def res_action(name, view=None, handler=None):
    """
    Declare resource action handler that handles 'POST /<res>/<name>' route.
    Usually used as decorator.

    Args:
        name: Action name.
        view: APIView class to apply. Usually not needed.
        handler: Route handler.
    Returns:
        Handler function.
    """
    if handler==None:
        return lambda handler: res_action(name, view, handler)
    if view==None:
        set_metadata(handler, "res_action", name)
    else:
        view._res_action_handlers[name] = handler
    return handler

def inst_data(name, view=None, handler=None):
    """
    Declare instance data handler that handles 'GET /<res>/<id>/<name>' route.
    Usually used as decorator.

    Args:
        name: Data name.
        view: APIView class to apply. Usually not needed.
        handler: Route handler.
    Returns:
        Handler function.
    """
    if handler==None:
        return lambda handler: inst_data(name, view, handler)
    if view==None:
        set_metadata(handler, "inst_data", name)
    else:
        view._inst_data_handlers[name] = handler
    return handler

def inst_action(name, view=None, handler=None):
    """
    Declare instance action handler that handles 'POST /<res>/<id>/<name>' route.
    Usually used as decorator.

    Args:
        name: Action name.
        view: APIView class to apply. Usually not needed.
        handler: Route handler.
    Returns:
        Handler function.
    """
    if handler==None:
        return lambda handler: inst_action(name, view, handler)
    if view==None:
        set_metadata(handler, "inst_action", name)
    else:
        view._inst_action_handlers[name] = handler
    return handler

__first_cap_rx = re.compile("(.)([A-Z][a-z]+)")
__all_cap_rx = re.compile("([a-z0-9])([A-Z])")

def camel_to_snake(camel_name):
    """
    Convert camel case name to snake case.

    >>> camel_to_snake("thisIsAVariable")
    'this_is_a_variable'

    Args:
        camel_name: Camel case name.
    Returns:
        Corresponding name in snake case.
    """
    s1 = __first_cap_rx.sub(r"\1_\2", camel_name)
    return __all_cap_rx.sub(r"\1_\2", s1).lower()

@contextmanager
def map_error(error_mapping):
    """
    Execute code in a with block that does error mapping for the API.

    >>> with map_error(APIError(400, "e")):
    ...     raise TypeError()
    Traceback (most recent call last):
      ...
    app.util.core.APIError: (400, 'e')

    >>> with map_error({TypeError: APIError(400, "e1"), AssertionError: APIError(400, "e2")}):
    ...     raise AssertionError()
    Traceback (most recent call last):
      ...
    app.util.core.APIError: (400, 'e2')

    Args:
        error_mapping: Either an error object or an error mapping from exception type to target error object.
    """
    try:
        yield
    except Exception as e:
        # Error mapping
        if isinstance(error_mapping, dict):
            # Iterate through mapping
            for error_type, target in error_mapping.items():
                # Type matched
                if isinstance(e, error_type):
                    # Transform handler
                    if isinstance(target, FunctionType):
                        raise target(e)
                    # Error object
                    else:
                        raise target
            # No match, rethrow exception
            raise e
        # Match all exceptions to same object
        else:
            raise error_mapping

def getattr_keypath(obj, key_path, default=None):
    """
    Get attribute by its key path.

    >>> class a(object):
    ...     class b(object):
    ...         c = 2
    ...
    >>> getattr_keypath(a, "b.c")
    2

    Args:
        obj: Target object.
        key_path: Key path separated by dot.
        default: Fallback value for a non-existing keypath.
    Returns:
        Value corresponding with given key path.
    """
    split_key_path = key_path.split(".")
    for part in split_key_path:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return default
    return obj

def setitem_keypath(obj, key_path, value, create=False):
    """
    Set item by its key path.
    """
    split_key_path = key_path.split(".")
    for i, part in enumerate(split_key_path[:-1]):
        # Create
        if create:
            obj.setdefault(part, {})
        if part in obj:
            obj = obj[part]
        # No such attribute
        else:
            raise KeyError(".".join(split_key_path[:i+1]))
    obj[split_key_path[-1]] = value
