""" Model and schema related utilities. """
import functools
from flask import request, g
from marshmallow import Schema
from marshmallow.schema import SchemaMeta

from app import db
from app.util.core import APIError, camel_to_snake

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
    return (
        db.relationship(target_model, backref=db.backref(backref_name, lazy="dynamic")),
        db.Column(db.Integer(), db.ForeignKey("%s.id" % camel_to_snake(target_model)))
    )

def many_to_many(source_model, target_model, backref_name):
    """ Define a many-to-many relationship. """
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
    """ Decorator for checking and parsing request parameters. """
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
