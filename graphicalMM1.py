#!/usr/bin/env python3
"""
Library with some objects that make use of the python Turtle library to show graphics of a discrete event simulation of an MM1 queue (random arrivals and services, a single server).

There are various objects that allow for the simulation and demonstration of emergent behaviour:

- Player (I use the term player instead of customer as I also allow for the selfish and optimal behaviour: graphical representation: blue coloured dot);
- SelfishPlayer (inherited from Player: when passed a value of service, a SelfishPlayer will join the queue if and only if it is in their selfish interest: graphical representation: red coloured dot.);
- OptimalPlayer (uses a result from Naor to ensure that the mean cost is reduced: graphical representation: gold coloured dot.)

- Queue
- Server

- Sim (this is the main object that generates all other objects as required).
"""
# try:
#     import tkinter
#     tkinter._test()
# except Exception:
#     raise Exception("tkinter not installed, or if you use WSL, install VcXsrc ")

import argparse
from collections.abc import Sequence
from turtle import Turtle, setworldcoordinates
from random import expovariate as randexp, random  # Pseudo random number generation
import sys  # Use to write to stdout
from typing import Any, Iterator, Literal
from pathlib import Path


def clamp(smallest: int, n: int, largest: int) -> int:
    """clamp n to the range [smallest, largest]."""
    return max(smallest, min(n, largest))


def mean(lst: Sequence[float]) -> float | Literal[False]:
    """
    Function to return the mean of a list.

    Argument: lst - a list of numeric variables

    Output: the mean of lst
    """
    if len(lst) > 0:
        return sum(lst) / len(lst)
    return False


def movingaverage(lst: Sequence[float]) -> list[float | bool]:
    """
    Custom built function to obtain moving average

    Argument: lst - a list of numeric variables

    Output: a list of moving averages
    """
    return [mean(lst[:k]) for k in range(1, len(lst) + 1)]


def plotwithnobalkers(
    queue_lengths: list[float],
    system_states: list[float],
    time_points: list[float],
    save_fig: bool,
    file_name: Path,
) -> None:
    """
    A function to plot histograms and timeseries.

    Arguments:
        - queue_lengths
        - system_states
        - time_points
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        sys.stdout.write(
            "matplotlib does not seem to be installed: no plots can be produced."
        )
        return

    plt.figure(1, figsize=(8, 6))
    plt.subplot(221)
    plt.hist(queue_lengths, density=True, bins=min(20, max(queue_lengths)))
    plt.xlabel("Queue length")
    plt.ylabel("Frequency")
    plt.subplot(222)
    plt.hist(system_states, density=True, bins=min(20, max(system_states)))
    plt.xlabel("System state")
    plt.ylabel("Frequency")
    plt.subplot(223)
    plt.plot(time_points, movingaverage(queue_lengths))
    plt.xlabel("Time")
    plt.ylabel("Mean queue length")
    plt.subplot(224)
    plt.plot(time_points, movingaverage(system_states))
    plt.xlabel("Time")
    plt.ylabel("Mean system state")
    if save_fig:
        plt.savefig(file_name)
    else:
        plt.show()


def plotwithbalkers(
    selfish_queue_lengths: Sequence[int],
    optimal_queue_lengths: Sequence[int],
    selfish_system_states: Sequence[float],
    optimal_system_states: Sequence[float],
    time_points: Sequence[float],
    save_fig: bool,
    file_name: Path,
):
    """
    A function to plot histograms and timeseries when you have two types of players

    Arguments:
        - selfish_queue_lengths
        - optimal_queue_lengths
        - selfish_system_states
        - optimal_system_states
        - time_points
        - save_fig
        - file_name
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        sys.stdout.write(
            "matplotlib does not seem to be installed: no plots can be produced."
        )
        return
    queue_lengths: Sequence[int] = [
        sum(k) for k in zip(selfish_queue_lengths, optimal_queue_lengths)
    ]
    system_states: Sequence[int] = [
        sum(k) for k in zip(selfish_system_states, optimal_system_states)
    ]
    fig = plt.figure(1)
    plt.subplot(221)
    plt.hist(
        [selfish_queue_lengths, optimal_queue_lengths, queue_lengths],
        density=True,
        bins=min(20, max(queue_lengths)),
        label=["Selfish players", "Optimal players", "Total players"],
        color=["red", "green", "blue"],
    )
    # plt.legend()
    plt.title("Number in queue")
    plt.subplot(222)
    plt.hist(
        [selfish_system_states, optimal_system_states, system_states],
        density=True,
        bins=min(20, max(system_states)),
        label=["Selfish players", "Optimal players", "Total players"],
        color=["red", "green", "blue"],
    )
    # plt.legend()
    plt.title("Number in system")
    plt.subplot(223)
    plt.plot(
        time_points,
        movingaverage(selfish_queue_lengths),
        label="Selfish players",
        color="red",
    )
    plt.plot(
        time_points,
        movingaverage(optimal_queue_lengths),
        label="Optimal players",
        color="green",
    )
    plt.plot(time_points, movingaverage(queue_lengths), label="Total", color="blue")
    # plt.legend()
    plt.title("Mean number in queue")
    plt.subplot(224)
    (line1,) = plt.plot(
        time_points,
        movingaverage(selfish_system_states),
        label="Selfish players",
        color="red",
    )
    (line2,) = plt.plot(
        time_points,
        movingaverage(optimal_system_states),
        label="Optimal players",
        color="green",
    )
    (line3,) = plt.plot(
        time_points, movingaverage(system_states), label="Total", color="blue"
    )
    # plt.legend()
    plt.title("Mean number in system")
    fig.legend(
        [line1, line2, line3],
        ["Selfish players", "Optimal players", "Total"],
        loc="lower center",
        fancybox=True,
        ncol=3,
        bbox_to_anchor=(0.5, 0),
    )
    plt.subplots_adjust(bottom=0.15)
    if save_fig:
        plt.savefig(file_name)
    else:
        plt.show()


