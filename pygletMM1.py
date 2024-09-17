"""
M/M/1 Queue Simulation

I need:

- entry (area?)
- queue location (position in area?)
- service point
- exit (area?)
- customer
- some vector to move stuff
- a queue to hold customers
"""

import pyglet
import random
import queue
from pyglet import shapes
from dataclasses import dataclass
from math import sqrt, atan2, degrees
from pydantic_settings import SettingsConfigDict, BaseSettings
import json


# Step 1: Define Pydantic settings model
class SimulationSettings(BaseSettings):
    arrival_rate: float
    service_rate: float
    move_speed: int
    window_width: int
    window_height: int
    queue_max_size: int
    customer_radius: int
    queue_position_offset: int
    queue_color: tuple[int, int, int]
    server_color: tuple[int, int, int]
    customer_color: tuple[int, int, int]
    entry_color: tuple[int, int, int]
    exit_color: tuple[int, int, int]

    @classmethod
    def from_json(cls, json_file: str) -> "SimulationSettings":
        with open(json_file, "r") as file:
            settings_data = json.load(file)
        # Convert lists to tuples
        settings_data["queue_color"] = tuple(settings_data["queue_color"])
        settings_data["server_color"] = tuple(settings_data["server_color"])
        settings_data["customer_color"] = tuple(settings_data["customer_color"])
        settings_data["entry_color"] = tuple(settings_data["entry_color"])
        settings_data["exit_color"] = tuple(settings_data["exit_color"])
        return cls(**settings_data)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Step 2: Load settings from a JSON file
