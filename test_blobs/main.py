# main.py

from psychopy import visual, core, event

# Import from your stimulus.py file
from stimulus import make_gaussian_blob
from psychopy.hardware import keyboard
import display as ds
import params as pm
def main():
    # Create PsychoPy window
    win = ds.initialize_window()

    # # Create 3 Gaussian blobs with different sizes
    # blob_small = make_gaussian_blob(win, size=0.03)
    # blob_medium = make_gaussian_blob(win, size=0.07)
    # blob_large = make_gaussian_blob(win, size=0.12)

    # # Set positions
    # blob_small.pos = (-0.4, 0.0)
    # blob_medium.pos = (0.0, 0.0)
    # blob_large.pos = (0.4, 0.0)
    blob_width = pm.TARGET_WIDTH_PER_BLOCK[3]
    targets = ds.create_targets_random(win,pm.TRIALS_PER_BLOCK[0],blob_width)
    # Main loop
    while True:
        # Draw blobs
        # blob_small.draw()
        # blob_medium.draw()
        # blob_large.draw()
        for target in targets:
            target.draw()
        # Update screen
        win.flip()

        # Exit on any key press
        kb = keyboard.Keyboard()
        if kb.getKeys(keyList=["escape"]):
            win.close()
            core.quit()

    win.close()
    core.quit()


if __name__ == "__main__":
    main()