def naor_threshold(
    arrival_rate: float, service_rate: float, cost_of_balking: float
) -> int:
    """
    Function to return Naor's threshold for optimal behaviour in an M/M/1 queue. This is taken from Naor's 1969 paper: 'The regulation of queue size by Levying Tolls'

    Arguments:
        arrival_rate: arrival rate
        service_rate: service rate
        cost_of_balking: the value of service, converted to time units.

    Output: A threshold at which optimal customers must no longer join the queue (integer)
    """
    n = 0  # Initialise n
    center = (
        service_rate * cost_of_balking
    )  # Center mid point of inequality from Naor's aper
    rho = arrival_rate / service_rate
    while True:
        LHS = (n * (1 - rho) - rho * (1 - rho**n)) / ((1 - rho) ** 2)
        RHS = ((n + 1) * (1 - rho) - rho * (1 - rho ** (n + 1))) / ((1 - rho) ** 2)
        if LHS <= center and center < RHS:
            return n
        n += 1  # Continually increase n until LHS and RHS are either side of center


class Queue:
    """
    A class for a queue.

    Attributes:
        players - a list of players in the queue
        position - graphical position of queue

    Methods:
        pop - returns first in player from queue and updates queue graphics
        join - makes a player join the queue

    """

    def __init__(self, qposition: list[float]) -> None:
        self.players: list[Player] = []
        self.position: list[float] = qposition

    def __iter__(self) -> Iterator["Player"]:
        return iter(self.players)

    def __len__(self) -> int:
        return len(self.players)

    def pop(self, index: int) -> "Player":
        """
        A function to return a player from the queue and update graphics.

        Arguments: index - the location of the player in the queue

        Outputs: returns the relevant player
        """
        for p in (
            self.players[:index] + self.players[index + 1 :]
        ):  # Shift everyone up one queue spot
            x = p.position()[0]
            y = p.position()[1]
            p.move(x + 10, y)
        self.position[0] += 10  # Reset queue position for next arrivals
        return self.players.pop(index)

    def join(self, player: "Player") -> None:
        """
        A method to make a player join the queue.

        Arguments: player object

        Outputs: NA
        """
        self.players.append(player)
        self.position[0] -= 10


