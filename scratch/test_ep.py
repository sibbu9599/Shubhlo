from flask import Flask, url_for

app = Flask(__name__)

@app.route('/booking1', endpoint='booking1')
@app.route('/booking', endpoint='booking')
def booking1():
    return "OK"

with app.test_request_context():
    print("booking1 ->", url_for('booking1'))
    print("booking ->", url_for('booking'))
