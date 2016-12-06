""" Paper-related APIs. """
import os
from flask import request, jsonify, g

from app import db
from app.models import *
from app.schemas import *
from app.util.core import *
from app.util.data import *

@register_view("/notes")
class NoteView(APIView):
    """ Note view class. """
    def list(self):
        """ List all users. """
        notes = filter_user(Note.query, Note).all()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(NoteSchema, notes, many=True)
        )

    def create(self):
        """ Create a new user. """
        # Load user data
        data = {**request.form, **request.files, "author": g.user}
        note = load_data(NoteSchema, data)
        # Add to database
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
            data=dump_data(NoteSchema, note)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        note = get_pk(Note, id)
        data = {**request.form, **request.files}
        load_data(NoteSchema, data, instance=note)
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