class Server:
    """
    A class for the server (this could theoretically be modified to allow for more complex queues than M/M/1)

    Attributes:
        - players: list of players in service (at present will be just the one player)
        - position: graphical position of queue

    Methods:
        - start: starts the service of a given player
        - free: a method that returns free if the server is free
    """

    def __init__(self, svrposition: list[float]):
        self.players: list[Player] = []
        self.position: list[float] = svrposition

    def __iter__(self) -> Iterator["Player"]:
        return iter(self.players)

    def __len__(self) -> int:
        return len(self.players)

    def start(self, player: "Player") -> None:
        """
        A function that starts the service of a player (there is some functionality already in place in case multi server queue ever gets programmed). Moves all graphical stuff.

        Arguments: A player object

        Outputs: NA
        """
        self.players.append(player)
        self.players = sorted(self.players, key=lambda x: x.servicedate)
        self.nextservicedate = self.players[0].servicedate

    def free(self) -> bool:
        """
        Returns True if server is empty.
        """
        return len(self.players) == 0


class Player(Turtle):
    """
    A generic class for our 'customers'. I refer to them as players as I like to consider queues in a game theoretical framework. This class is inherited from the Turtle class so as to have the graphical interface.

    Attributes:
        arrival_rate: arrival rate
        service_rate: service rate
        queue: a queue object
        server: a server object


    Methods:
        move - move player to a given location
        arrive - a method to make our player arrive at the queue
        startservice - a method to move our player from the queue to the server
        endservice - a method to complete service
    """

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        queue: Queue,
        server: Server,
        speed: int,
    ):
        """
        Arguments:
            arrival_rate: arrival rate (float)
            interarrivaltime: a randomly sampled interarrival time (negative exponential for now)
            service_rate: service rate (float)
            service: a randomly sampled service time (negative exponential for now)
            queue: a queue object
            shape: the shape of our turtle in the graphics (a circle)
            server: a server object
            served: a boolean that indicates whether or not this player has been served.
            speed: a speed (integer from 0 to 10) to modify the speed of the graphics
            balked: a boolean indicating whether or not this player has balked (not actually needed for the base Player class... maybe remove... but might be nice to keep here...)
        """
        Turtle.__init__(self)  # Initialise all base Turtle attributes
        self.interarrivaltime = randexp(arrival_rate)
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.queue: Queue = queue
        self.served = False
        self.server = server
        self.service_time = randexp(service_rate)
        self.shape("circle")
        self.speed(speed)
        self.balked = False

    def move(self, x: float, y: float) -> None:
        """
        A method that moves our player to a given point

        Arguments:
            x: the x position on the canvas to move the player to
            y: the y position on the canvas to move the player to.

        Output: NA
        """
        self.setx(x)
        self.sety(y)

    def arrive(self, t: float) -> None:
        """
        A method that make our player arrive (the player is first created to generate an interarrival time, service time etc...).

        Arguments: t the time of arrival (a float)

        Output: NA
        """
        self.penup()
        self.arrival_date = t
        self.move(self.queue.position[0] + 5, self.queue.position[1])
        self.color("blue")
        self.queue.join(self)

    def startservice(self, t: float) -> None:
        """
        A method that makes our player start service (This moves the graphical representation of the player and also make the queue update it's graphics).

        Arguments: t the time of service start (a float)

        Output: NA
        """
        if not self.served and not self.balked:
            self.move(self.server.position[0], self.server.position[1])
            self.servicedate = t + self.service_time
            self.server.start(self)
            self.color("gold")
            self.endqueuedate = t

    def endservice(self) -> None:
        """
        A method that makes our player end service (This moves the graphical representation of the player and updates the server to be free).

        Arguments: NA

        Output: NA
        """
        self.color("grey")
        self.move(
            self.server.position[0] + 50 + random(),
            self.server.position[1] - 50 + random(),
        )
        self.server.players = self.server.players[1:]
        self.endservicedate = self.endqueuedate + self.service_time
        self.waiting_time = self.endqueuedate - self.arrival_date
        self.served = True


