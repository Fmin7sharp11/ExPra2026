from typing import Any, Dict, Optional

import _csv
from psychopy import clock, event, visual, core
from psychopy.iohub.constants import EyeTrackerConstants
import pylink

from continuous_tracking.random_walker import RandomWalker
from continuous_tracking.stimulus import DotStimulus, make_gaussian_blob


class TrackingTask:
    def __init__(
        self,
        window: visual.Window,
        trial_number: int,
        num_trials: int,
        csv_writer: "_csv._writer",
        target_width: float = 0.5,
        cursor_width: float = 0.0,
        fps: int = 60,
        trial_duration: int = 20,
        training: bool = False,
        el_tracker: Any = None,
        dummy_mode: bool = False,
        trial_number_offset: int = 0,
        random_walk_kwargs: Dict[str, Any] = {},
    ) -> None:
        """
        Simple 2D continuous tracking task.

        Args:
            window (visual.Window): Window to draw on.
            trial_number (int): Number of current trial.
            num_trials (int): Total number of trials.
            csv_writer (_csv._writer): Object for storing data after the trial.
            target_width (float, optional): Width of the target stimulus. Either target or cursor
            should have a width of 0. Defaults to 0.5.
            cursor_width (float, optional): Width of the cursor stimulus. Either target or cursor
            should have a width of 0. Defaults to 0.0.
            fps (int, optional): Frames per second of the monitor. Defaults to 60.
            trial_duration (int, optional): How many seconds a trial lasts. Defaults to 20.
            training (bool, optional): Whether this trial is a training trial. Defaults to False.
            el_tracker: suports connection to Eyetracker
            trial_number_offset (int, optional): Number to add to the trial number when saving to
            CSV (but does not mess with the progress bar). Defaults to 0.
            random_walk_kwargs (Dict[str, Any], optional): Arguments to pass to the `RandomWalker`.
            Defaults to {}.
        """
        self.window = window
        self.trial_number = trial_number
        self.num_trials = num_trials
        self.csv_writer = csv_writer
        self.target_width = target_width
        self.cursor_width = cursor_width
        self.fps = fps
        self.trial_duration = trial_duration
        self.training = training
        self.el_tracker = el_tracker
        self.dummy_mode = dummy_mode
        self.trial_number_offset = trial_number_offset
        self.random_walk_kwargs = random_walk_kwargs

    def run(self) -> None:
        """
        Runs the trial.
        """
        self.prepare_visuals()
        self.show_fixation()
        self.show_trial()

    def prepare_visuals(self) -> None:
        """
        Constructs and stores the visual stimuli.
        """
        self.target = make_gaussian_blob(self.window, self.target_width)
        self.cursor = make_gaussian_blob(self.window, self.cursor_width)
        # self.mouse = event.Mouse(visible=False, newPos=(0, 0), win=self.window)
        self.mouse = event.Mouse(visible=False, win=self.window)

    def show_fixation(self) -> None:
        """
        Show a fixation screen before the trial starts.
        """
        text = "Place your cursor and click to start"
        if self.training:
            text = f"Training\n{text}"

        prompt = visual.TextBox2(
            self.window, pos=(0, 3), letterHeight=1, alignment="center", text=text
        )
        fixation_circle = visual.Circle(
            self.window, pos=(0, 0), radius=0.25, fillColor=None, lineColor=1
        )

        w = 10
        h = 0.5
        progress = w * self.trial_number / self.num_trials
        progress_bar_outline = visual.Rect(
            self.window, pos=(0, -5), width=w, height=h, fillColor=None, lineColor=0.5
        )
        progress_bar = visual.Rect(
            self.window,
            pos=((progress - w) / 2, -5),
            width=progress,
            height=h,
            fillColor=0.5,
            lineColor=None,
        )

        # TODO drift correction couly make sense here but I couldn't figure out how to use it
        # I tried `_doDriftCorrect(500, 1000, True, False)``
        # And `out = self.tracker.sendCommand("doDriftCorrect", value=(500, 1000, True, False)); print(x)`

        # Wait on user input
        while True:
            prompt.draw()
            fixation_circle.draw()
            progress_bar_outline.draw()
            progress_bar.draw()

            self.cursor.pos = self.mouse.getPos()
            self.cursor.draw()

            self.window.flip()
            # --- NEU: Tastaturabfrage für Notausgang und Bypass ---
            keys = event.getKeys()
            
            # 1. Notausgang: Wenn Escape gedrückt wird, sofort beenden
            if 'escape' in keys:
                self.window.close()
                core.quit()
                
            # 2. Bypass: Weiter, wenn Leertaste gedrückt ODER Kreis geklickt wird
            if 'space' in keys or self.mouse.isPressedIn(fixation_circle, buttons=[1]):
                break
            # -------------------------------------------------------

            if self.mouse.isPressedIn(fixation_circle, buttons=[1]):
                break

    def show_trial(self) -> None:
        """
        Displays the trial. At the end, stores the data to the CSV.
        """
        self.data = []

        dt = 1 / self.fps
        random_walker = RandomWalker(dt=dt, **self.random_walk_kwargs)

        actual_trial_number = self.trial_number + self.trial_number_offset
        num_frames = round(self.fps * self.trial_duration)

        self.el_tracker.sendMessage(f"TRIAL_START: {actual_trial_number}")
        if not self.training:
            self.el_tracker.setOfflineMode()
            self.el_tracker.startRecording(1, 1, 1, 1)
            pylink.pumpDelay(100)

        # Set up the timing
        timer = clock.Clock()

        # Perform one trial
        for i in range(num_frames):
            frame_start = timer.getTime()

            # Save current state
            target_pos = random_walker.pos
            target_vel = random_walker.vel
            mouse_pos = self.mouse.getPos()
