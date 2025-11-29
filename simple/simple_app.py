from flask import Flask

#Create Flask app
app = Flask(__name__)

#Create one simple route
@app.route("/")
def hello():
    return "Hello from Slovenia Air Quality!"

#run the app
if __name__ == "__main__":
    app.run(debug=True)






