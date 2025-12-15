from flask import Flask, Response
from flask.json.provider import DefaultJSONProvider
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:

    # Create Flask app
    app = Flask(__name__)

    # UTF-8 JSON Configuration
    app.config['JSON_AS_ASCII'] = False  # Ensure UTF-8 encoding for JSON responses
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Better JSON formatting
    app.config['JSON_SORT_KEYS'] = False  # Keep original order of JSON keys
    
    # Import blueprints
    from routes.station_routes import station_bp
    from routes.health_routes import health_bp
    from routes.debug_routes import debug_bp

    # Register blueprints
    app.register_blueprint(station_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)

    
    # Custom JSON provider to ensure UTF-8 encoding   
    class UTF8JsonProvider(DefaultJSONProvider):
        def dumps(self, obj, **kwargs):

            """Custom JSON encoder for UTF-8 support
            This method is called every time jsonify() is used
            Args:
                obj: Python object to convert to json
                **kwargs: JSON formatting options"""
        
            kwargs['ensure_ascii'] = False
            kwargs['indent'] =  2

            return super().dumps(obj, **kwargs)


    # Set custom JSON provider for the app
    app.json_provider_class = UTF8JsonProvider


    #Global UTF-8 header - aplies to all routes automatically Built-in Flask hook -runs after every request
    def _after_request(response: Response) -> Response:

        #only set JSON headers for JSON responses
        if response.content_type and 'application/json' in response.content_type:
            response.headers['Content-Type'] = 'application/json; charset=utf-8'

        #CORS headers for all responses   
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        #Cache control for all respnses
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
        return response #single return point


    # Register the after-request handler explicitly so static analyzers detect its usage
    app.after_request(_after_request)

    return app # Return the configured app instance

   

# run the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)




