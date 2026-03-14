from flask import Response, request
import os

# Global UTF-8 header - aplies to all routes automatically Built-in Flask hook -runs after every request
def after_request(response: Response) -> Response:

    allowed_origins = os.environ.get('CORS_ORIGINS','http://localhost:5173').split(',') 

    origin = request.headers.get('Origin')

    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    elif '*' in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = '*'

    # only set JSON headers for JSON responses
    if response.content_type and 'application/json' in response.content_type:
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

    # CORS headers for all responses
    # do not overwrite the origin set above
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    # Cache control for all responses
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response #single return point