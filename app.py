from flask import Flask, request
import config
from classes.Logger import Logger

app = Flask(__name__)
app.config.from_object(config)
log = Logger(app.config["LOG_PATH"])

@app.route("/", methods=["GET", "POST"])
def default():
    data = request.data.decode("utf-8")
    log.log(data)
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True, port=8000)
