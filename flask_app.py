
from flask import Flask, request, render_template, render_template_string
from utils import folium_with_corners
from florian_functions import runner_function
import os
import pandas as pd
import json

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
    
    f = open('static/drivers.json')
    drivers = json.load(f)
    try:
        clusters = pd.read_csv(f"static/dashboard/{track_name.capitalize()}/corner{index}/clusters.csv")
        li = []
        for i in range(max(clusters.Cluster)):
            sub = clusters[clusters["Cluster"] == i]["driver"]
            li.append((sub.iloc[0],sub.iloc[1]))

        clusters_with_names = []
        for pairing in li:
            clusters_with_names.append([drivers[driver] for driver in pairing if driver in drivers])

        clusters_with_names = []
        for pairing in li:
            clusters_with_names.append([drivers[str(x)] for x in pairing if str(x) in drivers])
    except:
        clusters_with_names = [()]
    
    return render_template('dashboard.html', track_name=track_name.capitalize(), index=index, clusters_with_names=clusters_with_names)





@app.route('/idk', methods=['POST'])
def display_track():
    d = dict()
    year = 2023
    track = request.form.get('track')
    event_type = request.form.get('event_type')
    num_laps = request.form.get('lap')
        # Get checkbox values
    print(num_laps)
    d["Throttle"] = request.form.get('throttle') == 'throttle'
    d["Speed"] = request.form.get('speed') == 'speed'
    d["Brake"] = request.form.get('braking') == 'braking'
    d["Cluster"] = request.form.get('cluster') == 'cluster'
    d["Trajectory"] = request.form.get('trajectory') == 'trajectory'
    d["Folium"] = request.form.get('folium') == 'folium'
    d["Separate Laps"] = request.form.get('gif') == 'gif'
    print(d)
    dx_dy =  runner_function(track,d, year,event_type, num_laps)

    folium_with_corners(year,track, event_type,dx_dy)
    html = f"created_data/{year}_{track}_{event_type}.html"
    return render_template(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
