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
    el_tracker.sendMessage("DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1))
    
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
    
    # Setup Experiment COnditions
    exp_conds = params["conditions_training"]
    exp_reps = params["num_repetitions_training"]
    exp_method = params["randomization_training"] 
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

    # Log participant code
    el_tracker.sendMessage(f"PARTICIPANT: {participant_info['code']}")

    # Training trials
    for trial in tqdm(trial_handler_training, desc="Training", total=trial_handler_training.nTotal):
        task = TrackingTask(
            window,
            trial["thisN"],
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
        # --- NEU: Aufnahme vor dem Trial starten ---
        if not dummy_mode:
            el_tracker.setOfflineMode()
            el_tracker.startRecording(1, 1, 1, 1)
            pylink.pumpDelay(100)
        
        task.run()
        
        # --- NEU: Aufnahme nach dem Trial stoppen ---
        if not dummy_mode:
            pylink.pumpDelay(100)
            el_tracker.stopRecording()

    # Regular trials
    for trial in tqdm(trial_handler, desc="Experiment", total=trial_handler.nTotal):
        if trial["thisN"] in params["calibration_trials"]:
            # Call calibration routine
            if not dummy_mode:
                el_tracker.doTrackerSetup()

        task = TrackingTask(
            window,
            trial["thisN"],
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
        # --- NEU: Aufnahme vor dem Trial starten ---
        if not dummy_mode:
            el_tracker.setOfflineMode()
            el_tracker.startRecording(1, 1, 1, 1)
            pylink.pumpDelay(100)
            
        task.run()
        
        # --- NEU: Aufnahme nach dem Trial stoppen ---
        if not dummy_mode:
            pylink.pumpDelay(100)
            el_tracker.stopRecording()
    
# Host-Datei schließen und herunterladen
    if not dummy_mode:
        el_tracker.setOfflineMode()
        pylink.msecDelay(500)
        el_tracker.closeDataFile()
        
        # --- NEU: Ladebildschirm anzeigen ---
        transfer_msg = visual.TextStim(
            window, 
            text="Daten werden vom Eyetracker heruntergeladen...\nBitte warten.",
            color="white",  
            height=30
        )
        transfer_msg.draw()
        window.flip()
        # ------------------------------------

        # NEU: Ein ausführlicher Dateiname für deinen lokalen Rechner
        lokaler_dateiname = f"Participant_{participant_info['code']}_eyetracking.EDF"

        # Holt den Ordner, in dem dieses Skript gerade ausgeführt wird
        skript_ordner = os.path.dirname(os.path.abspath(__file__))
        lokaler_pfad = os.path.join(skript_ordner, lokaler_dateiname)
        
        try:
            el_tracker.receiveDataFile(edf_name, lokaler_pfad)
            print("--------------------------------------------------")
            print(f"ERFOLG: EDF-Datei gespeichert unter: {lokaler_pfad}")
            print("--------------------------------------------------")
        except RuntimeError as error:
            print("Fehler beim Herunterladen der EDF-Datei:", error)
            
        el_tracker.close()
