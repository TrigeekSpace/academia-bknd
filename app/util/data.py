""" Model and schema related utilities. """
import functools, operator, json
from flask import request, g
from marshmallow import Schema, fields
from marshmallow.schema import SchemaMeta
from sqlalchemy import and_, or_, not_
from sqlalchemy.orm.query import Query
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.operators import ColumnOperators

from app import db
from app.util.core import APIError, camel_to_snake, map_error, getattr_keypath, setitem_keypath

class Nested(fields.Nested):
    """ Modified Marshmallow Nested field with flexible nested serialization and deserialization. """
    def __init__(self, *args, **kwargs):
        # Initialize base class
        super(Nested, self).__init__(*args, **kwargs)
        # Model
        model = self.metadata.get("model")
        if not model:
            raise AttributeError("Model parameter must be defined for nested schema field.")
        # Primary key
        model_mirror = self.model_mirror = inspect(model)
        self.primary_key = getattr(model, model_mirror.primary_key[0].name)
    def _serialize(self, value, attr, obj):
        """
        Serialized nested data.

        Args:
            value: The value to be serialized.
            attr: The attribute or key on the object to be serialized.
            obj: The object the value was pulled from.
        Returns:
            Serialized value.
        """
        many = self.metadata.get("many", False)
        model = self.metadata["model"]
        nested_fields_stack = self.context.get("__nested_stack", None)
        nested_fields = nested_fields_stack[-1] if nested_fields_stack else None
        # No value
        if value==None:
            return value
        # Queryset type check
        if many and not isinstance(value, Query):
            raise TypeError("Only queryset can be serialized when many is True.")
        # Nested field serialization restriction
        if not nested_fields or attr not in nested_fields:
            if many:
                return [item[0] for item in value.with_entities(self.primary_key).all()]
            else:
                return getattr(value, self.primary_key.name)
        # Transfrom query set to iterable data if many is true
        if many and isinstance(value, Query):
            value = value.all()
        # Nested nested fields
        nested_nested_fields = nested_fields[attr]
        if nested_nested_fields:
            nested_fields_stack.append(nested_nested_fields)
            result = super(Nested, self)._serialize(value, attr, obj)
            nested_fields_stack.pop()
        else:
            result = super(Nested, self)._serialize(value, attr, obj)
        # Call base class serialize method
        return result
    def _deserialize(self, value, attr, data):
        """
        Find nested data by primary key as deserialize result.

        Args:
            value: The value to be deserialized.
            attr: The attribute or key in "data" to be deserialized.
            obj: The raw input data.
        Returns:
            Deserialized value.
        """
        import sys
        print(value, file=sys.stderr)
        many = self.metadata.get("many", False)
        model = self.metadata["model"]
        # Many
        if many:
            raise NotImplementedError()
        else:
            return value if isinstance(value, model) else get_pk(model, value)

def load_data(schema, data, load_args={}, **kwargs):
    """
    Load data through schema.

    Args:
        schema: Schema instance or class used for serialization.
        obj: Data to be deserialized.
        load_args: Arguments for "load" method in serialization process.
            Only valid if schema is a class derived from "Schema".
        kwargs: Arguments for class constructor if schema is class, or for "load" method if schema is instance.
    """
    # Schema instance
    if isinstance(schema, Schema):
        load_args = kwargs
    # Schema class
    elif issubclass(schema, Schema):
        schema = schema(**kwargs)
    else:
        raise TypeError("'schema' must be a derived class or a instance of Schema class.")
    # Parse with error handling
    obj, error = schema.load(data, **load_args)
    if error:
        raise APIError(400, "arg_fmt", errors=error)
    return obj

