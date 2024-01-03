from flask import Flask, request
import config
from Logger.classes.Logger import LoggerServer

app = Flask(__name__)
app.config.from_object(config)
log = LoggerServer(app.config["LOG_PATH"])

@app.route("/", methods=["GET", "POST"])
def default():
    data = request.data.decode("utf-8")
    log.log(data)
    return "Hello World!"

@app.route("/getLogs", methods=["GET"])
def getLogs():
    return log.getLogs()

@app.route("/checkConnection", methods=["GET"])
def checkConnection():
    return "Connection successful!"

if __name__ == "__main__":
    app.run(debug=True, port=8000)
