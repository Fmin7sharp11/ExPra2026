import csv
import json
import os
import sys
from os.path import abspath, dirname
from pathlib import Path

import yaml
from psychopy import core, data, gui

sys.path.append(dirname(dirname(abspath(__file__))))

from continuous_tracking.procedure import run_experiment


def start():
    """
    Entry point for running the experiment.
    """
    # Create dialog for inputting participant data
    dlg = gui.Dlg("Continuous Tacking Task")
    dlg.addField("Participant code")
    dlg.addField("Session", "1")
    dlg.addField("Age")
    dlg.addField("Gender", choices=["male", "female", "diverse"])
    dlg.addField("Visual aids", choices=["none", "glasses", "contact lenses"])
    dlg.addField("Ocular dominance", choices=["right", "left"])
    dlg.addField("Tracker Mode", choices=["Labor (eyelink)", "Laptop (mouse)"])
    dlg_data = dlg.show()

    if dlg.OK:
        code = dlg_data[0].strip().lower() if dlg_data[0] else "unnamed"
        session = int(dlg_data[1])
        participant_info = {
            "code": code,
            "session": session,
            "age": dlg_data[2],
            "gender": dlg_data[3],
            "visual aids": dlg_data[4],
            "ocular dominance": dlg_data[5],
        }

        # Save participant information
        #folder_path = Path(".") / "continuous_tracking" / "data" / "out" / code
        folder_path = Path(__file__).parent / "data" / "out" / code
        os.makedirs(folder_path, exist_ok=True)
        info_path = folder_path / f"info-{session}.json"
        with open(info_path, "a") as file:
            json.dump(participant_info, file, indent=4)

        # Load params
        #params_path = Path(".") / "continuous_tracking" / "config" / "params.yaml"
        params_path = Path(__file__).parent / "config" / "params.yaml"
        with open(params_path) as params_file:
            params = yaml.safe_load(params_file)
        # Den ausgewählten Tracker-Modus aus dem Dialog abfangen (Index 6 ist das 7. Feld)
        tracker_mode = dlg_data[6]
        
        # Den Wert aus der yaml-Datei im Arbeitsspeicher überschreiben
        if tracker_mode == "Laptop (mouse)":
            params["tracker_type"] = "mouse"
        else:
            params["tracker_type"] = "eyelink"

        # Save copy of params
        params_copy_path = folder_path / f"params-{session}.yaml"
        with open(params_copy_path, "a") as file:
            yaml.safe_dump(params, file, indent=4)

        # Prepare CSV file
        csv_filename = f"{code}_{session}_{data.getDateStr()}.csv"
        csv_path = folder_path / csv_filename
        with open(csv_path, "w", newline="") as csv_file:
            # `newline=""` is recommended
            # See https://docs.python.org/3/library/csv.html
            csv_writer = csv.writer(csv_file)

            # Start the procedure
            run_experiment(params, participant_info, csv_writer)

    else:
        print("Canceled")


if __name__ == "__main__":
    start()
    core.quit()
