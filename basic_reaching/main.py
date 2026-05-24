from psychopy import prefs
#prefs.hardware['audioLib'] = ['pyo', 'sounddevice']
#prefs.general['audioLib'] = ['pyo', 'sounddevice']
from psychopy import visual, core, event, gui
#from ReachingTask import rt_params
import pylink
import platform
import params
import display as ds
import random
import sys
import os
import reaching_exp as re
from pathlib import Path
from string import ascii_letters, digits
import ctypes


def main():
  import platform
  if platform.system() == "Linux":
      xlib = ctypes.cdll.LoadLibrary("libX11.so")
      xlib.XInitThreads()
  # Switch to the script folder
  script_path = os.path.dirname(sys.argv[0])
  if len(script_path) != 0:
      os.chdir(script_path)
      
  # Show only critical log message in the PsychoPy console
  from psychopy import logging
  logging.console.setLevel(logging.CRITICAL) 
  
  # For macOS users check if they have a retina/H screen
  if 'Darwin' in platform.system():
    dlg = gui.Dlg("Retina Screen?")
    dlg.addText("What type of screen will the experiment run on?")
    dlg.addField("Screen Type", choices=["High Resolution (Retina, 2k, 4k, 5k)", "Standard Resolution (HD or lower)"])
    # show dialog and wait for OK or Cancel
    ok_data = dlg.show()
    if dlg.OK:
        if dlg.data["Screen Type"] == "High Resolution (Retina, 2k, 4k, 5k)":  
            use_retina = True
        else:
            use_retina = False
    else:
        print('user cancelled')
        core.quit()
        sys.exit()

  # Set this variable to True to run the script in "Dummy Mode"
  dummy_mode = False 
  
  allowed_char = ascii_letters + digits + '_'
  dlg = gui.Dlg(title = "Introduce participant's ID")
  dlg.addField('Participant ID', required = True)
  dlg.addField('Tracker Mode', choices=["Labor (EyeLink)", "Laptop (Dummy)"])
  ok_data = dlg.show()
  if dlg.OK:
      if ok_data[0].strip() == '':
        print('No participant alias was entered.\nPlease start again and fill in alias.')
        quit()
      # Set up EDF data file name and local data folder
      #
      # The EDF data filename should not exceed 8 alphanumeric characters
      # use ONLY number 0-9, letters, & _ (underscore) in the filename
      elif not all([c in allowed_char for c in ok_data[0].rstrip().split(".")[0]]):
        print('ERROR: Invalid EDF filename')
      elif len(ok_data[0].rstrip().split(".")[0]) > 8:
        print('ERROR: EDF filename should not exceed 8 characters')
      participantID = ok_data[0]
      #Auslesen des Feldes ob Dummy mode aktiviert wurde.
      if ok_data[1] == "Laptop (Dummy)":
          params.DUMMY_MODE = True
      else:
          params.DUMMY_MODE = False
  else:
      quit()

  ## Does data folder exist? If not create it
  os.makedirs(os.path.dirname(__file__)+"/data", exist_ok=True)
  ## Does participant's folder exist? If not create it
  
  participant_folder = os.path.dirname(__file__)+"/data/"+ participantID
  os.makedirs(participant_folder, exist_ok=True)
  win = ds.initialize_window()

  # Experiment 1: Blob Stim, Fixed Sizes, Change of Opacity
  exp = re.ReachingExperiment(
    win=win,
    participant_id=participantID,
    data_dir=participant_folder
  )
  exp._run_exp()

main()