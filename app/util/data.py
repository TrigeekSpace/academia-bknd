""" Model and schema related utilities. """
import functools, operator
from flask import request, g
from marshmallow import Schema, fields
from marshmallow.schema import SchemaMeta
from sqlalchemy import and_, or_, not_
from sqlalchemy.orm.query import Query

from app import db
from app.util.core import APIError, camel_to_snake, map_error

class Nested(fields.Nested):
    """
    Modified Marshmallow Nested field that allows flexible nested serialization.
    Use on_exclude metadata to control nested field behavior when excluded.
    (Currently on_exclude can be 'none', 'primary_keys' or 'default')
    """
    def _serialize(self, nested_obj, attr, obj):
        """
        Serialize nested data.

        Args:
            nested_obj: Nested model instance or query set.
            attr: Attribute name of nested object.
            obj: Model instance being handled.
        Returns:
            Serialized JSON object, with or without nested serialization applied.
        """
        serialize_nested = self.context.get("__serialize_nested")
        # Metadata
        on_exclude = self.metadata.get("on_exclude", "none")
        many = self.metadata.get("many", False)
        # Nested field serialization restriction
        if not serialize_nested or attr not in serialize_nested:
            # None
            if on_exclude=="none":
                return None
            # TODO: Primary key
        # Transfrom query set to iterable data if many is true
        if many and isinstance(nested_obj, Query):
            nested_obj = nested_obj.all()
        # Call base class serialize method
        return super(Nested, self)._serialize(nested_obj, attr, obj)

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
        nested += g.user_filters.get("with", [])
    # Schema instance
    if isinstance(schema, Schema):
        load_args = kwargs
    # Schema class
    elif issubclass(schema, Schema):
        schema = schema(**kwargs)
    else:
        raise TypeError("'schema' must be a derived class or a instance of Schema class.")
    # Dump with nested schema support
    schema.context["__serialize_nested"] = nested
    result = schema.dump(obj, **dump_args)[0]
    schema.context["__serialize_nested"] = None
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
    "lte": operator.le
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
        filter_exp = __build_filter_exp(query)
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
    if offset:
        query_set = query_set.offset(offset)
    # Limit
    limit = params.get("limit")
    if limit:
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
        query_set = handler(query_set, model, g.user_filters)
    return query_set
