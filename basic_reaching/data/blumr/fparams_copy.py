USE_RETINA = False
DUMMY_MODE = False

###############################################
################### WINDOW ####################
###############################################
FULLSCREEN = True
BACKGROUND_COLOR = 'grey'
UNITS = 'pix'
TEXT_COLOR = 'white'
BACKGROUND_SQUARES_SIZE = 2
MEAN_LUM = 0.5
SCREEN_WIDTH = 59.7 #cm
SCREEN_HEIGHT = 33.7 #cm
VIEW_DISTANCE = 70 # cm ???? check in continuous task
RESOLUTION_X = 2560
RESOLUTION_Y = 1440

###############################################
################## TEXTBOXES ##################
###############################################
INSTRUCTION = "Press the home button to continue."
CALIBRATION = 'We will first calibrate the eyetracker.\n' + \
                'Then the experiment will start.\n'
CALIBRATION_DUMMY_MODE = '\nNow, press the home button to start the task'
CALIBRATION_NO_DUMMY_MODE = '\nNow, press the home button twice to calibrate tracker'
TERMINATE_TASK = 'EDF data is transferring from EyeLink Host PC...'
FEEDBACK_TEXT_TARGET_REACHED = "You have reached the target"
FEEDBACK_TEXT_TIMEOUT = "Time out"

###############################################
################### STIMULI ###################
###############################################
# TARGETS_X_POS = [-730, -632, -365, 0, 365, 632, 730] #pix
# TARGETS_Y_POS = [-370, -5, 262, 360, 262, -5, -370] #pix
TARGETS_RANGE = 1/3                    # pix
TARGETS_DISTANCE = 600             # pix
TARGET_WIDTH_PER_BLOCK = [0.2, 0.3, 0.4, 0.5] # Width in DEGREES
CIRCLE_COLOR = 'white'
FEEDBACK_TIME = 2 # sec
FEEDBACK_POS = (0, 0)
FEEDBACK_ALIGNMENT = 'center'
FEEBACK_REACHED_COLOR = '#023020'
FEEBACK_TIMEOUT_COLOR = [1.0,-1,-1]

###############################################
################### TRIALS ####################
###############################################
START_TRIAL_LOW = 0.5 # seconds
START_TRIAL_HIGH = 1.5 # seconds 
END_TRIAL = 0.45 # seconds
TIMEOUT = 4 # seconds
MOUSE_VISIBLE = False
CURSOR_COLOR = 'black'
CURSOR_RADIUS = 7 #pix
STARTING_POINT_COLOR = '#023020'
STARTING_POINT_POS = [0,-360] #pix
STARTING_POINT_RADIUS = 15 #pix
BLOCKS = 4
TRIALS_PER_BLOCK = [30, 30, 30, 30]
PRACTICE_TRIALS = 3
PRACTICE_TARGET_WIDTH = 0.1
