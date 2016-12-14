""" Paper-related APIs. """
import os
from flask import request, jsonify, g

from app import db
from app.models import *
from app.schemas import *
from app.util.core import *
from app.util.data import *
from app.util.perm import auth_required

@register_view("/notes")
class NoteView(APIView):
    """ Note view class. """
    def list(self):
        """ List all users. """
        notes = filter_user(Note.query, Note).all()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(NoteSchema, notes, many=True, nested_user=True)
        )
    @auth_required()
    def create(self):
        """ Create a new user. """
        # Load note data
        note = load_data(NoteSchema, {**get_data(), "author": g.user})
        # Add to database
        db.session.add(note)
        db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(NoteSchema, note)
        )
    def retrieve(self, id):
        """ Get existing user information. """
        note = get_pk(Note, id)
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(NoteSchema, note, nested_user=True)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        note = get_pk(Note, id)
        load_data(NoteSchema, get_data(), instance=note)
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(NoteSchema, note)
        )
    def destroy(self, id):
        """ Remove user. """
        # Find and remove user
        note = get_pk(Note, id)
        db.session.delete(note)
        db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
