from flask import Flask, request
import requests
import config
from classes.Logger import Logger

app = Flask(__name__)
app.config.from_object(config)
log = Logger(app.config["LOG_PATH"])

@app.route("/")
def default():
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True, port=8000)