def dump_data(schema, obj, nested=(), nested_user=False, dump_args={}, **kwargs):
    """
    Dump data through schema.

    Args:
        schema: Schema instance or class used for serialization.
        obj: Model instance to be serialized.
        nested: Nested fields to be serialized.
        nested_user: Serialize nested fields designated by user request.
        dump_args: Arguments for "dump" method in serialization process.
            Only valid if schema is a class derived from "Schema".
        kwargs: Arguments for class constructor if schema is class, or for "dump" method if schema is instance.
    """
    # Nested serialization field list
    nested = list(nested)
    if nested_user:
        nested += g.json_params.get("with", [])
    # Schema instance
    if isinstance(schema, Schema):
        load_args = kwargs
    # Schema class
    elif issubclass(schema, Schema):
        schema = schema(**kwargs)
    else:
        raise TypeError("'schema' must be a derived class or a instance of Schema class.")
    # Nested fields
    nested_fields = {}
    for keypath in nested:
        setitem_keypath(nested_fields, keypath, {}, True)
    # Dump with nested schema support
    schema.context["__nested_stack"] = [nested_fields]
    result = schema.dump(obj, **dump_args)[0]
    schema.context["__nested_stack"] = None
    return result

def get_pk(model, pk, allow_null=False, error=APIError(404, "not_found")):
    """
    Get element by primary key.

    Args:
        model: Model class to operate.
        pk: Primary key of the element.
        allow_null: Return null when nothing is found. Will throw APIError otherwise.
        error: Custom error instance to be thrown when nothing is found.
    Returns:
        Model instance.
    Raises:
        APIError: When nothing is found and allow_null is set to false.
    """
    result = model.query.get(pk)
    if not (allow_null or result):
        raise error
    return result

def get_by(model, allow_null=False, error=APIError(404, "not_found"), **kwargs):
    """
    Get element by given condition.

    Args:
        model: Model class to operate.
        allow_null: Return null when nothing is found. Will throw APIError otherwise.
        error: Custom error instance to be thrown when nothing is found.
        kwargs: Keyword arguments to be passed to filter_by function.
    Returns:
        Model instance.
    Raises:
        APIError: When nothing is found and allow_null is set to false.
    """
    result = model.query.filter_by(**kwargs).first()
    if not (allow_null or result):
        raise error
    return result

def foreign_key(target_model, backref_name):
    """
    Define a foreign key relationship.

    Args:
        target_model: Name of the target model.
        backref_name: Back reference name on the target model.
    Returns:
        A tuple with a foreign key relationship object and a foreign key ID field.
    """
    return (
        db.relationship(target_model, backref=db.backref(backref_name, lazy="dynamic")),
        db.Column(db.Integer(), db.ForeignKey("%s.id" % camel_to_snake(target_model)))
    )

def many_to_many(source_model, target_model, backref_name):
    """
    Define a many-to-many relationship.

    Args:
        source_model: Name of the source model.
        target_model: Name of the target model.
        backref_name: Back reference name on the target model.
    Returns:
        A SQLAlchemy many-to-many relationship object.
    """
    source_model_snake = camel_to_snake(source_model)
    target_model_snake = camel_to_snake(target_model)
    # Helper table
    helper_table = db.Table(
        "m2m_%s_%s_%s" % (source_model, target_model, backref_name),
        db.Column("%s_id" % source_model_snake, db.Integer, db.ForeignKey("%s.id" % source_model_snake)),
        db.Column("%s_id" % target_model_snake, db.Integer, db.ForeignKey("%s.id" % target_model_snake))
    )
    # Many-to-many relationship
    return db.relationship(
        target_model,
        secondary=helper_table,
        backref=db.backref(backref_name, lazy="dynamic"),
        lazy="dynamic"
    )

def parse_param(schema=None, schema_class=None, target="params", init_args={}, load_args={}):
    """
    Decorator for checking and parsing request parameters.

    Args:
        schema: Schema instances to be used for deserializing.
        schema_class: Schema class to be used for deserializing.
            Can be a class derived from Schema class or a dictionary of class members.
            In the latter class, a class derived from Schema class will be created from given dictionary.
        target: Name of the attribute to be set on request data object (g).
        init_args: Parameters used to initialize a schema instance.
            Only valid when a schema class is passed in.
        load_args: Parameters used to deserialize requests.
    Returns:
        A decorator which does request parameters checking and deserializing before calling decorated view.
    """
    # Build schema from schema class
    if schema==None:
        # Build schema class from dictionary
        if isinstance(schema_class, dict):
            schema_class = SchemaMeta("ParamSchema", (Schema,), schema_class)
        # Illegal schema class type
        elif not issubclass(schema_class, Schema):
            raise TypeError("schema_class must be a dictionary or derived from Schema class.")
        schema = schema_class(**init_args)
    # Decorator
    def decorator(func):
        # Save parsed result into target variable
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            setattr(g, target, load_data(schema, request.get_json(), **load_args))
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Comparison filters
__comp_filters = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "contains": ColumnOperators.contains
}

