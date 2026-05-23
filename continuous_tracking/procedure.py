from typing import Any, Dict, Union

import _csv
from psychopy import data
from tqdm import tqdm
import numpy as np
from continuous_tracking.eyetracking import add_calibration_listener, init_iohub, setup_tracker
from continuous_tracking.helpers import add_shutdown_listener, check_window_fps, create_window
from continuous_tracking.task import TrackingTask


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

    ioh = init_iohub(params["tracker_type"], window, out_file=data.getDateStr("%H_%M"))
    tracker = ioh.getDevice("tracker")

    # Add callbacks
    add_shutdown_listener()
    add_calibration_listener(tracker)

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
    tracker.sendMessage(f"PARTICIPANT: {participant_info['code']}")

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
            ioh=ioh,
        )
        task.run()

    # Regular trials
    for trial in tqdm(trial_handler, desc="Experiment", total=trial_handler.nTotal):
        if trial["thisN"] in params["calibration_trials"]:
            # Call calibration routine
            setup_tracker(tracker)

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
            ioh=ioh,
            trial_number_offset=trial_handler_training.nTotal,
        )
        task.run()
