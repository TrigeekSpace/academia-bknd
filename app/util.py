# Util.py: Utility functions and classes
from flask.views import MethodView

from app import app

METADATA_KEY = "__metadata__"
HANDLER_TYPES = ["res_data", "res_action", "inst_data", "inst_action"]

class APIError(Exception):
    """ API error class. """
    def __init__(self, status, type, **kwargs):
        super(APIError, self).__init__(dict(status="failed", type=type, **kwargs))
        self.status = status

def assert_logic(value, description, status=400):
    """ API logic assert. """
    if not value:
        raise APIError(status, "logic", description)

class APIView(MethodView):
    """ Backend API view. """
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
