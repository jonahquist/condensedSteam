from flask import Flask
from flask import current_app as app
from flask import render_template


app = Flask(__name__)

@app.route("/")
def home():
    """home page"""
    return render_template(
        'home.html'
    )