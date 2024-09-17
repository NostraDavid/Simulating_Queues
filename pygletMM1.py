import pyglet
import random
import queue
from pyglet import shapes
from dataclasses import dataclass
from math import sqrt, atan2, degrees

# Constants for queue behavior
ARRIVAL_RATE = 1 / 2  # Average of 2 seconds between arrivals (lambda)
SERVICE_RATE = 1 / 3  # Average of 3 seconds service time (mu)
MOVE_SPEED = 200  # Speed at which the customers move to the server

BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


@dataclass
class Vector2D:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vector2D") -> "Vector2D":
        """Add two vectors."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        """Subtract one vector from another."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2D":
        """Multiply vector by a scalar."""
        return Vector2D(self.x * scalar, self.y * scalar)

    def dot(self, other: "Vector2D") -> float:
        """Dot product of two vectors."""
        return self.x * other.x + self.y * other.y

    def magnitude(self) -> float:
        """Magnitude (length) of the vector."""
        return sqrt(self.x**2 + self.y**2)

    def normalize(self) -> "Vector2D":
        """Return a normalized vector (unit vector)."""
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return self * (1 / mag)

    def angle(self) -> float:
        """Return the angle of the vector in degrees from the positive x-axis."""
        return degrees(atan2(self.y, self.x))


class Customer:
    def __init__(
        self,
        spawn_position: Vector2D,
        queue_position: Vector2D,
        radius: float,
        batch: pyglet.graphics.Batch,
    ):
        self.position = spawn_position
        self.shape = shapes.Circle(
            spawn_position.x, spawn_position.y, radius, color=BLUE, batch=batch
        )
        self.target = queue_position  # Initially moving towards queue position

    def move_toward(self, target: Vector2D, dt: float) -> bool:
        """Move the customer toward the target position."""
        direction = target - self.position  # Calculate direction vector
        distance = direction.magnitude()  # Calculate distance to target

        if distance > 0:
            move_vector = (
                direction.normalize() * MOVE_SPEED * dt
            )  # Move in the direction of the target
            self.position += move_vector  # Update position
            self.shape.x, self.shape.y = self.position.x, self.position.y

        # Check if we have reached the target
        return distance < 1.0  # Consider target reached if within 1 pixel


class MM1Queue:
    """Represents the M/M/1 queue system."""

    def __init__(
        self,
        start_position: Vector2D,
        end_position: Vector2D,
        window_height: float,
    ):
        self.start_position = start_position  # Queue start position (Vector2D)
        self.end_position = end_position  # Queue end position (Vector2D)
        self.spawn_position = Vector2D(
            0, window_height
        )  # Spawn in the upper-left corner
        self.queue: queue.Queue[Customer] = queue.Queue()  # FIFO queue for customers
        self.server = None  # The customer currently being served
        self.batch = pyglet.graphics.Batch()  # Batch for efficient drawing
        self.next_arrival_time = random.expovariate(ARRIVAL_RATE)
        self.next_service_time = None

        # Shapes for the start and end points (visualized)
        self.queue_entry = shapes.Rectangle(
            self.start_position.x - 5,
            self.start_position.y - 25,
            10,
            50,
            color=RED,
            batch=self.batch,
        )
        self.server_box = shapes.Rectangle(
            self.end_position.x - 25,
            self.end_position.y - 25,
            50,
            50,
            color=GREEN,
            batch=self.batch,
        )

    def add_customer(self):
        """Add a new customer to the queue."""
        if self.queue.qsize() < 10:  # Limit queue size for visualization
            position_in_queue = Vector2D(
                self.start_position.x - self.queue.qsize() * 50, self.start_position.y
            )
            customer = Customer(self.spawn_position, position_in_queue, 20, self.batch)
            self.queue.put(customer)

    def update(self, dt: float):
        """Update the queue system and move customers."""
        # Handle customer arrivals
        self.next_arrival_time -= dt
        if self.next_arrival_time <= 0:
            self.add_customer()
            self.next_arrival_time = random.expovariate(ARRIVAL_RATE)

        # Handle serving customers
        if self.server is None and not self.queue.empty():
            self.server = self.queue.get()
            self.server.target = self.end_position  # Move customer to server
            self.next_service_time = random.expovariate(SERVICE_RATE)

        if self.server:
            # Move the customer to the server smoothly
            if self.server.move_toward(self.server.target, dt):
                self.next_service_time -= dt
                if self.next_service_time <= 0:
                    # Customer has been served
                    self.server = None

        # Update customers in the queue to move forward if needed
        for i in range(self.queue.qsize()):
            customer = self.queue.queue[i]
            customer.target = Vector2D(
                self.start_position.x - i * 50, self.start_position.y
            )
            customer.move_toward(customer.target, dt)

    def draw(self):
        """Draw all elements in the system."""
        self.batch.draw()


class QueueSimulationWindow(pyglet.window.Window):
    """Main window to run the M/M/1 queue simulation."""

    def __init__(self, start_x: float, end_x: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        window_height = self.height
        start_position = Vector2D(start_x, window_height // 2)
        end_position = Vector2D(end_x, window_height // 2)
        self.queue_system = MM1Queue(start_position, end_position, window_height)

    def on_draw(self):
        self.clear()
        self.queue_system.draw()

    def update(self, dt: float):
        self.queue_system.update(dt)


# Create a fullscreen window
window = QueueSimulationWindow(
    start_x=0,  # Start position at the queue
    end_x=700,  # End position (server) of the queue
    fullscreen=True,
    caption="M/M/1 Queue Simulation",
)

# Schedule the update function to run every 1/60 of a second
pyglet.clock.schedule_interval(window.update, 1 / 60)

# Start the Pyglet application
if __name__ == "__main__":
    pyglet.app.run()
