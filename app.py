from flask import Flask
import logging
app = Flask(__name__)
logging.basicConfig(filename='dev.log', level=logging.INFO)
@app.route('/')
def hello():
    return 'hello world Dev!'

if __name__== "__main__":
    app.run(host='0.0.0.0', port=80)
