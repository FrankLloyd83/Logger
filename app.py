from flask import Flask, request
import config
from Logger.classes.Logger import LoggerServer

app = Flask(__name__)
app.config.from_object(config)
log = LoggerServer(app.config)


@app.route("/")
def index():
    return "Hello World! This is the logger default route."

@app.route("/Send", methods=["POST"])
def send():
    if log.validateAccessToken(request.headers.get("Authorization").split(" ")[1],
                               app.config["URL_ISSUER_BASE"] + app.config["TENANT_ID"],
                               log.client_id):
        data = request.data.decode("utf-8")
        log.log(data)
        return "Log sent!"

@app.route("/getLogs", methods=["GET"])
def getLogs():
    return log.getLogs()

@app.route("/checkConnection", methods=["GET"])
def checkConnection():
    if log.validateAccessToken(request.headers.get("Authorization").split(" ")[1], 
                               app.config["URL_ISSUER_BASE"] + app.config["TENANT_ID"],
                               log.client_id):
        return "Connection successful!"
    else:
        return "Connection failed!"

if __name__ == "__main__":
    app.run(debug=True, port=8000)
