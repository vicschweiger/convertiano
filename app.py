from flask import Flask
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    pass

if __name__ == "__main__":
    app.run(debug=True)