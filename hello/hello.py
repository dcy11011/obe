from flask import Flask
from sqlalchemy import true

app = Flask(__name__)
app.debug = True

@app.route("/")
def hello_world():
    return "<p>Hello! This is a flask test text. Enjoy!</p>"