from psychopy import event, iohub, visual


def init_iohub(
    tracker_type: str,
    window: visual.Window,
    out_file: str = "et_data",
) -> "iohub.client.ioHubConnection":
    """
    Launches the iohub server which communicates with the eye tracker.

    Args:
        tracker_type (str): Whether to use the 'eyelink' or dummy mode with 'mouse'.
        window (visual.Window): Psychopy window.
        out_file (str, optional): What to call the EDF. Defaults to "et_data".

    Raises:
        RuntimeError: If tracker_type is invalid.

    Returns:
        iohub.client.ioHubConnection: The iohub server.
    """
    bg_color = 0

    # See https://github.com/psychopy/psychopy-eyetracker-sr-research/blob/main/psychopy_eyetracker_sr_research/sr_research/eyelink/default_eyetracker.yaml
    # Can be used to adjust settings of the eye tracker
    devices_config = {}
    eyetracker_config = {"name": "tracker"}
    if tracker_type == "mouse":
        eyetracker_config["calibration"] = {
            "screen_background_color": bg_color,
            "auto_pace": True,
            "target_duration": 0.75,  # Speed up
            "target_delay": 0.25,  # Speed up
            "target_attributes": {
                "animate": {"enable": True, "contract_only": True},
                "outer_diameter": 0.5,
                "inner_diameter": 0.25,
                #"outer_stroke_width": 0,
                #"inner_stroke_width": 0,
                "outer_fill_color": -1,
                "inner_fill_color": 1,
                "outer_line_color": None,
                "inner_line_color": None
            },
        }
        devices_config["eyetracker.hw.mouse.EyeTracker"] = eyetracker_config

    elif tracker_type == "eyelink":
        eyetracker_config["model_name"] = "EYELINK 1000 TOWER"
        eyetracker_config["simulation_mode"] = False
        eyetracker_config["runtime_settings"] = {
            "sampling_rate": 1000,
            "track_eyes": "BOTH",  # or is it "BINOCULAR"?
        }
        eyetracker_config["calibration"] = {
            "screen_background_color": bg_color,
            "auto_pace": True,
            "target_attributes": {
                "outer_diameter": 0.75,
                "inner_diameter": 0.25,
                # "outer_stroke_width": 0,
                # "inner_stroke_width": 0,
                "outer_fill_color": -1,
                "inner_fill_color": 1,
                "outer_line_color": None,
                "inner_line_color": None
            },
            "type": "THIRTEEN_POINTS",
        }
        eyetracker_config["default_native_data_file_name"] = out_file
        devices_config["eyetracker.hw.sr_research.eyelink.EyeTracker"] = eyetracker_config

    else:
        raise RuntimeError(
            f"{tracker_type} is not a valid tracker name; please use 'mouse' or 'eyelink'!"
        ) 
    
    ioh = iohub.launchHubServer(window=window, **devices_config)
    return ioh


def setup_tracker(tracker: "iohub.client.ioHubDeviceView") -> None:
    """
    Runs setup procedure, i.e., calibration.

    Args:
        tracker (ioHubDeviceView): The device you get from `ioh.getDevice("tracker")`.
    """
    # NOTE recalibration only works (for me) if you monkey-patch the eyetracker library
    # See eyelink_notes.md for further infos

    # Display calibration gfx window and run calibration.
    result = tracker.runSetupProcedure()
    print("Calibration returned: ", result)


def add_calibration_listener(tracker: "iohub.client.ioHubDeviceView") -> None:
    """
    Adds a callback to psychopy for starting the calibration/validation procedure.

    Args:
        tracker (ioHubDeviceView): The device you get from `ioh.getDevice("tracker")`.
    """
    func = lambda: setup_tracker(tracker)

    if event.globalKeys.get("0") is None:
        event.globalKeys.add(key="0", func=func, name="setup tracker")
