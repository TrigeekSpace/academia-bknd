""" Academia site configuration. """
from app.private_config import *

# Rounds of hashing
N_HASH_ROUNDS = 256
# Cross origin request max age
CORS_MAX_AGE = 691200
# Authentication token header
AUTH_TOKEN_HEADER = "X-Academia-Auth-Token"

# Database name
DB_NAME = os.environ["DB_NAME"]
# Database user name
DB_USERNAME = os.environ["POSTGRES_USER"]
# Database user password
DB_PASSWORD = os.environ["POSTGRES_PASSWORD"]
