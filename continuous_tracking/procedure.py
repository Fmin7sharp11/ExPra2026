from typing import Any, Dict, Union

import _csv
from psychopy import data, visual
from tqdm import tqdm
import numpy as np
import pylink
from continuous_tracking.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from continuous_tracking.helpers import add_shutdown_listener, check_window_fps, create_window
from continuous_tracking.task import TrackingTask
import os


def run_experiment(
    params: Dict[str, Any], participant_info: Dict[str, Union[str, int]], csv_writer: "_csv._writer"
) -> None:
    """
    First sets up the window and eye tracker, then runs the experiment loop (training and regular
    trials).

    Args:
        params (Dict[str, Any]): Parameters from `params.yaml` that define the experiment settings.
        participant_info (Dict[str, Union[str, int]]): Containing all given information about the
        current participant.
        csv_writer (_csv._writer): Object for storing trial data.
    """
    window = create_window()
    check_window_fps(window)
    #---------------------Neue eingefügt, damit verbindung/ tracking basic reaching entspricht -------------
    dummy_mode = params["tracker_type"] == "dummy"

    if dummy_mode:
        el_tracker = pylink.EyeLink(None)
    else:
        el_tracker = pylink.EyeLink("100.1.1.1")
        
    edf_name = f"P{participant_info['code']}.EDF"
    el_tracker.openDataFile(edf_name)
    el_tracker.setOfflineMode()

    scn_width, scn_height = window.size
    el_tracker.sendCommand("screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1))
    
    # HIER IST DAS LEERZEICHEN WIEDER DRIN:
    el_tracker.sendMessage("DISPLAY_COORDS  0 0 %d %d " % (scn_width - 1, scn_height - 1))
    
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, window)
    genv.setCalibrationColors((-1, -1, -1), window.color)
    genv.setTargetType('circle')
    pylink.openGraphicsEx(genv)
    window.units = "deg"
    
    add_shutdown_listener()
    
    if not dummy_mode:
        el_tracker.doTrackerSetup()


    #------------------------------------------------------------
    # Write CSV header
    TrackingTask.init_csv(csv_writer)
    
    # Setup Training conditions
    train_conds = params["conditions_training"]
    train_reps = params["num_repetitions_training"]
    train_method = params["randomization_training"]
    train_trial_duration = params["trial_duration_training"]

    if train_method == "block":
        train_indices = np.repeat(np.arange(len(train_conds)), train_reps)
        blocked_training_conds = [train_conds[i] for i in train_indices]
    
        trial_handler_training = data.TrialHandler2(
            trialList=blocked_training_conds,
            nReps=1,
            method="sequential",  # Strict sequential order for blocks
        )
    else:
        trial_handler_training = data.TrialHandler2(
            trialList=train_conds,
            nReps=train_reps,
            method=train_method,
        )
    
    # Setup Experiment Conditions
    exp_conds = params["conditions"] 
    exp_reps = params["num_repetitions"]
    exp_method = params["randomization"] 
    exp_trial_duration = params["trial_duration"]

    if exp_method == "block":
        exp_indices = np.repeat(np.arange(len(exp_conds)), exp_reps)
        blocked_exp_conds = [exp_conds[i] for i in exp_indices]
    
        trial_handler = data.TrialHandler2(
            trialList=blocked_exp_conds,
            nReps=1,
            method="sequential",  # Strict sequential order for blocks
        )
    else:
        trial_handler = data.TrialHandler2(
            trialList=exp_conds,
            nReps=exp_reps,
            method=exp_method,
        )

    # Log participant code - HIER IST DAS LEERZEICHEN WIEDER DRIN:
    el_tracker.sendMessage(f"PARTICIPANT: {participant_info['code']} ")
    
    try:
        # Training trials
        for trial in tqdm(trial_handler_training, desc="Training", total=trial_handler_training.nTotal):
            current_training_n = trial_handler_training.thisN  # Sichere Abfrage der Trial-Nummer
            window.units="deg"
            task = TrackingTask(
                window,
                current_training_n,
                trial_handler_training.nTotal,
                csv_writer,
                target_width=trial["target_width"],
                cursor_width=trial["cursor_width"],
                fps=params["monitor_fps"],
                trial_duration=train_trial_duration,
                training=True,
                el_tracker=el_tracker,
                dummy_mode=dummy_mode,
            )
            # --- Aufnahme vor dem Trial starten ---
            if not dummy_mode:
                el_tracker.setOfflineMode()
                el_tracker.startRecording(1, 1, 1, 1)
                pylink.pumpDelay(100)
            
            task.run()
            
            # --- Aufnahme nach dem Trial stoppen ---
            if not dummy_mode:
                pylink.pumpDelay(100)
                el_tracker.stopRecording()

        # Regular trials
        for trial in tqdm(trial_handler, desc="Experiment", total=trial_handler.nTotal):
        
            current_trial_n = trial_handler.thisN  # Sichere Abfrage der Trial-Nummer
            window.units = "deg"
            # Absicherung: Überprüfen, ob calibration_trials existiert und der aktuelle Trial enthalten ist
            if "calibration_trials" in params and current_trial_n in params["calibration_trials"]:
                # Call calibration routine
                if not dummy_mode:
                    el_tracker.setOfflineMode()
                    pylink.msecDelay(500)
                    el_tracker.doTrackerSetup()
            window.units="deg"
            task = TrackingTask(
                window,
                current_trial_n,
                trial_handler.nTotal,
                csv_writer,
                target_width=trial["target_width"],
                cursor_width=trial["cursor_width"],
                fps=params["monitor_fps"],
                trial_duration=exp_trial_duration,
                training=False,
                el_tracker=el_tracker,
                dummy_mode=dummy_mode,
                trial_number_offset=trial_handler_training.nTotal,
            )
            # --- Aufnahme vor dem Trial starten ---
            if not dummy_mode:
                el_tracker.setOfflineMode()
                el_tracker.startRecording(1, 1, 1, 1)
                pylink.pumpDelay(100)
                
            task.run()
            
            # --- Aufnahme nach dem Trial stoppen ---
            if not dummy_mode:
                pylink.pumpDelay(100)
                el_tracker.stopRecording()
    finally:
        # ==========================================
        # Host-Datei schließen und herunterladen
        # ==========================================
        if not dummy_mode:
            # 1. Zwingend Aufnahme stoppen, falls das Programm im Trial abbrach
            el_tracker.stopRecording()
            pylink.pumpDelay(100)
            
            # 2. In den Offline-Modus wechseln und Datei schließen
            el_tracker.setOfflineMode()
            pylink.msecDelay(500)
            el_tracker.closeDataFile()
            
            # Ladebildschirm anzeigen, damit der Proband/Versuchsleiter weiß, was passiert
            try:
                window.units = "deg"
                transfer_msg = visual.TextBox2(
                    window, 
                    pos=(0, 0), 
                    letterHeight=1, 
                    alignment="center", 
                    text="Daten werden vom Eyetracker heruntergeladen...\nBitte warten."
                )
                transfer_msg.draw()
                window.flip()
            except Exception:
                pass

            # Speicherort für die EDF-Datei im selben Ordner wie die CSV festlegen
            basis_ordner = os.path.dirname(os.path.abspath(__file__))
            ziel_ordner = os.path.join(basis_ordner, "data", "out", str(participant_info["code"]))
            
            # Sicherstellen, dass der Zielordner existiert
            os.makedirs(ziel_ordner, exist_ok=True)
            
            lokaler_dateiname = f"P{participant_info['code']}_eyetracking.EDF"
            lokaler_pfad = os.path.join(ziel_ordner, lokaler_dateiname)
            
            try:
                # Datei übertragen
                el_tracker.receiveDataFile(edf_name, lokaler_pfad)
                print("--------------------------------------------------")
                print(f"ERFOLG: EDF-Datei gespeichert unter:\n{lokaler_pfad}")
                print("--------------------------------------------------")
            except RuntimeError as error:
                print("Fehler beim Herunterladen der EDF-Datei:", error)
            
        # Verbindung zum EyeTracker endgültig trennen
        el_tracker.close()