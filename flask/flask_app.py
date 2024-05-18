
from flask import Flask, request, render_template, render_template_string

from utils import save_api_data, create_sample_map
import os


app = Flask(__name__)



@app.route('/')
def index():
    return render_template("index.html")


@app.route('/create_data/')
def create_data():
    return render_template("create_data.html")

#@app.route("/show_data/")
#def show_data():
#    return render_template("created_data/2023_monza_R.html")



@app.route('/show_data/', methods=['GET', 'POST'])
def show_data():
    files_path = "templates/created_data"
    if request.method == 'POST':
        selected_file = request.form.get('selected_file')
        file_path = os.path.join(files_path, selected_file)

        # Check if the file exists and read its content
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
            # Render the content of the file
            return render_template_string(file_content)
        else:
            return "File not found", 404

    # List all files in the specified directory
    files = os.listdir(files_path)
    return render_template('show_data.html', files=files)


@app.route('/idk', methods=['POST'])
def idk():
    year = request.form.get('year')
    track = request.form.get('track')
    event_type = request.form.get('event_type')
    
    save_api_data(int(year), track, "R", create_sample_map )

    # Redirect to a thank you page or back to the form
    return "DONE"






@app.route('/monza')
def render_the_map():
    return render_template('monza.html')

if __name__ == '__main__':
    app.run(debug=True)