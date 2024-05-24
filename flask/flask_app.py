
from flask import Flask, request, render_template, render_template_string
from utils import folium_with_corners
import os


app = Flask(__name__)



@app.route('/')
def index():
    return render_template("index.html")


@app.route('/create_data/')
def create_data():
    return render_template("create_data.html")



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
    files = [x for x in os.listdir(files_path) if x.endswith(".html")]
    return render_template('show_data.html', files=files)






@app.route('/dashboard')
def dashboard():
    track_name = request.args.get('track_name')
    index = request.args.get('index')
    # Now you can use track_name and index as needed, for example, to render the template
    return render_template('dashboard.html', track_name=track_name.capitalize(), index=index)



@app.route('/monza')
def render_the_map():
    return render_template('monza.html')




@app.route('/idk', methods=['POST'])
def display_track():
    d = dict()
    year = int(request.form.get('year'))
    track = request.form.get('track')
    event_type = request.form.get('event_type')
        # Get checkbox values
    d["throttle"] = request.form.get('throttle') == 'throttle'
    d["speed"] = request.form.get('speed') == 'speed'
    d["braking"] = request.form.get('braking') == 'braking'
    d["cluster"] = request.form.get('cluster') == 'cluster'


    print(d)

    folium_with_corners(year,track, event_type)
    html = f"created_data/{year}_{track}_{event_type}.html"

    return render_template(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
