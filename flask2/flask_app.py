from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/something1/')
def something1():
    return "You are on the Something 1 page."

@app.route('/something2/')
def something2():
    return "You are on the Something 2 page."

@app.route('/something3/')
def something3():
    return "You are on the Something 3 page."

@app.route('/something4/')
def something4():
    return "You are on the Something 4 page."

if __name__ == '__main__':
    app.run(debug=True)
