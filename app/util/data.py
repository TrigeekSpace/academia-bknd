""" Model and schema related utilities. """
from app import db
from app.util.core import APIError

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

def foreign_key(target_model, backref_name, pk="id", pk_type=db.Integer()):
    """ Define a foreign key relationship. """
    return (
        db.relationship(target_model, backref=db.backref(backref_name, lazy="dynamic")),
        db.Column(pk_type, db.ForeignKey("%s.%s" % (target_model.lower(), pk)))
    )

def many_to_many(source_model, target_model, backref_name):
    """ Define a many-to-many relationship. """
    helper_table = db.Table(
        "m2m_%s_%s_%s" % (source_model, target_model, backref_name),
        db.Column("%s_id" % source_model.lower(), db.Integer, db.ForeignKey("%s.id" % source_model.lower())),
        db.Column("%s_id" % target_model.lower(), db.Integer, db.ForeignKey("%s.id" % target_model.lower()))
    )
    return db.relationship(
        target_model,
        secondary=helper_table,
        backref=db.backref(backref_name, lazy="dynamic"),
        lazy="dynamic"
    )
