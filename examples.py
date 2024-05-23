from utils import create_buffered_track, save_api_data, create_sample_map

#These are example functions

def example():
    create_buffered_track("../bacinger f1-circuits master circuits/it-1922.geojson")


def pull_monza():
    save_api_data(2023, "monza", "R", create_sample_map )