class SelfishPlayer(Player):
    """
    A class for a player who acts selfishly (estimating the amount of time that they will wait and comparing to a value of service). The only modification is the arrive method that now allows players to balk.
    """

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        queue: Queue,
        server: Server,
        speed: int,
        cost_of_balking: bool | float | list[float],
    ):
        Player.__init__(self, arrival_rate, service_rate, queue, server, speed)
        self.cost_of_balking = cost_of_balking

    def arrive(self, t: float) -> None:
        """
        As described above, this method allows players to balk if the expected time through service is larger than some alternative.

        Arguments: t - time of arrival (a float)

        Output: NA
        """
        self.penup()
        self.arrivaldate = t
        self.color("red")
        system_state = len(self.queue) + len(self.server)
        if (system_state + 1) / (self.service_rate) < self.cost_of_balking:
            self.queue.join(self)
            self.move(self.queue.position[0] + 5, self.queue.position[1])
        else:
            self.balk()
            self.balked = True

    def balk(self):
        """
        Method to make player balk.

        Arguments: NA

        Outputs: NA
        """
        self.move(random(), self.queue.position[1] - 25 + random())


class OptimalPlayer(Player):
    """
    A class for a player who acts within a socially optimal framework (using the threshold from Naor's paper). The only modification is the arrive method that now allows players to balk and a new attribute for the Naor threshold.
    """

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        queue: Queue,
        server: Server,
        speed: int,
        naor_threshold: bool | int,
    ):
        Player.__init__(self, arrival_rate, service_rate, queue, server, speed)
        self.naor_threshold = naor_threshold

    def arrive(self, t: float) -> None:
        """
        A method to make player arrive. If more than Naor threshold are present in queue then the player will balk.

        Arguments: t - time of arrival (float)

        Outputs: NA
        """
        self.penup()
        self.arrivaldate = t
        self.color("green")
        system_state = len(self.queue) + len(self.server)
        if system_state < self.naor_threshold:
            self.queue.join(self)
            self.move(self.queue.position[0] + 5, self.queue.position[1])
        else:
            self.balk()
            self.balked = True

    def balk(self):
        """
        A method to make player balk.
        """
        self.move(10 + random(), self.queue.position[1] - 25 + random())


