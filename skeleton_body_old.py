import pymunk
from typing import Literal


class SkeletonBody:
    def __init__(
        self,
        space: pymunk.Space,
        position: tuple[float, float] = (0, 0),
        mass: float = 1.0,
        radius: float = 10.0,
        elasticity: float = 0.3,
        friction: float = 0,
        damping: float = 1,
    ):
        """
        A Body object that holds the physics representation of the skeleton.

        Parameters:
        - skeleton: The Skeleton object that this body will be associated with.
        - mass: The mass of the body for physics simulation.
        - radius: The radius for the collision shape (for simplicity, assuming a circular shape).
        - position: The initial position of the body.
        """
        self.space = space

        self.body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        self.shape.collision_type = 1
        self.space.add(self.body, self.shape)

        self.body.position = pymunk.Vec2d(*position)
        self.normal_damping = damping

        # Track collision state
        self.is_colliding = False

        # Set up collision handlers
        self._setup_collision_handlers()

    def _setup_collision_handlers(self):
        """Set up collision handlers for the body."""
        collision_handler = self.space.add_collision_handler(
            1, 2
        )  # Player (1) with Wall (2)

        collision_handler.begin = self._on_collision_begin
        collision_handler.separate = self._on_collision_end
        collision_handler.pre_solve = (
            self._on_collision_pre_solve
        )  # New handler during collision

    def _on_collision_begin(self, arbiter, space, data):
        """Callback when collision begins."""
        return True  # Continue processing the collision

    def _on_collision_pre_solve(self, arbiter, space, data):
        """Callback that occurs while the collision is happening."""
        self.body.velocity = pymunk.Vec2d(0, 0)
        return True  # Continue processing the collision

    def _on_collision_end(self, arbiter, space, data):
        """Callback when collision ends."""
        self.is_colliding = False
        # self.body.angular_velocity = 0  # Reset angular velocity
        # self.body.force = pymunk.Vec2d(0, 0)
        # self.body.torque = 0
        # self.body.velocity = pymunk.Vec2d(0, 0)

        return True

    def update(self, dt):
        """Update the body position and resolve collisions."""
        self.space.step(dt)
        print(self.shape.friction)
        self.limit_speed()

    def set_damping(self, damping: float | Literal["normal"] = "normal"):
        """Set the damping of the body."""
        if damping == "normal":
            self.damping = self.normal_damping
            return
        self.damping = damping

    def apply_force(self, force: pymunk.Vec2d):
        """Apply a force to the body."""
        self.body.apply_force_at_local_point(force)

    def set_velocity(self, velocity: pymunk.Vec2d):
        """Set the velocity of the body."""
        self.body.velocity = velocity

    def set_max_velocity(self, max_velocity: float):
        """Set the maximum speed for the body."""
        self.max_velocity = max_velocity

    def limit_speed(self):
        """Limit the body's speed to the set maximum speed."""
        if self.max_velocity is not None:
            current_speed = self.body.velocity.length
            if current_speed > self.max_velocity:
                self.body.velocity = self.body.velocity.normalized() * self.max_velocity
