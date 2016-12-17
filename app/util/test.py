""" Utilities for testing """
import json
from urllib.parse import quote
from base64 import b64encode

def create_json_param(param):
    '''
    Encode json param to string under the following sequence
    json -> json.dumps -> base64encode -> urllib.parse.quote

    Args:
        param: json param needs to be encoded.
    Returns:
        Encoded string.
    '''
    return quote(b64encode(json.dumps(param).encode()))

def get_response_data(data):
    '''
    Decode byteString data to json object.

    Args:
        data: byteString needs to be decode.
    Returns:
        decoded json object.
    '''
    return json.loads(data.decode())
    