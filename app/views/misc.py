from flask import jsonify

from app import app
from app.util.core import SUCCESS_RESP

@app.route("/ping")
def ping_endpoint():
    return jsonify(
        academia_bknd=1,
        **SUCCESS_RESP,
    )
