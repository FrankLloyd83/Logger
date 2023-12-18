from flask import Flask, request
import requests
import config
from classes.Logger import Logger

app = Flask(__name__)
app.config.from_object(config)
log = Logger(app.config["LOG_PATH"])

if __name__ == "__main__":
    print("Hello World!")
