from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)