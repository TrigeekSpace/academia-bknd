# Util.py: Utility functions and classes
import functools
from types import FunctionType
from flask import Response, request
from flask.views import MethodView

from app import app, db
from app.models import User, Session, AbstractBaseGroup
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
        super(APIError, self).__init__(dict(status="failed", type=type, **kwargs))
        self.status = status

# API error handler
@app.errorhandler(APIError)
def api_error_handler(e):
    """ API error handler. """
    return jsonify(e.message), e.status

def assert_logic(value, description, status=400):
    """ API logic assert. """
    if not value:
        raise APIError(status, "logic", reason=description)
    return value

class APIView(MethodView):
    """ Backend API view. """
    def dispatch_request(self, *args, **kwargs):
        """ Cross-origin request support. Authentication. """
        # Authentication
        token = request.headers.get(AUTH_TOKEN_HEADER)
        request.user = get_by(Session, token=token, error=APIError(401, "auth_failure")).user if token else None
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
    def delete(self, id):
        """ HTTP DELETE method. """
        return self.destroy(self, id)
    def patch(self, id):
        """ HTTP PATCH method. """
        return self.partial_update(self, id)
    def option(self):
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
        for (key, value) in view.__dict__:
            target = get_metadata(value, handler_type)
            if target:
                handlers[target] = value
    # Register routes
    view_func = view.as_func(endpoint or view.__name__)
    app.add_url_rule(url, view_func=view_func, methods=["GET", "POST"], defaults={"ph1": None, "ph2": None})
    app.add_url_rule("%s/<ph1:int>" % url, view_func=view_func, methods=["GET"], defaults={"ph2": None})
    app.add_url_rule("%s/<ph1:string>" % url, view_func=view_func, methods=["GET", "POST"], defaults={"ph2": None})
    app.add_url_rule("%s/<ph1:int>/<ph2:string>" % url, view_func=view_func, methods=["GET", "POST"])
    app.add_url_rule("%s/<id:int>" % url, view_func=view_func, methods=["PATCH", "DELETE"])
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

def load_data(schema, data, **kwargs):
    """ Load data through schema. """
    obj, error = schema.load(data, **kwargs)
    if error:
        raise APIError(400, "arg_fmt", errors=error)
    return obj

def dump_data(schema, obj, **kwargs):
    """ Dump data through schema. """
    return schema.dump(obj, **kwargs)[0]

def get_pk(model, pk, allow_null=False, error=APIError(404, "not_found")):
    """ Get element by primary key. """
    result = model.query.get(pk)
    if not (allow_null or result):
        raise error
    return result

def get_by(model, allow_null=False, error=APIError(404, "not_found"), **kwargs):
    """ Get element by given condition. """
    result = model.query.filter_by(**kwargs).first()
    if not (allow_null or result):
        raise error
    return result

def foreign_key(target_model, backref_name):
    """ Define a foreign key relationship. """
    return db.relationship(target_model, backref=backref_name, lazy="dynamic")

def many_to_many(source_model, target_model, backref_name):
    """ Define a many-to-many relationship. """
    helper_table = db.Table(
        "m2m_%s_%s_%s" % (source_model, target_model, backref_name),
        db.Column("%s_id" % source_model.lower(), db.Integer, db.ForeignKey("%s.id" % source_model.lower())),
        db.Column("%s_id" % target_model.lower(), db.Integer, db.ForeignKey("%s.id" % target_model.lower()))
    )
    return db.relationship(target_model, secondary=helper_table, backref=db.backref(backref_name, lazy="dynamic"))

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
