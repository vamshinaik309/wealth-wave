from flask import Flask, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/logged_in', methods=['GET', 'POST'])
def logged_in():
    return render_template('logged_in.html')

@app.route('/logged_out', methods=['GET', 'POST'])
def logged_out():
    return render_template('logged_out.html')

if __name__ == '__main__':
    app.run(debug=True)