class Sim:
    """
    The main class for a simulation.

    Attributes:
        - cost_of_balking (by default set to False for a basic simulation). Can be a float (indicating the cost of balking) in which case all players act selfishly. Can also be a list: l. In which case l[0] represents proportion of selfish players (other players being social players). l[1] then indicates cost of balking.
        - naor_threshold (by default set to False for a basic simulation). Can be an integer (not to be input but calculated using cost_of_balking).
        - simulation_time total run time (float)
        - arrival_rate: arrival rate (float)
        - service_rate: service rate (float)
        - players: list of players (list)
        - queue: a queue object
        - queue_length_dict: a dictionary that keeps track of queue length at given times (for data handling)
        - system_state_dict: a dictionary that keeps track of system state at given times (for data handling)
        - server: a server object
        - speed: the speed of the graphical animation

    Methods:
        - run: runs the simulation model
        - newplayer: generates a new player (that does not arrive until the clock advances past their arrivaldate)
        - printprogress: print the progress of the simulation to stdout
        - collectdata: collects data at time t
        - plot: plots summary graphs
    """

    def __init__(
        self,
        simulation_time: float,
        arrival_rate: float,
        service_rate: float,
        speed: int,
        cost_of_balking: Literal[False] | list[float] = False,
    ) -> None:
        ##################
        bLx = -10  # This sets the size of the canvas (I think that messing with this could increase speed of turtles)
        bLy = -110
        tRx = 230
        tRy = 5
        setworldcoordinates(bLx, bLy, tRx, tRy)
        qposition: list[float] = [
            (tRx + bLx) / 2,
            (tRy + bLy) / 2,
        ]  # The position of the queue
        ##################
        self.cost_of_balking: Literal[False] | list[float] = cost_of_balking
        self.simulation_time = simulation_time
        self.completed: list[Player] = []
        self.balked: list[Player] = []
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.players: list[Player] = []
        self.queue = Queue(qposition)
        self.queue_length_dict: dict[float, int | list[int]] = {}
        self.server = Server([qposition[0] + 50, qposition[1]])
        self.speed: int = clamp(0, speed, 10)
        self.naor_threshold: bool | int = False
        if type(cost_of_balking) is list:
            self.naor_threshold = naor_threshold(
                arrival_rate, service_rate, cost_of_balking[1]
            )
        else:
            self.naor_threshold = naor_threshold(
                arrival_rate, service_rate, cost_of_balking
            )
        self.system_state_dict: dict[float, float | list[float]] = {}

    def newplayer(self) -> None:
        """
        A method to generate a new player (takes in to account cost of balking). So if no cost of balking is passed: only generates a basic player. If a float is passed as cost of balking: generates selfish players with that float as worth of service. If a list is passed then it creates a player (either selfish or optimal) according to a random selection.

        Arguments: NA

        Outputs: NA
        """
        if len(self.players) == 0:
            if not self.cost_of_balking:
                self.players.append(
                    Player(
                        self.arrival_rate,
                        self.service_rate,
                        self.queue,
                        self.server,
                        self.speed,
                    )
                )
            elif type(self.cost_of_balking) is list:
                if random() < self.cost_of_balking[0]:
                    self.players.append(
                        SelfishPlayer(
                            self.arrival_rate,
                            self.service_rate,
                            self.queue,
                            self.server,
                            self.speed,
                            self.cost_of_balking[1],
                        )
                    )
                else:
                    self.players.append(
                        OptimalPlayer(
                            self.arrival_rate,
                            self.service_rate,
                            self.queue,
                            self.server,
                            self.speed,
                            self.naor_threshold,
                        )
                    )
            else:
                self.players.append(
                    SelfishPlayer(
                        self.arrival_rate,
                        self.service_rate,
                        self.queue,
                        self.server,
                        self.speed,
                        self.cost_of_balking,
                    )
                )

    def printprogress(self, t: float) -> None:
        """
        A method to print to screen the progress of the simulation.

        Arguments: t (float)

        Outputs: NA
        """
        sys.stdout.write(
            f"\r{100*t/self.simulation_time:.2f}% of simulation completed (t={t} of {self.simulation_time})"
        )
        sys.stdout.flush()

    def run(self) -> None:
        """
        The main method which runs the simulation. This will collect relevant data throughout the simulation so that if matplotlib is installed plots of results can be accessed. Furthermore all completed players can be accessed in self.completed.

        Arguments: NA

        Outputs: NA
        """
        tick: int = 0
        self.newplayer()  # Create a new player
        nextplayer = self.players.pop()  # Set this player to be the next player
        # Make the next player arrive for service (potentially at the queue)
        nextplayer.arrive(tick)
        nextplayer.startservice(tick)  # This player starts service immediately
        self.newplayer()  # Create a new player that is now waiting to arrive
        while tick < self.simulation_time:
            tick += 1
            self.printprogress(tick)  # Output progress to screen
            # Check if service finishes
            if not self.server.free() and tick > self.server.nextservicedate:
                # Add completed player to completed list
                self.completed.append(self.server.players[0])
                # End service of a player in service
                self.server.players[0].endservice()
                if len(self.queue) > 0:  # Check if there is a queue
                    # This returns player to go to service and updates queue.
                    nextservice = self.queue.pop(0)
                    nextservice.startservice(tick)
                    self.newplayer()
            # Check if player that is waiting arrives
            if tick > self.players[-1].interarrivaltime + nextplayer.arrival_date:
                nextplayer = self.players.pop()
                nextplayer.arrive(tick)
                if nextplayer.balked:
                    self.balked.append(nextplayer)
                if self.server.free():
                    if len(self.queue) == 0:
                        nextplayer.startservice(tick)
                    else:  # Check if there is a queue
                        # This returns player to go to service and updates queue.
                        nextservice = self.queue.pop(0)
                        nextservice.startservice(tick)
            self.newplayer()
            self.collectdata(tick)

    def collectdata(self, t: float) -> None:
        """
        Collect data at each time step: updates data dictionaries.

        Arguments: t (float)

        Outputs: NA
        """
        if self.cost_of_balking:
            selfish_queue_length = len(
                [sp for sp in self.queue if type(sp) is SelfishPlayer]
            )
            self.queue_length_dict[t] = [
                selfish_queue_length,
                len(self.queue) - selfish_queue_length,
            ]
            if self.server.free():
                self.system_state_dict[t] = [0, 0]
            else:
                self.system_state_dict[t] = [
                    self.queue_length_dict[t][0]
                    + len([p for p in self.server.players if type(p) is SelfishPlayer]),
                    self.queue_length_dict[t][1]
                    + len([p for p in self.server.players if type(p) is OptimalPlayer]),
                ]
        else:
            self.queue_length_dict[t] = len(self.queue)
            if self.server.free():
                self.system_state_dict[t] = 0
            else:
                self.system_state_dict[t] = self.queue_length_dict[t] + 1

    def plot(self, save_fig: bool, warmup: float = 0) -> None:
        """
        Plot the data
        """
        file_name = Path(
            f"arrival_rate={self.arrival_rate}-mu={self.service_rate}-T={self.simulation_time}-cost={self.cost_of_balking}.pdf"
        )
        if self.cost_of_balking:
            selfish_queue_lengths: Sequence[int] = []
            optimal_queue_lengths: Sequence[int] = []
            selfish_system_states: Sequence[float] = []
            optimal_system_states: Sequence[float] = []
            time_points: Sequence[float] = []
            assert isinstance(
                self.system_state_dict, dict
            ), "self.system_state_dict is not a dict"
            for t in self.queue_length_dict:
                assert isinstance(
                    self.system_state_dict[t], list
                ), "self.system_state_dict[t] is not a list"
                if t >= warmup:
                    selfish_queue_lengths.append(self.queue_length_dict[t][0])
                    optimal_queue_lengths.append(self.queue_length_dict[t][1])
                    selfish_system_states.append(self.system_state_dict[t][0])
                    optimal_system_states.append(self.system_state_dict[t][1])
                    time_points.append(t)
            plotwithbalkers(
                selfish_queue_lengths,
                optimal_queue_lengths,
                selfish_system_states,
                optimal_system_states,
                time_points,
                save_fig,
                file_name,
            )
        else:
            queue_lengths: list[float] = []
            system_states: list[float] = []
            time_points: Sequence[float] = []
            for t in self.queue_length_dict:
                if t >= warmup:
                    queue_lengths.append(self.queue_length_dict[t])
                    system_states.append(self.system_state_dict[t])
                    time_points.append(t)
            plotwithnobalkers(
                queue_lengths,
                system_states,
                time_points,
                save_fig,
                file_name,
            )

    def printsummary(self, warmup: float = 0):
        """
        A method to print summary statistics.
        """
        if not self.cost_of_balking:
            self.queue_lengths: list[float] = []
            self.system_states: list[float] = []
            for t in self.queue_length_dict:
                if t >= warmup:
                    self.queue_lengths.append(self.queue_length_dict[t])
                    self.system_states.append(self.system_state_dict[t])
            self.mean_queue_length = mean(self.queue_lengths)
            self.mean_system_state = mean(self.system_states)
            self.waiting_times: list[float] = []
            self.service_times: list[float] = []
            for p in self.completed:
                if p.arrival_date >= warmup:
                    self.waiting_times.append(p.waiting_time)
                    self.service_times.append(p.service_time)
            self.mean_waiting_time = mean(self.waiting_times)
            self.mean_system_time = mean(self.service_times) + self.mean_waiting_time
            sys.stdout.write("\n%sSummary statistics%s\n" % (10 * "-", 10 * "-"))
            sys.stdout.write("Mean queue length: %.02f\n" % self.mean_queue_length)
            sys.stdout.write("Mean system state: %.02f\n" % self.mean_system_state)
            sys.stdout.write("Mean waiting time: %.02f\n" % self.mean_waiting_time)
            sys.stdout.write("Mean system time: %.02f\n" % self.mean_system_time)
            sys.stdout.write(39 * "-" + "\n")
        else:
            self.selfish_queue_lengths: list[float] = []
            self.optimal_queue_lengths: list[float] = []
            self.selfish_system_states: list[float] = []
            self.optimal_system_states: list[float] = []
            for t in self.queue_length_dict:
                if t >= warmup:
                    self.selfish_queue_lengths.append(self.queue_length_dict[t][0])
                    self.optimal_queue_lengths.append(self.queue_length_dict[t][1])
                    self.selfish_system_states.append(self.system_state_dict[t][0])
                    self.optimal_system_states.append(self.system_state_dict[t][1])
            self.mean_selfish_queue_length = mean(self.selfish_queue_lengths)
            self.mean_optimal_queue_length = mean(self.optimal_queue_lengths)
            self.mean_queue_length = mean(
                [
                    sum(k)
                    for k in zip(self.selfish_queue_lengths, self.optimal_queue_lengths)
                ]
            )
            self.mean_selfish_system_state = mean(self.selfish_system_states)
            self.mean_optimal_system_state = mean(self.optimal_system_states)
            self.mean_system_state = mean(
                [
                    sum(k)
                    for k in zip(self.selfish_system_states, self.optimal_system_states)
                ]
            )

            self.selfish_waiting_times: list[float] = []
            self.optimal_waiting_times: list[float] = []
            self.selfish_service_times: list[float] = []
            self.optimal_service_times: list[float] = []
            for p in self.completed:
                if p.arrival_date >= warmup:
                    if type(p) is SelfishPlayer:
                        self.selfish_waiting_times.append(p.waiting_time)
                        self.selfish_service_times.append(p.service_time)
                    else:
                        self.optimal_waiting_times.append(p.waiting_time)
                        self.optimal_service_times.append(p.service_time)
            self.mean_selfish_waiting_time = mean(self.selfish_waiting_times)
            self.mean_selfish_system_time = (
                mean(self.selfish_service_times) + self.mean_selfish_waiting_time
            )
            self.mean_optimal_waiting_time = mean(self.optimal_waiting_times)
            self.mean_optimal_system_time = (
                mean(self.optimal_service_times) + self.mean_optimal_waiting_time
            )

            self.selfish_prob_balk: float = 0
            self.optimal_prob_balk: float = 0
            for p in self.balked:
                if p.arrival_date >= warmup:
                    if type(p) is SelfishPlayer:
                        self.selfish_prob_balk += 1
                    else:
                        self.optimal_prob_balk += 1

            assert isinstance(
                self.cost_of_balking, list
            ), "self.cost_of_balking is not a list"
            self.mean_selfish_cost: float | bool = (
                self.selfish_prob_balk * self.cost_of_balking[1]
                + sum(self.selfish_service_times)
                + sum(self.selfish_waiting_times)
            )
            self.mean_optimal_cost: float = (
                self.optimal_prob_balk * self.cost_of_balking[1]
                + sum(self.optimal_service_times)
                + sum(self.optimal_waiting_times)
            )
            self.mean_cost: float = self.mean_selfish_cost + self.mean_optimal_cost
            if len(self.selfish_waiting_times) + self.selfish_prob_balk != 0:
                self.mean_selfish_cost /= self.selfish_prob_balk + len(
                    self.selfish_waiting_times
                )
            else:
                self.mean_selfish_cost = False
            if len(self.optimal_waiting_times) + self.optimal_prob_balk != 0:
                self.mean_optimal_cost /= self.optimal_prob_balk + len(
                    self.optimal_waiting_times
                )
            else:
                self.mean_selfish_cost = False

            if (
                self.selfish_prob_balk
                + self.optimal_prob_balk
                + len(self.selfish_waiting_times)
                + len(self.optimal_waiting_times)
                != 0
            ):
                self.mean_cost /= (
                    self.selfish_prob_balk
                    + self.optimal_prob_balk
                    + len(self.selfish_waiting_times)
                    + len(self.optimal_waiting_times)
                )
            else:
                self.mean_cost = False

            if self.selfish_prob_balk + len(self.selfish_waiting_times) != 0:
                self.selfish_prob_balk /= self.selfish_prob_balk + len(
                    self.selfish_waiting_times
                )
            else:
                self.selfish_prob_balk = False
            if self.optimal_prob_balk + len(self.optimal_waiting_times) != 0:
                self.optimal_prob_balk /= self.optimal_prob_balk + len(
                    self.optimal_waiting_times
                )
            else:
                self.optimal_prob_balk = False

            sys.stdout.write("\n%sSummary statistics%s\n" % (10 * "=", 10 * "="))

            sys.stdout.write("\n%sSelfish players%s\n" % (13 * "-", 10 * "-"))
            sys.stdout.write(
                "Mean number in queue: %.02f\n" % self.mean_selfish_queue_length
            )
            sys.stdout.write(
                "Mean number in system: %.02f\n" % self.mean_selfish_system_state
            )
            sys.stdout.write(
                "Mean waiting time: %.02f\n" % self.mean_selfish_waiting_time
            )
            sys.stdout.write(
                "Mean system time: %.02f\n" % self.mean_selfish_system_time
            )
            sys.stdout.write("Probability of balking: %.02f\n" % self.selfish_prob_balk)

            sys.stdout.write("\n%sOptimal players%s\n" % (13 * "-", 10 * "-"))
            sys.stdout.write(
                "Mean number in queue: %.02f\n" % self.mean_optimal_queue_length
            )
            sys.stdout.write(
                "Mean number in system: %.02f\n" % self.mean_optimal_system_state
            )
            sys.stdout.write(
                "Mean waiting time: %.02f\n" % self.mean_optimal_waiting_time
            )
            sys.stdout.write(
                "Mean system time: %.02f\n" % self.mean_optimal_system_time
            )
            sys.stdout.write("Probability of balking: %.02f\n" % self.optimal_prob_balk)

            sys.stdout.write("\n%sOverall mean cost (in time)%s\n" % (9 * "-", "-"))
            sys.stdout.write("All players: %.02f\n" % self.mean_cost)
            sys.stdout.write("Selfish players: %.02f\n" % self.mean_selfish_cost)
            sys.stdout.write("Optimal players: %.02f\n" % self.mean_optimal_cost)
            sys.stdout.write(39 * "=" + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "A simulation of an MM1 queue with a graphical representation made "
            "using the python Turtle module. Also, allows for some agent based "
            "aspects which at present illustrate results from Naor's paper: "
            "'The Regulation of Queue Size by Levying Tolls'"
        )
    )
    parser.add_argument(
        "-l",
        action="store",
        dest="arrival_rate",
        type=float,
        help="The arrival rate",
        default=2,
    )
    parser.add_argument(
        "-m",
        action="store",
        dest="service_rate",
        type=float,
        help="The service rate",
        default=1,
    )
    parser.add_argument(
        "-T",
        action="store",
        dest="simulation_time",
        type=float,
        help="The overall simulation time",
        default=100,
    )
    parser.add_argument(
        "-p",
        action="store",
        dest="prob_of_selfish",
        help="Proportion of selfish players (default: 0)",
        default=0,
        type=float,
    )
    parser.add_argument(
        "-c",
        action="store",
        dest="cost_of_balking",
        help="Cost of balking (default: False)",
        default=False,
        type=float,
    )
    parser.add_argument(
        "-w",
        action="store",
        dest="warmup",
        help="Warm up time",
        default=0,
        type=float,
    )
    parser.add_argument(
        "-s",
        action="store",
        dest="save_fig",
        help="Boolean to save the figure or not",
        default=False,
        type=bool,
    )
    parser.add_argument(
        "-S",
        action="store",
        dest="speed",
        help="int between 1 and 10 for the speed of the simulation; 0 for no animation",
        default=10,
        type=int,
    )
    inputs: argparse.Namespace = parser.parse_args()
    arrival_rate: float = inputs.arrival_rate
    service_rate: float = inputs.service_rate
    simulation_time: float = inputs.simulation_time
    warmup: float = inputs.warmup
    save_fig: bool = inputs.save_fig
    speed: int = inputs.speed
    cost_of_balking: bool | list[float] = inputs.cost_of_balking
    if cost_of_balking:
        cost_of_balking = [inputs.prob_of_selfish, inputs.cost_of_balking]
    q = Sim(simulation_time, arrival_rate, service_rate, speed, cost_of_balking)
    q.run()
    q.printsummary(warmup=warmup)
    q.plot(save_fig)
