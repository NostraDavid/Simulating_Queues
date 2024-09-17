import pyglet
import random
import queue
from pyglet import shapes
from dataclasses import dataclass

# Constants for queue behavior
ARRIVAL_RATE = 1 / 2  # Average of 2 seconds between arrivals (lambda)
SERVICE_RATE = 1 / 3  # Average of 3 seconds service time (mu)
MOVE_SPEED = 200  # Speed at which the customers move to the server

BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


@dataclass
class Vector2D:
    x: float
    y: float

    def move_toward(self, target: "Vector2D", speed: float, dt: float) -> bool:
        """Move this vector toward the target vector at the given speed."""
        if self.x < target.x:
            self.x += speed * dt
        elif self.x > target.x:
            self.x -= speed * dt

        return abs(self.x - target.x) < 1e-2  # Consider it reached if very close


class Customer:
    def __init__(self, position: Vector2D, radius: float, batch: pyglet.graphics.Batch):
        self.position = position
        self.shape = shapes.Circle(
            position.x, position.y, radius, color=BLUE, batch=batch
        )
        self.target = position

    def move_toward(self, target: Vector2D, dt: float) -> bool:
        """Move the customer toward the target position."""
        reached = self.position.move_toward(target, MOVE_SPEED, dt)
        self.shape.x = self.position.x
        return reached


class MM1Queue:
    """Represents the M/M/1 queue system."""

    def __init__(
        self,
        start_x: float,
        end_x: float,
        y: float,
    ):
        self.start_position = Vector2D(start_x, y)
        self.end_position = Vector2D(end_x, y)
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
            position = Vector2D(self.start_position.x, self.start_position.y)
            customer = Customer(position, 20, self.batch)
            customer.target = Vector2D(
                self.start_position.x - self.queue.qsize() * 50, self.start_position.y
            )
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
        self.queue_system = MM1Queue(start_x, end_x, self.height // 2)

    def on_draw(self):
        self.clear()
        self.queue_system.draw()

    def update(self, dt: float):
        self.queue_system.update(dt)


# Create a fullscreen window
window = QueueSimulationWindow(
    start_x=300,  # Start position of the queue
    end_x=700,  # End position (server) of the queue
    fullscreen=True,
    caption="M/M/1 Queue Simulation",
)

# Schedule the update function to run every 1/60 of a second
pyglet.clock.schedule_interval(window.update, 1 / 60)

# Start the Pyglet application
if __name__ == "__main__":
    pyglet.app.run()