# Logical filter
__logical_filters = {
    "and": and_,
    "or": or_,
    "not": not_
}

def __build_filter_exp(query, model):
    """
    Recursively build SQLAlchemy filter expression from user-provided query.

    Args:
        query: An array whose first element is the name of the filter.
            Subsequent elements in this array are the parameters of this filter.
            Parameters can be a single value or another query array.
            e.g. ["and", ["eq", "field1", true], ["or", ["ne", "field2", "hi"], ["gte", "field3.nested", 10]]]
        model: Data model on which fields in the filters can be found.
    Returns:
        A corresponding SQLAlchemy filter expression.
    Raises:
        APIError: When unknown query operator occurs.
    """
    # Comparison filters
    comp_builder = __comp_filters.get(query[0])
    if comp_builder:
        field = getattr_keypath(model, query[1])
        return comp_builder(field, query[2])
    # Logical filters
    logical_builder = __logical_filters.get(query[0])
    if logical_builder:
        nested_exp_list = [__build_filter_exp(nested_query, model) for nested_query in query[1:]]
        return logical_builder(*nested_exp_list)
    # Unknown filter
    raise APIError(400, "unknown_query_oper", operator=query[0])

def __filter_handler(query_set, model, params):
    """
    Handle user-provided filtering requests.

    Args:
        query_set: SQLAlchemy query set to be filtered.
        model: Data model from which given query set is generated.
        params: User-provided filter params, with format {"query": [...], ...}.
            For query format see "__build_filter_exp" function.
    Returns:
        A query set with user-provided filters applied.
    """
    query = params.get("query")
    if query:
        filter_exp = __build_filter_exp(query, model)
        return query_set.filter(filter_exp)
    else:
        return query_set

def __ordering_handler(query_set, model, params):
    """
    Handle ordering requests.

    Args:
        query_set: SQLAlchemy query set to be ordered.
        model: Data model from which given query set is generated.
        params: User-provided filter params, with format {"order": {"field1": <bool>, ...}, ...}.
            True indicates ascending order, while False indicates descending order.
    Returns:
        A query set with user-provided ordering applied.
    """
    orders = params.get("order")
    if not orders:
        return query_set
    # Ordering
    sqla_params = []
    for (field_keypath, order) in orders:
        field = getattr_keypath(model, field_keypath)
        param = field.asc() if order else field.desc()
        sqla_params.append(param)
    return query_set.order_by(*sqla_params)

def __pagination_handler(query_set, model, params):
    """
    Handle user-provided pagination requests.

    Args:
        query_set: SQLAlchemy query set to be paginated.
        model: Data model from which given query set is generated.
        params: User-provided filter params, with format {"offset": <int>, "limit": <int>, ...}.
    Returns:
        A query set with user-provided pagination applied.
    """
    # Offset
    offset = params.get("offset")
    if offset!=None:
        query_set = query_set.offset(offset)
    # Limit
    limit = params.get("limit")
    if limit!=None:
        query_set = query_set.limit(limit)
    return query_set

# User filter handlers
__user_filters = [
    __filter_handler,
    __pagination_handler,
    __ordering_handler
]

def filter_user(query_set, model):
    """
    Apply user-provided data filters to given query set.

    Args:
        query_set: SQLAlchemy query set to be filtered.
        model: Data model from which given query set is generated.
    Returns:
        A query set with user-provided filters, ordering and pagination applied.
    """
    # Handle user filters
    for handler in __user_filters:
        query_set = handler(query_set, model, g.json_params)
    return query_set

def file_field(**kwargs):
    """ Define a Marshmallow file field to use with depot. """
    return fields.Function(
        serialize=lambda file_obj: file_obj.path,
        deserialize=lambda file_obj: file_obj,
        **kwargs
    )

def get_form():
    """ Get form data and files from request object. """
    data = {}
    # Form
    for key, value in request.form.items():
        data[key] = json.loads(value)
    # File
    for key, value in request.files.items():
        data[key] = value
    return data
    