#---------------------Eingefügt für Eyetracking
            if self.dummy_mode:
                gaze_x, gaze_y = mouse_pos[0], mouse_pos[1]
                trk_time = -1
            else:
                sample = self.el_tracker.getNewestSample()
                if sample is not None:
                    if sample.isLeftSample():
                        raw_x, raw_y = sample.getLeftEye().getGaze()
                    elif sample.isRightSample():
                        raw_x, raw_y = sample.getRightEye().getGaze()
                    else:
                        raw_x, raw_y = None, None
                    
                    if raw_x is not None and raw_y is not None:
                        gaze_x = raw_x - (self.window.size[0] / 2.0)
                        gaze_y = (self.window.size[1] / 2.0) - raw_y
                    else:
                        gaze_x, gaze_y = -999, -999
                    
                    trk_time = sample.getTime()
                else:
                    gaze_x, gaze_y = -999, -999
                    trk_time = -1

            self.data.append(
                [
                    self.target_width,
                    self.cursor_width,
                    target_pos[0],
                    target_pos[1],
                    mouse_pos[0],
                    mouse_pos[1],
                    target_vel[0],
                    target_vel[1],
                    frame_start,
                    actual_trial_number,
                    self.training,
                    gaze_x,
                    gaze_y,
                    trk_time
                ]
            )

            self.target.pos = target_pos
            self.cursor.pos = mouse_pos

            # Draw order depends on uncertainty condition
            if self.cursor_width == 0:
                self.target.draw()
                self.cursor.draw()
            else:
                assert self.target_width == 0
                self.cursor.draw()
                self.target.draw()

            self.window.flip()

            # Make one step (per frame)
            random_walker.walk()

        if not self.training:
            self.el_tracker.stopRecording()
            
        self.el_tracker.sendMessage(f"TRIAL_END: {actual_trial_number}")

        # Save data
        self.csv_writer.writerows(self.data)

    @staticmethod
    def init_csv(csv_writer: "_csv._writer") -> None:
        """
        Static method.
        Writes the header of the CSV.

        Args:
            csv_writer (_csv._writer): Object for writing to the CSV.
        """
        csv_writer.writerow(
            [
                "target_width",
                "cursor-width",
                "target_pos_x",
                "target_pos_y",
                "cursor_pos_x",
                "cursor_pos_y",
                "target_vel_x",
                "target_vel_y",
                "timestamp",
                "trial_number",
                "training",
                "gaze_pos_x",
                "gaze_pos_y",
                "tracker_time",
            ]
        )
