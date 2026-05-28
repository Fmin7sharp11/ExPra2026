import math

import numpy as np
import scipy as sp
from psychopy import visual


def make_gaussian_blob(
    window: visual.Window, size: float, min_size: float = 0.1, blend_mode: str = "add"
) -> visual.GratingStim:
    """
    Way of creating blob stimuli. `size` should be >= `min_size`.
    Corresponds to `blob_type` 'gaussian'.
    `size` is the standard deviation of the Gaussian and `s` is the stimulus bounding box size.

    Args:
        window (visual.Window): Window to draw on.
        size (float): Standard deviation of the Gaussian.
        min_size (float, optional): Minimal possible size. Wider stimuli are computed relativ to
        this one. Defaults to 0.1.
        blend_mode (str, optional): Psychopy blend mode. Defaults to "add".

    Returns:
        visual.GratingStim: The created Stimulus.
    """
    # ± 3 standard deviations contain 99.7% of the mass
    # https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule
    s = size * 6
    min_s = min_size * 6

    if s == 0:
        # 'Perfectly' visible, black blob (radius equal to minimal blob size / 2)
        return visual.Circle(
            window,
            size=min_s / 4,  # TODO why 4? What was our rational?
            fillColor=-1,
            # fillColor=(1., -1., -1.),
            # lineWidth=0,
            lineColor=None,
        )

    if s == math.inf:
        # Invisible blob
        return visual.Circle(window, size=0)

    contrast = min_s / s
    return visual.GratingStim(
        win=window,
        size=s,
        mask="gauss",
        tex=None,
        contrast=contrast,
        blendmode=blend_mode,
        color=1,
    )


class FakeDistribution:
    """
    Mimics a scipy statistical distribution but alsways returns zeros. See usage in DotStimulus.
    """

    def rvs(self, *args, **kwargs):
        return np.zeros((1, 2))


class DotStimulus:
    # Adapted from Locke et al. (2020)

    def __init__(
        self, window: visual.Window, std: float = 0.5, num_dots: int = 2, life_time: int = 1
    ) -> None:
        """
        Args:
            window (visual.Window): PsychoPy window instance to draw to.
            std (List[float], optional): Standard deviation of multivariate Gaussian. Might aswell be
            list of diagonal arrays or single value. Defaults to 0.5.
            num_dots (int, optional): Number of points to draw and display. Defaults to 2.
            life_time (int, optional): Number of frames until new points are drawn. Defaults to 1.
        """
        # self.window = window
        self.pos = np.zeros(2)

        if std == 0 or std == [0, 0]:
            # Only one dot without variation
            self.dist = FakeDistribution()
            self.num_dots = 1

            fill_color = -1
        else:
            self.dist = sp.stats.multivariate_normal(mean=[0.0, 0.0], cov=np.square(std))
            self.num_dots = num_dots

            fill_color = 1

        self.circles = [
            visual.Circle(window, radius=0.1, fillColor=fill_color, lineColor=None)
            for c in range(self.num_dots)
        ]
        self.dots = self.dist.rvs(self.num_dots)

        self.life_time = life_time
        self.frame = 0

    def draw(self) -> None:
        """
        Draw the stimulus to the window. Mimics the draw function of psychopy stimuli.
        """
        if self.frame % self.life_time == 0:
            # Slowing it down
            self.dots = self.dist.rvs(self.num_dots)

        poss = self.dots + self.pos

        for pos, circle in zip(poss, self.circles):
            circle.pos = pos
            circle.draw()

        self.frame += 1
