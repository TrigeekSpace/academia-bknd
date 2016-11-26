""" Core utility functions and classes. """
import json
from importlib import import_module
from flask import Response, request
from flask.views import MethodView

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
        self.data = dict(status="failed", type=type, **kwargs)
        self.status = status

# API error handler
@app.errorhandler(APIError)
def api_error_handler(e):
    """ API error handler. """
    return Response(
        json.dumps(e.data),
        status=e.status,
        headers={"Access-Control-Allow-Origin": "*"},
        mimetype="application/json"
    )

def assert_logic(value, description, status=400):
    """ API logic assert. """
    if not value:
        raise APIError(status, "logic", reason=description)
    return value

class APIView(MethodView):
    """ Backend API view. """
    # Session class (Used to break reference circle)
    session_class = None
    def __init__(self, *args, **kwargs):
        """ Constructor. """
        super(APIView, self).__init__(*args, **kwargs)
        # Session class
        if not self.session_class:
            self.session_class = import_module("app.models").Session
    def dispatch_request(self, *args, **kwargs):
        """ Cross-origin request support. Authentication. """
        # Authentication
        token = request.headers.get(AUTH_TOKEN_HEADER)
        request.user = get_by(self.session_class, token=token, error=APIError(401, "auth_failure")).user if token else None
        # Call base class method
        response = super(APIView, self).dispatch_request(*args, **kwargs)
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
    """ Register view with given URL. """
    # Use as decorator
    if view==None:
        return lambda view: register_view(url, endpoint, view)
    # Process action or data handlers
    for handler_type in HANDLER_TYPES:
        handlers = {}
        setattr(view, "_%s_handlers" % handler_type, handlers)
        # Search for handlers
        for (key, value) in enumerate(view.__dict__):
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
    """ Set metadata for object. """
    metadata = getattr(obj, METADATA_KEY, {})
    metadata[name] = value
    setattr(obj, METADATA_KEY, metadata)

def has_metadata(obj, name):
    """ Check if an object has metadata. """
    return name in getattr(obj, METADATA_KEY, {})

def get_metadata(obj, name, default=None):
    """ Get metadata. """
    return getattr(obj, METADATA_KEY, {}).get(name, default)

def res_data(name, view=None, handler=None):
    """ Declare resource data handler. """
    if handler==None:
        return lambda handler: res_data(name, view, handler)
    if view==None:
        set_metadata(handler, "res_data", name)
    else:
        view._res_data_handlers[name] = handler
    return view

def res_action(name, view=None, handler=None):
    """ Declare resource action handler. """
    if handler==None:
        return lambda handler: res_action(name, view, handler)
    if view==None:
        set_metadata(handler, "res_action", name)
    else:
        view._res_action_handlers[name] = handler
    return view

def inst_data(name, view=None, handler=None):
    """ Declare instance data handler. """
    if handler==None:
        return lambda handler: inst_data(name, view, handler)
    if view==None:
        set_metadata(handler, "inst_data", name)
    else:
        view._inst_data_handlers[name] = handler
    return view

def inst_action(name, view=None, handler=None):
    """ Declare instance action handler. """
    if handler==None:
        return lambda handler: inst_action(name, view, handler)
    if view==None:
        set_metadata(handler, "inst_action", name)
    else:
        view._inst_action_handlers[name] = handler
    return view