def load_settings_from_json(json_file: str) -> SimulationSettings:
    with open(json_file, "r") as file:
        settings_data = json.load(file)
    return SimulationSettings(**settings_data)


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
        color: tuple[int, int, int],
    ):
        self.position = spawn_position
        self.shape = shapes.Circle(
            spawn_position.x,
            spawn_position.y,
            radius,
            color=color,
            batch=batch,
        )
        self.target = queue_position  # Initially moving towards queue position

    def move_toward(self, target: Vector2D, dt: float, move_speed: float) -> bool:
        """Move the customer toward the target position."""
        direction = target - self.position  # Calculate direction vector
        distance = direction.magnitude()  # Calculate distance to target

        if distance > 0:
            # Normalize the direction and calculate the move vector
            move_vector = direction.normalize() * move_speed * dt

            # If the move vector would overshoot the target, limit the movement to exactly reach the target
            if move_vector.magnitude() > distance:
                move_vector = direction  # Move the remaining distance to the target

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
        window_width: float,
        window_height: float,
        settings: SimulationSettings,
    ):
        self.settings = settings
        self.start_position = start_position  # Queue start position (Vector2D)
        self.end_position = end_position  # Queue end position (Vector2D)
        self.spawn_position = Vector2D(50, window_height - 50)
        self.exit_position = Vector2D(window_width - 50, 50)
        self.queue: queue.Queue[Customer] = queue.Queue()  # FIFO queue for customers
        self.server = None  # The customer currently being served
        self.exiting_customers: list[Customer] = []  # List to hold customers moving to the exit
        self.batch = pyglet.graphics.Batch()  # Batch for efficient drawing
        self.next_arrival_time = random.expovariate(self.settings.arrival_rate)
        self.next_service_time = None
        self.waiting_time = 0.0  # Initialize the waiting time to 0

        # Shapes for the start and end points (visualized)
        self.queue_entry = shapes.Rectangle(
            self.start_position.x - 5,
            self.start_position.y - 25,
            10,
            50,
            color=self.settings.queue_color,
            batch=self.batch,
        )
        self.server_box = shapes.Rectangle(
            self.end_position.x - 25,
            self.end_position.y - 25,
            50,
            50,
            color=self.settings.server_color,
            batch=self.batch,
        )
        self.entry_box = shapes.Rectangle(
            self.spawn_position.x - 25,
            self.spawn_position.y - 25,
            50,
            50,
            color=self.settings.entry_color,
            batch=self.batch,
        )
        self.exit_box = shapes.Rectangle(
            self.exit_position.x - 25,
            self.exit_position.y - 25,
            50,
            50,
            color=self.settings.exit_color,
            batch=self.batch,
        )

        # Timer label above the server box
        self.server_timer_label = pyglet.text.Label(
            "",
            font_name="Arial",
            font_size=14,
            x=self.end_position.x,
            y=self.end_position.y + 40,  # Position the label above the server box
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
        )

        # Timer label above the queue to show waiting time
        self.queue_waiting_time_label = pyglet.text.Label(
            "",
            font_name="Arial",
            font_size=14,
            x=self.start_position.x,
            y=self.start_position.y + 40,  # Position the label above the queue
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
        )

        # Timer label above the entry to show next arrival time
        self.next_arrival_time_label = pyglet.text.Label(
            "",
            font_name="Arial",
            font_size=14,
            x=self.spawn_position.x,
            y=self.spawn_position.y + 40,  # Position the label above the entry
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
        )

    def add_customer(self):
        """Add a new customer to the queue."""
        if self.queue.qsize() < self.settings.queue_max_size:  # Limit queue size
            position_in_queue = Vector2D(
                self.start_position.x
                - self.queue.qsize() * self.settings.queue_position_offset,
                self.start_position.y,
            )
            customer = Customer(
                self.spawn_position,
                position_in_queue,
                self.settings.customer_radius,
                self.batch,
                self.settings.customer_color,
            )
            self.queue.put(customer)
            # Reset the waiting time when a customer is added
            self.waiting_time = 0.0

    def update(self, dt: float) -> None:
        """Update the queue system and move customers."""
        # Update the next arrival timer
        self.next_arrival_time -= dt
        self.next_arrival_time_label.text = (
            f"next: {self.next_arrival_time:.2f}s"
        )

        if self.next_arrival_time <= 0:
            self.add_customer()
            self.next_arrival_time: float = random.expovariate(
                self.settings.arrival_rate
            )

        # Handle serving customers
        if self.server is None and not self.queue.empty():
            self.server = self.queue.get()
            self.server.target = self.end_position  # Move customer to server
            self.next_service_time = random.expovariate(self.settings.service_rate)

        if self.server:
            # Move the customer to the server smoothly
            if self.server.move_toward(
                self.server.target, dt, self.settings.move_speed
            ):
                self.next_service_time -= dt
                # Update the timer label with remaining service time
                self.server_timer_label.text = f"{self.next_service_time:.2f} s"

                if self.next_service_time <= 0:
                    # Customer has been served; now move to the exit
                    self.server.target = self.exit_position
                    self.exiting_customers.append(self.server)
                    self.server = None
                    # Clear the timer when done
                    self.server_timer_label.text = ""

        # Update exiting customers moving toward the exit
        for customer in self.exiting_customers[:]:  # Iterate over a copy of the list
            if customer.move_toward(self.exit_position, dt, self.settings.move_speed):
                # Remove customer once they reach the exit
                self.exiting_customers.remove(customer)

        # Update waiting time for customers in the queue
        if not self.queue.empty():
            self.waiting_time += dt
            self.queue_waiting_time_label.text = (
                f"waiting {self.waiting_time:.2f}s"
            )

        # Update customers in the queue to move forward if needed
        for i in range(self.queue.qsize()):
            customer = self.queue.queue[i]
            customer.target = Vector2D(
                self.start_position.x - i * self.settings.queue_position_offset,
                self.start_position.y,
            )
            customer.move_toward(customer.target, dt, self.settings.move_speed)

    def draw(self):
        """Draw all elements in the system."""
        self.batch.draw()


class QueueSimulation:
    """Simulation that has a Pyglet window to run the M/M/1 queue."""

    def __init__(self, settings: SimulationSettings):
        # Create the Pyglet window
        self.window = pyglet.window.Window(
            width=settings.window_width,
            height=settings.window_height,
            caption="M/M/1 Queue Simulation",
        )

        # Setup the queue system
        window_height = self.window.height
        window_width = self.window.width
        start_position = Vector2D(window_width // 3, window_height // 2)
        end_position = Vector2D(window_width // 3 * 2, window_height // 2)
        self.queue_system = MM1Queue(
            start_position,
            end_position,
            window_width,
            window_height,
            settings,
        )

        # Set up event handlers
        self.window.push_handlers(self)

    def on_draw(self):
        self.window.clear()
        self.queue_system.draw()

    def update(self, dt: float):
        self.queue_system.update(dt)

    def run(self):
        # Schedule the update function to run every 1/60 of a second
        pyglet.clock.schedule_interval(self.update, 1 / 60)

        # Start the Pyglet application
        pyglet.app.run()


# Step 4: Load settings and start the simulation
settings = load_settings_from_json("simulation_config.json")

# Create the simulation instance
simulation = QueueSimulation(settings)

# Run the simulation
simulation.run()
