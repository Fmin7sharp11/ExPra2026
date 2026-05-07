# README

This repository contains code for running continuous psychophysics tracking task experiment.

## Stand-alone Version

This branch (`clean`) contains a self-contained and slimmed down version of the continuous psychophysics experiment. The purpose of this is to have a stand-alone version that is close to the original one, but without all the unnecessary functionality that ended up not being unused or that was specific to a research question.

Some scripts are more or less copied from the original, others are restructured to be a bit cleaner. One of the main improvements is that you can now adjust the experiment settings through the `params.yaml` file in the `config` folder. A copy of this file will be stored to the participant data folder.

The experiment can be started by running `main.py`. 

> [!CAUTION]
>
> The stand-alone version has not yet been tested on the lab PC. Most things should work, but especially the EyeLink connection should be tested.

> [!WARNING]
>
> You might encounter an error caused by `pylink`. To fix this, please follow the instructions in the Setup section below.

> [!NOTE]
>
> This implementation currently doesn't use drift correction, since I couldn't figure out how to do it. It should be considered taking a second look at it. 

### Changes

Some of the things I stripped:

- The blocking of trials (and the block info screen)
	- Instead, all trials are fully randomized
- The Scoreboard after each trial
- Unnecessary complex class structures
- Option for different inputs (e.g., Leap Motion)
- Option for noise backgrounds
- Option for sampling the initial target position

## Setup

### Python environment

We used [Conda](https://www.anaconda.com/) / [Miniconda](https://docs.conda.io/en/latest/miniconda.html) and will assume that it is installed on your system. In principle, you can also fulfil all requirements via `pip` installs. Also see the [official installation instructions](https://www.psychopy.org/download.html#linux) of PsychoPy.

Create the environment with:

```shell
conda env create --name cpp --file env.yaml
```

Activate the environment with:

```shell
conda activate cpp 
```

If you made changes to your environment and want to "realign" it with the YAML using:

```shell
conda env update --name cpp --file env.yaml --prune
```

### EyeLink

We currently use an "Eyelink 1000" and control it in the code via the [`iohub`](https://psychopy.org/api/iohub/index.html) library integrated into `psychopy`.

1. To access the [SR Research Forum](https://www.sr-research.com/support/index.php) you first need to request access
2. You (probably) need to install the [Eyelink Developers Kit](https://www.sr-research.com/support/thread-13.html)
3. If the installation of `pylink` did not work for any reason, you can download the wheel from [this page](https://www.sr-research.com/support/thread-8291.html)

> [!NOTE]
> Maybe the following issue got fixed in newer `psychopy` or `pylink` versions. In that case, the instructions can be ignored.

I got a `RuntimeError: Unable to use new EyeLinkCustomDisplay when a previous EyeLinkCustomDisplay is active. Call closeGraphics() before calling openGraphicsEx()` when trying to use `tracker.runSetupProcedure()` a second time in the experiment.

The only fix I found was to locally modify the file `miniconda3/envs/cpp/lib/python3.10/site-packages/psychopy_eyetracker_sr_research/sr_research/eyelink/eyetracker.py` and add `pylink.closeGraphics()` before `pylink.openGraphicsEx(genv)` in `runSetupProcedure`:

<details>
<summary>Code</summary>

```python
def runSetupProcedure(self, calibration_args={}):
    """Start the EyeLink Camera Setup and Calibration procedure.

    During the system setup, the following keys can be used on either the
    Host PC or Experiment PC to control the state of the setup procedure:

        * C = Start Calibration
        * V = Start Validation
        * ENTER should be pressed at the end of a calibration or validation to accept the calibration,
        or in the case of validation, use the option drift correction that can be performed as part of
        the validation process in the EyeLink system.
        * ESC can be pressed at any time to exit the current state of the setup procedure and return to
        the initial blank screen state.
        * O = Exit the runSetupProcedure method and continue with the experiment.
    """
    try:
        from . import calibration
        EyeLinkCoreGraphicsIOHubPsychopy = calibration.EyeLinkCalibrationProcedure

        already_recording = self.isRecordingEnabled()
        self.setRecordingState(False)

        if calibration_args:
            self.sendCalibrationSettingsCommands(self._eyelink, calibration_args)

        genv = EyeLinkCoreGraphicsIOHubPsychopy(self, calibration_args)

        print("eyetracker.py modified")  # XXX
        pylink.closeGraphics()  # XXX

        pylink.openGraphicsEx(genv)

        self._eyelink.doTrackerSetup()

        m = self._eyelink.getCalibrationMessage()
        r = self._eyelink.getCalibrationResult()

        # from pylink docs, getCalibrationResult should return:
        #
        # NO_REPLY if calibration not completed yet.
        # OK_RESULT(0) if success.
        # ABORT_REPLY(27) if 'ESC'  key aborted calibration.
        # -1 if calibration failed.
        # 1 if poor calibration or excessive validation error.
        #
        # but it returns 1000. ??
        #
        # getCalibrationResult returns "calibration_result: 0", where
        # 0 == OK_RESULT == successful calibration.
        # TODO: Test if eyelink returns different calibration_result if calibration fails.
        reply = dict(message=m, result=r)
        # reply is returning:
        # {'message': 'calibration_result: 0', 'result': 1000}
        # on a successful calibration.

        genv._unregisterEventMonitors()
        genv.window.winHandle.set_fullscreen(False)
        genv.window.winHandle.minimize()
        genv.clearAllEventBuffers()
        genv.window.close()
        del genv.window
        del genv

        self.setRecordingState(already_recording)

        return reply

    except Exception:
        printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_ERROR
```

</details>

### Monitor configuration

When the code creates a PsychoPy window, it reads in the monitor configuration from a JSON (so that visual degrees can be computed correctly). If your monitor configuration differs from the values in `config/window_config_fallback.json`, create a file named `config/window_config.json` and adjust the values there. Also see the [official tutorial](https://www.psychopy.org/builder/builderMonitors.html) for setting up a PsychoPy monitor.


## Controls

- <kbd>q</kbd> quits the experiment
- <kbd>0</kbd> opens the EyeLink interface, e.g., for recalibration
- <kbd>Esc</kbd> closes the EyeLink interface
- Everything else should be self explanatory

---

## Development

When using Visual Studio Code, we recommend adding the following lines to your project settings (`.vscode/settings.json`):

```json
{
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}"
    },
    "terminal.integrated.env.osx": {
        "PYTHONPATH": "${workspaceFolder}"
    },
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder}"
    }
}
```

This will make it easier to use absolute imports of your modules.
