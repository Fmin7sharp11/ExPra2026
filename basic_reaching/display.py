from psychopy import prefs
prefs.hardware['audioLib'] = ['pyo', 'sounddevice']
prefs.general['audioLib'] = ['pyo', 'sounddevice']
from psychopy import visual, event, core, gui
import params as pm
import random
import numpy as np
from PIL import Image
import math
import stimulus

def initialize_window():
    # initialize PsychoPy window
    return visual.Window(fullscr=pm.FULLSCREEN, color = pm.BACKGROUND_COLOR, units=pm.UNITS)

def blank_screen(win: visual.Window):
    # displays a blank screen for half a second
    win.flip()
    core.wait(0.5)
    
def create_mouse(win: visual.Window):
    '''
    Creates mouse
    '''
    return event.Mouse(visible=pm.MOUSE_VISIBLE, win = win)

def create_cursor(win: visual.Window):
    '''
    Creates cursor
    '''
    return visual.Circle(win, fillColor = pm.CURSOR_COLOR, radius = pm.CURSOR_RADIUS)

#------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------#
#---------------------------------------Stimuli--------------------------------------------------#
#------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------#
def get_pos_cm(mouse_pos, win):
    '''
    Returns current position of the cursor in cm. Origin in the middle of the screen
    '''
    # Calculate cm per pixel of used monitor
    cm_per_pixel_x = pm.SCREEN_WIDTH / win.size[0]        #
    cm_per_pixel_y = pm.SCREEN_HEIGHT / win.size[1]       #
    return mouse_pos[0] * cm_per_pixel_x, mouse_pos[1] * cm_per_pixel_y
    
def is_mouse_in_object(mouse_pos, obj_pos, radius):
    '''
    Returns if mouse position in range of radius/2 of an object.
    '''
    # Calculate distance between position of the mouse and position of the object
    dist = np.sqrt((mouse_pos[0] - obj_pos[0])**2 + (mouse_pos[1] - obj_pos[1])**2)
    return dist <= radius / 2
    
def create_targets(win):
    '''
    Returns a list of different circle targets in different positions
    '''
    targets = []
    for n in range(len(pm.TARGETS_X_POS)):
        targets.append(visual.Circle(win, fillColor = pm.CIRCLE_COLOR, pos = (pm.TARGETS_X_POS[n], pm.TARGETS_Y_POS[n]), radius=10))
    return targets

def create_targets_random(win,num_targets,blob_width):
    """
    Returns a list of targets randomly drawn from a fixed circular arc in front of the start point.
    """
    targets = []
    
    # 1. Define the angle constraints based on parameters
    # pm.TARGET_RANGE is the fraction (e.g., 1/3), convert to radians
    arc_span = pm.TARGETS_RANGE * (2 * math.pi) 
    
    # Center the arc straight ahead (90 degrees or pi/2 radians)
    center_angle = math.pi / 2  
    min_angle = center_angle - (arc_span / 2)
    max_angle = center_angle + (arc_span / 2)
    
    # 2. Generate each target at a random angle within the arc
    for _ in range(num_targets):
        # Pick a random continuous angle inside the 1/3 arc limits
        random_angle = random.uniform(min_angle, max_angle)
        
        # Calculate coordinates using the fixed distance
        x = pm.STARTING_POINT_POS[0] + pm.TARGETS_DISTANCE * math.cos(random_angle)
        y = pm.STARTING_POINT_POS[1] + pm.TARGETS_DISTANCE * math.sin(random_angle)
        
        # Create the random blob target
        target = stimulus.make_gaussian_blob(win, 8)
        target.pos = [x,y]
        targets.append(target)
        
    return targets


def create_starting_point(win: visual.Window):
    '''
    Creates starting point
    '''
    return visual.Circle(win, fillColor = pm.STARTING_POINT_COLOR, pos = (pm.STARTING_POINT_POS[0], pm.STARTING_POINT_POS[1]), radius=pm.STARTING_POINT_RADIUS)

def create_targets(win: visual.Window):
    '''
    Returns a list of 5 different circle targets in 5 different positions
    '''
    targets = []
    for n in range(5):
        targets.append(visual.Circle(win, fillColor = pm.CIRCLE_COLOR, pos = (pm.TARGETS_X_POS[n], pm.TARGETS_Y_POS[n]), radius=10))
    return targets

def choose_target(targets):
    '''
    Returns a random target from the list. Sets a random size or opacity from a given list for the chosen target
    '''
    return random.choice(targets)

#------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------#
#-----------------------------------------Textboxes----------------------------------------------#
#------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------#
      
def target_reached(win: visual.Window):
    '''
    Displays feedback after a trial finished. The participant has reached the target.
    '''
    text = pm.FEEDBACK_TEXT_TARGET_REACHED
    stim = visual.TextBox2(win, text = text, color=pm.FEEBACK_REACHED_COLOR, pos=pm.FEEDBACK_POS, alignment=pm.FEEDBACK_ALIGNMENT)
    stim.draw()
    win.flip()
    core.wait(pm.FEEDBACK_TIME)
    
def target_not_reached(win: visual.Window):
    '''
    Displays feedback after a trial finished. The participant did not reach the target.
    '''
    text = pm.FEEDBACK_TEXT_TIMEOUT
    stim = visual.TextBox2(win, text = text, color=pm.FEEBACK_TIMEOUT_COLOR, pos=pm.FEEDBACK_POS, alignment=pm.FEEDBACK_ALIGNMENT)
    stim.draw()
    win.flip()
    core.wait(pm.FEEDBACK_TIME)
