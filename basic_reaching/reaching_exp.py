from __future__ import division
from __future__ import print_function
from psychopy import visual, core, event, monitors, gui
import pylink
import platform
import params as pm
import display as ds
import random
import numpy as np
import time
import os
import sys
import csv
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

class ReachingExperiment:
  def __init__(self, win, participant_id, data_dir) -> None:
    self.win = win
    self.participant_id = participant_id
    self.data_dir = data_dir
    
  def calibrate(self, win):
    # Step 5: Set up the camera and calibrate the tracker

    # Show the task instructions
    task_msg = pm.CALIBRATION
    if pm.DUMMY_MODE:
      task_msg = task_msg + pm.CALIBRATION_DUMMY_MODE
    else:
      task_msg = task_msg + pm.CALIBRATION_NO_DUMMY_MODE
    self.show_msg(win, task_msg)

    # skip this step if running the script in Dummy Mode
    if not pm.DUMMY_MODE:
      try:
          self.el_tracker.doTrackerSetup()
      except RuntimeError as err:
          print('ERROR:', err)
          self.el_tracker.exitCalibration()

  def clear_screen(self, win):
    """ clear up the PsychoPy window"""

    win.fillColor = self.genv.getBackgroundColor()
    win.flip()

  def show_msg(self, win, text, wait_for_keypress=True):
    """ Show task instructions on screen"""

    msg = visual.TextStim(win, text,
                          color=self.genv.getForegroundColor(),
                          wrapWidth=self.scn_width/2)
    self.clear_screen(win)
    msg.draw()
    win.flip()

    # wait indefinitely, terminates upon any key press
    if wait_for_keypress:
      while True:
        keys = event.waitKeys(keyList=['return', 'escape'])
        if 'return' in keys:
          break
        if 'escape' in keys:
          win.close()
          core.quit()
      self.clear_screen(win)

  def terminate_task(self, win, edf_file, session_folder, session_identifier):
    """ Terminate the task gracefully and retrieve the EDF data file

    file_to_retrieve: The EDF on the Host that we would like to download
    win: the current window used by the experimental script
    """

    if self.el_tracker.isConnected():
      # Terminate the current trial first if the task terminated prematurely
      error = self.el_tracker.isRecording()
      if error == pylink.TRIAL_OK:
        self.abort_trial(win)

      # Put tracker in Offline mode
      self.el_tracker.setOfflineMode()

      # Clear the Host PC screen and wait for 500 ms
      self.el_tracker.sendCommand('clear_screen 0')
      pylink.msecDelay(500)

      # Close the edf data file on the Host
      self.el_tracker.closeDataFile()

      # Show a file transfer message on the screen
      msg = pm.TERMINATE_TASK
      self.show_msg(win, msg, wait_for_keypress=False)

      # Download the EDF data file from the Host PC to a local data folder
      # parameters: source_file_on_the_host, destination_file_on_local_drive
      local_edf = os.path.join(session_folder, session_identifier + '.EDF')
      try:
        self.el_tracker.receiveDataFile(edf_file, local_edf)
      except RuntimeError as error:
        print('ERROR:', error)

      # Close the link to the tracker.
      self.el_tracker.close()

    # close the PsychoPy window
    win.close()

    # quit PsychoPy
    core.quit()
    sys.exit()

  def abort_trial(self, win):
    """Ends recording """

    # Stop recording
    if self.el_tracker.isRecording():
      # add 100 ms to catch final trial events
      pylink.pumpDelay(100)
      self.el_tracker.stopRecording()

    # clear the screen
    self.clear_screen(win)
    # Send a message to clear the Data Viewer screen
    bgcolor_RGB = (116, 116, 116)
    self.el_tracker.sendMessage('!V CLEAR %d %d %d ' % bgcolor_RGB)

    # send a message to mark trial end
    self.el_tracker.sendMessage('TRIAL_RESULT %d ' % pylink.TRIAL_ERROR)

    return pylink.TRIAL_ERROR

  def _update(self, trial_nr, mouse_pos, target_pos, global_timer, block, gaze_x, gaze_y, state_marker, button_pressed, start_time):
    '''
    Create new csv file if needed and add new row of data
    '''
    # Get current position of mouse
    mouse_x_cm, mouse_y_cm = ds.get_pos_cm(mouse_pos, self.win)
    # Define filename/-path of a trial, create path if it does not exist yet
    file_name = f"participant_{self.participant_id}_block_{block}_trial_{trial_nr}_trajectory.csv"
    file_path = os.path.join(self.data_dir, file_name)
    file_exists = os.path.exists(file_path)
    # Open csv file
    with open(file_path, "a", newline="") as f:
      writer = csv.writer(f)
      #write first line of csv file if not written yet
      if not file_exists:
        writer.writerow([
        "trial",
        "block",
        "time",
        "cursor_x_pix",
        "cursor_y_pix",
        "cursor_x_cm",
        "cursor_y_cm",
        "gaze_x",
        "gaze_y",
        "target_x",
        "target_y",
        "state_marker",
        "button_pressed",
        "start_time"
        ])
        # add row of data
      writer.writerow([
      trial_nr,
      block,
      global_timer.getTime(),
      mouse_pos[0],
      mouse_pos[1],
      mouse_x_cm,
      mouse_y_cm,
      gaze_x,
      gaze_y,
      target_pos[0],
      target_pos[1],
      state_marker,
      button_pressed,
      start_time
      ])

  def _run_trial(self, block, global_timer, trial_nr, mouse, cursor, start_point, chosen_target, radius):

    self.el_tracker.sendCommand('clear_screen 0 ')
    self.el_tracker.sendMessage('TRIAL_ID %d ' % trial_nr)
    pylink.pumpDelay(100)
    
    status_msg = 'TRIAL number %d ' % trial_nr
    self.el_tracker.sendCommand("record_status_message '%s' " % status_msg)
    
    timer = core.Clock()
    keys = event.getKeys(keyList=['return'])
    
    left = int(self.scn_width/2.0) - 60
    top = int(self.scn_height/2.0) - 60
    right = int(self.scn_width/2.0) + 60
    bottom = int(self.scn_height/2.0) + 60
    ia_pars = (1, left, top, right, bottom, 'screen_center')
    self.el_tracker.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s ' % ia_pars)
    
    trial_done = False
    
    # Zustand initialisieren und die erste Nachricht genau einmal feuern
    state = "start"
    self.el_tracker.sendMessage('START_POINT_ONSET ') 
    change_state_timer = None
    trial_duration_timer = None
    
    # Flag für den Startpunkt/Target
    mouse_in_start = False 
    mouse_in_target = False
    start_time = np.random.uniform(low=pm.START_TRIAL_LOW,high=pm.START_TRIAL_HIGH)
    while not trial_done:
      if 'escape' in event.getKeys():
        self.el_tracker.stopRecording()
        self.terminate_task(win=self.win, edf_file=self.edf_file, session_folder=self.data_dir, session_identifier=self.session_identifier)
      
      mouse_pos = mouse.getPos()
      
      # Eyetracker Abfragen
      if pm.DUMMY_MODE:
        gaze_x, gaze_y = mouse_pos[0], mouse_pos[1]
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
            gaze_x = raw_x - (self.scn_width / 2.0)
            gaze_y = (self.scn_height / 2.0) - raw_y
          else:
            gaze_x, gaze_y = -999, -999
        else:
          gaze_x, gaze_y = -999, -999

      cursor.setPos(mouse_pos)
      
      # --- Status-Marker für die CSV-Datei berechnen ---
      flat_mouse = [float(x) for x in np.asarray(mouse_pos).ravel()]
      flat_target = [float(x) for x in np.asarray(chosen_target.pos).ravel()]
      scalar_radius = float(np.asarray(radius).ravel()[0])
      
      if state == "start":
        if ds.is_mouse_in_object(mouse_pos, start_point.pos, start_point.radius):
          state_marker = 1
        else:
          state_marker = 0
      elif state == "hold":
        state_marker = 1
      elif state == "targets":
        if ds.is_mouse_in_object(flat_mouse, flat_target, scalar_radius):
          state_marker = 4
        elif ds.is_mouse_in_object(mouse_pos, start_point.pos, start_point.radius):
          state_marker = 2
        else:
          state_marker = 3
      # mouse button pressed?
      button_pressed = bool(mouse.getPressed()[0])# is left mouse button pressed
      self._update(trial_nr, mouse_pos, chosen_target.pos, global_timer, block, gaze_x, gaze_y, state_marker, button_pressed, start_time)
      
      if state == "start":
        start_point.draw()
        cursor.draw()
        
        if ds.is_mouse_in_object(mouse_pos, start_point.pos, start_point.radius):
          if not mouse_in_start:
            self.el_tracker.sendMessage('CURSOR_IN_START_POINT ')
            mouse_in_start = True
            
          if mouse.isPressedIn(start_point,buttons=[0]):
            self.el_tracker.sendMessage('BUTTON_PRESSED_IN_START_POINT')
            change_state_timer = core.Clock()
            state = "hold"
        else:
          mouse_in_start = False

      elif state == "hold":
        if change_state_timer.getTime() >= start_time:
          state = "targets"
          self.el_tracker.sendMessage('START_POINT_END ')
          self.el_tracker.sendMessage('TARGET_ONSET ')
          trial_duration_timer = core.Clock()
          change_state_timer = None
        start_point.draw()
        cursor.draw()

      elif state == "targets" and chosen_target:
        chosen_target.draw()
        cursor.draw()
        

        time_out = pm.TIMEOUT
        
        if trial_duration_timer.getTime() >= time_out:
          ds.blank_screen(self.win)
          ds.target_not_reached(self.win)
          ds.blank_screen(self.win)
          self.el_tracker.sendMessage('TIME_OUT ')
          state = "start"
          self.el_tracker.sendMessage('START_POINT_ONSET ')
          trial_done = True
          trial_duration_timer = None

        if ds.is_mouse_in_object(flat_mouse, flat_target, scalar_radius):

          # update target flag
          if not mouse_in_target:
            self.el_tracker.sendMessage('CURSOR_IN_TARGET ')
            mouse_in_target = True

          # initialise timer
          if change_state_timer is None:
            change_state_timer = core.Clock()

          # target timer
          if change_state_timer.getTime() >= pm.END_TRIAL:
              self.el_tracker.sendMessage('TARGET_END ')
              ds.blank_screen(self.win)
              ds.target_reached(self.win)
              ds.blank_screen(self.win)
              self.el_tracker.sendMessage('TRIAL_END ')
              state = "start"
              trial_done = True
              change_state_timer = None

          else:
            # left target when in already
            if mouse_in_target:
              self.el_tracker.sendMessage('CURSOR_LEFT_TARGET ')
              mouse_in_target = False

      
      self.win.flip()

      if 'escape' in keys:
        self.el_tracker.stopRecording()
        self.terminate_task(win=self.win, edf_file=self.edf_file, session_folder=self.data_dir, session_identifier=self.session_identifier)
        return

    # Die Einrückung wurde hier aufgehoben. Diese Zeilen laufen erst nach trial_done.
    self.el_tracker.sendMessage("STIM_END ")
    self.el_tracker.stopRecording()
    self.el_tracker.sendMessage('TRIAL_RESULT %d ' % pylink.TRIAL_OK)

  def _run_block(self, block, global_timer,practice=False):
    #create mouse and cursor
    mouse = ds.create_mouse(win=self.win)
    cursor = ds.create_cursor(win=self.win)

    # choose practice or trial parameters
    if not practice:
      n_trials = pm.TRIALS_PER_BLOCK[block]
      target_width = pm.TARGET_WIDTH_PER_BLOCK[block]
    else: # if practice
      n_trials = pm.PRACTICE_TRIALS
      target_width = pm.PRACTICE_TARGET_WIDTH

    # create targets
    targets = ds.create_targets_random(self.win,n_trials,target_width)
    
    #run trial
    for trial in range(n_trials):
      start_point = ds.create_starting_point(self.win)
      chosen_target = ds.choose_target(targets)
      
      radius = chosen_target.size * (2/3) #
      
      # put the tracker in the offline mode first
      self.el_tracker.setOfflineMode()

      # Start recording
      # arguments: sample_to_file, events_to_file, sample_over_link,
      # event_over_link (1-yes, 0-no)
      try:
        self.el_tracker.startRecording(1, 1, 1, 1)
      except RuntimeError as error:
        print("ERROR:", error)
        self.abort_trial(self.win)
      # Allocate some time for the tracker to cache some samples
      pylink.pumpDelay(100)
      if trial == 0:
        self.el_tracker.sendMessage('BLOCK_ID %d ' % block)
        pylink.pumpDelay(10)
      self._run_trial(block=block, global_timer=global_timer, trial_nr=trial, mouse=mouse, cursor=cursor, start_point=start_point, chosen_target=chosen_target, radius=radius)
  
  def _run_exp(self):
    self.el_tracker = self.connect_to_eyelink()
    self.session_identifier, self.edf_file = self.host_open_edf(participant_id=self.participant_id)
    self.preamble_text()
    self.el_tracker.setOfflineMode()
    self.get_software_version()
    self.scn_width, self.scn_height = self.screen_res(self.win)
    self.el_coords, self.dv_coords, self.genv, self.foreground_color, self.background_color = self.graph_env()
    self.set_calib_target(genv=self.genv)
    self.show_msg(self.win, pm.INSTRUCTION)
    self.calibrate(self.win)
    global_timer = core.Clock()
    
    # Practice block
    practice_msg = f"Let's begin with a Practice Block with " + str(pm.PRACTICE_TRIALS)+ " trials\n Press the Home Button to continue."
    self.show_msg(self.win, practice_msg)
    self._run_block(
    block=-1,
    global_timer=global_timer,
    practice=True
    )

    practice_completed_msg = "Practice trials Completed! We will now begin the experiment\n Press the Home Button to continue."
    self.show_msg(self.win, practice_completed_msg)
    for block in range(pm.BLOCKS):
      block_msg = f"Block {block + 1}\n Press the Home Button to continue."
      self.show_msg(self.win, block_msg)
      self._run_block(block=block, global_timer=global_timer)
    # disconnect, download the EDF file, then terminate the task
    self.terminate_task(win=self.win, edf_file=self.edf_file, session_folder=self.data_dir, session_identifier=self.session_identifier)

    # 5️ Funktion sauber beenden → kein return nötig
    return
  
  def connect_to_eyelink(self) -> pylink.EyeLink:
    if pm.DUMMY_MODE:
      return pylink.EyeLink(None)
    else:
      try:
        return pylink.EyeLink("100.1.1.1")
      except RuntimeError as error:
        print('ERROR:', error)
        core.quit()
        sys.exit()

  # Step 2: Open an EDF data file on the Host PC
  def host_open_edf(self, participant_id):
    session_identifier = participant_id + "_data_eyetracking"
    edf_file = participant_id + ".EDF"
    try:
      self.el_tracker.openDataFile(edf_file)
    except RuntimeError as err:
      print('ERROR:', err)
      # close the link if we have one open
      if self.el_tracker.isConnected():
        self.el_tracker.close()
      core.quit()
      sys.exit()
    return session_identifier, edf_file

  def preamble_text(self):
    preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
    self.el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)

  def get_software_version(self):
    eyelink_ver = 0  # set version to 0, in case running in Dummy mode
    if not pm.DUMMY_MODE:
      vstr = self.el_tracker.getTrackerVersionString()
      eyelink_ver = int(vstr.split()[-1].split('.')[0])
      # print out some version info in the shell
      print('Running experiment on %s, version %d' % (vstr, eyelink_ver))
    # File and Link data control
    # what eye events to save in the EDF file, include everything by default
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # what eye events to make available over the link, include everything by default
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    # what sample data to save in the EDF data file and to make available
    # over the link, include the 'HTARGET' flag to save head target sticker
    # data for supported eye trackers
    if eyelink_ver > 3:
      file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
      link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
      file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
      link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    self.el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
    self.el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
    self.el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
    self.el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

    # Optional tracking parameters
    # Sample rate, 250, 500, 1000, or 2000, check your tracker specification
    # if eyelink_ver > 2:
    #     el_tracker.sendCommand("sample_rate 1000")
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    self.el_tracker.sendCommand("calibration_type = HV9")
    # Set a gamepad button to accept calibration/drift check target
    # You need a supported gamepad/button box that is connected to the Host PC
    self.el_tracker.sendCommand("button_function 5 'accept_target_fixation'")
      
  def screen_res(self, win):
    # get the native screen resolution used by PsychoPy
    scn_width, scn_height = win.size
    # resolution fix for Mac retina displays
    if 'Darwin' in platform.system():
      if pm.USE_RETINA:
        scn_width = int(scn_width/2.0)
        scn_height = int(scn_height/2.0)
    return scn_width, scn_height

  def graph_env(self):
    # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
    # see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d " % (self.scn_width - 1, self.scn_height - 1)
    self.el_tracker.sendCommand(el_coords)

    # Write a DISPLAY_COORDS message to the EDF file
    # Data Viewer needs this piece of info for proper visualization, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    dv_coords = "DISPLAY_COORDS  0 0 %d %d " % (self.scn_width - 1, self.scn_height - 1)
    self.el_tracker.sendMessage(dv_coords)

    # Configure a graphics environment (genv) for tracker calibration
    genv = EyeLinkCoreGraphicsPsychoPy(self.el_tracker, self.win)
    print(genv)  # print out the version number of the CoreGraphics library

    # Set background and foreground colors for the calibration target
    # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
    foreground_color = (-1, -1, -1)
    background_color = self.win.color
    genv.setCalibrationColors(foreground_color, background_color)
    return el_coords, dv_coords, genv, foreground_color, background_color

  def set_calib_target(self, genv):
    # Set up the calibration target
    #
    # The target could be a "circle" (default), a "picture", a "movie" clip,
    # or a rotating "spiral". To configure the type of calibration target, set
    # genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
    # genv.setTargetType('picture')
    #
    # Use gen.setPictureTarget() to set a "picture" target
    # genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))
    #
    # Use genv.setMovieTarget() to set a "movie" target
    # genv.setMovieTarget(os.path.join('videos', 'calibVid.mov'))

    # Use a picture as the calibration target
    genv.setTargetType('picture')
    genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))

    # Configure the size of the calibration target (in pixels)
    # this option applies only to "circle", "spiral", and "movie" targets
    # genv.setTargetSize(24)

    # Beeps to play during calibration, validation and drift correction
    # parameters: target, good, error
    #     target -- sound to play when target moves
    #     good -- sound to play on successful operation
    #     error -- sound to play on failure or interruption
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    genv.setCalibrationSounds('', '', '')
    
    # resolution fix for macOS retina display issues
    if pm.USE_RETINA:
      genv.fixMacRetinaDisplay()

    # Request Pylink to use the PsychoPy window we opened above for calibration
    pylink.openGraphicsEx(genv)