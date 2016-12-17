""" Paper-related APIs. """
import os
from flask import request, jsonify, g
from sqlalchemy.exc import ProgrammingError

from app import db
from app.models import *
from app.schemas import *
from app.util.core import *
from app.util.data import *
from app.util.perm import auth_required

@register_view("/papers")
class PaperView(APIView):
    """ User view class. """
    def list(self):
        """ List all users. """
        papers = filter_user(Paper.query, Paper).all()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, papers, many=True, nested_user=True)
        )
    @auth_required()
    def create(self):
        """ Create a new user. """
        # Load user data
        paper = load_data(PaperSchema, {**get_data(), "author": g.user})
        # Add to database
        with map_error({ProgrammingError: handle_prog_error}):
            db.session.add(paper)
            db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, paper)
        )
    def retrieve(self, id):
        """ Get existing user information. """
        paper = get_pk(Paper, id)
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(PaperSchema, paper, nested_user=True)
        )
    def partial_update(self, id):
        """ Update user information. """
        # Load update data, then find and update user
        paper = get_pk(Paper, id)
        with map_error({ProgrammingError: handle_prog_error}):
            load_data(PaperSchema, get_data(), instance=paper)
            db.session.commit()
        # Success
        return jsonify(
            **SUCCESS_RESP,
            data=dump_data(UserSchema, paper)
        )
    def destroy(self, id):
        """ Remove user. """
        # Find and remove user
        paper = get_pk(Paper, id)
        db.session.delete(paper)
        db.session.commit()
        # Success
        return jsonify(**SUCCESS_RESP)
    @inst_action("toggle_collect_status")
    @auth_required()
    def toggle_collect_status(self, id):
        """ Toggle paper collection status. """
        # Find paper
        paper = get_pk(Paper, id)
        user = g.user
        # Cancel collection
        if user in paper.collectors:
            paper.collectors.remove(user)
            db.session.commit()
            return jsonify(
                **SUCCESS_RESP,
                collected=False
            )
        # Collect paper
        else:
            paper.collectors.append(user)
            db.session.commit()
            return jsonify(
                **SUCCESS_RESP,
                collected=True
            )
