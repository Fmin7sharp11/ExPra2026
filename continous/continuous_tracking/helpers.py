import json
from pathlib import Path

from psychopy import core, event, visual, monitors


def create_window(dummy_mode: bool = False) -> visual.Window:
    """
    Instantiates a window based on a configuration JSON file and returns it.

    Returns:
        visual.Window: The created window.
    """
    #try:
    #    with open(
    #        Path(".") / "experiment" / "config" / "window_config.json"
    #    ) as file:
    #        config = json.load(file)
    #except (FileNotFoundError, json.decoder.JSONDecodeError) as error:
    #    # This is a generic configuration to use, when the window_config.json can't be opened
    #    with open(
    #        Path(".") / "experiment" / "config" / "window_config_fallback.json"
    #    ) as file:
    #        print("'config/window_config.json' not found -> ", repr(error))
    #        print("Using window_config_fallback.json instead")
    #        config = json.load(file)

    """     window = visual.Window(
        monitor="testMonitor",
        size=(2560, 1440),
        fullscr=True,
        # screen=config["screen"],
        units="deg",
        color=0,
        )

    return window """
    if dummy_mode:
        # SETUP 1: LOKALES TESTEN (Laptop)
        mon = monitors.Monitor('LaptopMonitor')
        mon.setWidth(34.5)           
        mon.setDistance(50)          
        mon.setSizePix((1920, 1080)) 

        window = visual.Window(
            monitor=mon,
            size=(1280, 720),        
            fullscr=False,           
            units="deg",
            color=0,
        )
        
    else:
        # SETUP 2: LABOR (EyeLink)
        mon = monitors.Monitor('LaborMonitor')
        mon.setWidth(33)             # Reale Breite im Labor
        mon.setDistance(70)          # Realer Abstand im Labor
        mon.setSizePix((1920, 1080)) # Reale Auflösung im Labor

        window = visual.Window(
            monitor=mon,
            size=(1920, 1080),       
            fullscr=True,            
            units="deg",
            color=0,
        )

    return window




def check_window_fps(window: visual.Window) -> None:
    """
    For a given Window, measures the actual frame rate.

    Args:
        window (visual.Window): The window for which the frame rate is measured.
    """
    try:
        frame_rate = window.getActualFrameRate(nIdentical=30, nMaxFrames=300, nWarmUpFrames=30)
        print(f"Monitor refresh rate ≈ {frame_rate:.2f}")
    except:
        print("Was not able to measure frame rate!")


def add_shutdown_listener() -> None:
    """
    Adds a callback to psychopy to for stopping the experiment code.
    """
    if event.globalKeys.get("q") is None:
        event.globalKeys.add(key="q", func=core.quit, name="shutdown")
