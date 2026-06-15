import numpy as np


class RandomWalker:
    """
    Gaussian random walk.
    
    $$
    \\begin{align*}
    
    pos &= \\alpha \\cdot pos + dt \\cdot vel + \\sqrt{dt} \\cdot \\varepsilon  & \\varepsilon \\sim \\mathcal{N}(0, \\sigma_{pos}) \\
    vel &= \\beta \\cdot vel + \\sqrt{dt} \\cdot \\eta & \\eta \\sim \\mathcal{N}(0, \\sigma_{vel})
    
    \\end{align*}
    $$
    """

    def __init__(
        self,
        std_pos: float = 0.5,
        std_vel: float = 0.0,
        dt: float = 1 / 60,
        alpha: float = 1.0,
        beta: float = 1.0,
    ) -> None:
        """
        2D random walk.

        Args:
            std_pos (float, optional): Change in position. Defaults to 0.5.
            std_vel (float, optional): Change in velocity. Defaults to 0.0.
            dt (float, optional): Duration of time steps. Defaults to 1/60.
            alpha (float, optional): "Damping" of position. Defaults to 1.0.
            beta (float, optional): "Damping" of velocity. Defaults to 1.0.
        """
        self.rng = np.random.default_rng()

        self.std_pos = std_pos
        self.std_vel = std_vel
        self.dt = dt
        self.alpha = alpha
        self.beta = beta

        self.dim = 2
        self.pos = np.zeros(self.dim)
        self.vel = np.zeros(self.dim)

    def __str__(self) -> str:
        """
        Returns:
            str: String representation.
        """
        s = (
            f"{self.__class__.__name__} "
            f"({self.std_pos=}, {self.std_vel=}, {self.dt=}, {self.alpha=}, {self.beta=})"
        )
        return s

    def walk(self) -> None:
        """
        Performs one step, i.e. calculates the next position.
        """
        pos_next = (
            self.alpha * self.pos
            + self.dt * self.vel
            + np.sqrt(self.dt) * self.rng.normal(scale=self.std_pos, size=self.dim)
        )
        vel_next = self.beta * self.vel + np.sqrt(self.dt) * self.rng.normal(
            scale=self.std_vel, size=self.dim
        )

        self.pos = pos_next
        self.vel = vel_next


if __name__ == "__main__":
    rw = RandomWalker()
    print(rw)
    print(rw.pos)
    rw.walk()
    print(rw.pos)
