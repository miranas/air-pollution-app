from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

#Route 1: Home page
@app.route("/")
def hello():
    return "Hello from Slovenia Air Quality"

#Route 2: Health check
@app.route("/api/health")
def health():
    return jsonify({
        "status": "OK",
        "message": "Slovenia Air Quality Monitoring",
        "version": "1.0"
    })

# run the app
if __name__ == "__main__":
    app.run(debug=True)
