import pyglet
import random
import queue
from pyglet import shapes

# Constants for queue behavior
ARRIVAL_RATE = 1 / 2  # Average of 2 seconds between arrivals (lambda)
SERVICE_RATE = 1 / 3  # Average of 3 seconds service time (mu)
MOVE_SPEED = 200  # Speed at which the customers move to the server

BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


class Customer:
    def __init__(self, x: float, y: float, radius: float, batch: pyglet.graphics.Batch):
        self.shape = shapes.Circle(x, y, radius, color=BLUE, batch=batch)
        self.target_x = x

    def move_toward(self, target_x: float, dt: float) -> bool:
        """Move the customer toward the target x position smoothly."""
        if self.shape.x < target_x:
            self.shape.x += MOVE_SPEED * dt
            return False  # Not yet at the target
        elif self.shape.x > target_x:
            self.shape.x -= MOVE_SPEED * dt
        return self.shape.x == target_x  # Reached the target


class MM1Queue:
    """Represents the M/M/1 queue system."""

    def __init__(
        self,
        start_x: float,
        end_x: float,
        y: float,
    ):
        self.start_x = start_x  # Where customers enter the queue
        self.end_x = end_x  # Where the server is located
        self.y = y  # Vertical position of the queue and server
        self.queue: queue.Queue[Customer] = queue.Queue()  # FIFO queue for customers
        self.server = None  # The customer currently being served
        self.batch = pyglet.graphics.Batch()  # Batch for efficient drawing
        self.next_arrival_time = random.expovariate(ARRIVAL_RATE)
        self.next_service_time = None

        # Shapes for the start and end points (visualized)
        self.queue_entry = shapes.Rectangle(
            self.start_x - 5, self.y - 25, 10, 50, color=RED, batch=self.batch
        )
        self.server_box = shapes.Rectangle(
            self.end_x - 25, self.y - 25, 50, 50, color=GREEN, batch=self.batch
        )

    def add_customer(self):
        """Add a new customer to the queue."""
        if self.queue.qsize() < 10:  # Limit queue size for visualization
            customer = Customer(self.start_x, self.y, 20, self.batch)
            customer.target_x = (
                self.start_x - self.queue.qsize() * 50
            )  # Position them in line
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
            self.server.target_x = self.end_x  # Move customer to server
            self.next_service_time = random.expovariate(SERVICE_RATE)

        if self.server:
            # Move the customer to the server smoothly
            if self.server.move_toward(self.server.target_x, dt):
                self.next_service_time -= dt
                if self.next_service_time <= 0:
                    # Customer has been served
                    self.server = None

        # Update customers in the queue to move forward if needed
        for i in range(self.queue.qsize()):
            customer = self.queue.queue[i]
            customer.target_x = self.start_x - i * 50
            customer.move_toward(customer.target_x, dt)

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
