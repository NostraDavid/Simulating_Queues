"""
λ is arrival_rate
μ is service_rate

https://en.wikipedia.org/wiki/M/M/1_queue
"""

# %%
import random
import csv
from dataclasses import dataclass
from statistics import mean
from pathlib import Path


@dataclass
class Customer:
    """define a class called 'Customer'"""

    arrival_date: float
    service_start_date: float
    service_time: float

    @property
    def service_end_date(self) -> float:
        return self.service_start_date + self.service_time

    @property
    def wait(self) -> float:
        return self.service_start_date - self.arrival_date


def neg_exp(arrival_rate: int) -> float:
    """a simple function to sample from negative exponential."""
    return random.expovariate(arrival_rate)


def simulation(
    simulation_time: int,
    arrival_rate: int,
    service_rate: int,
) -> tuple[list[Customer], float]:
    """
    Run the simulation and return the generated customers and the end time of
    the simulation.
    """
    # Initialise clock
    tick = 0

    # Initialise empty list to hold all data
    customers: list[Customer] = []

    # ----------------------------------
    # The actual simulation happens here:
    while tick < simulation_time:
        # calculate arrival date and service time for new customer
        arrival_date = 0
        if len(customers) == 0:
            arrival_date = neg_exp(arrival_rate)
            service_start_date = arrival_date
        else:
            arrival_date += neg_exp(arrival_rate)
            service_start_date = max(arrival_date, customers[-1].service_end_date)
        service_time = neg_exp(service_rate)

        # create new customer
        customers.append(Customer(arrival_date, service_start_date, service_time))

        # increment clock till next end of service
        tick += arrival_date
    # ----------------------------------
    return customers, tick


def print_stats(customers: list[Customer], tick: float) -> None:
    # calculate summary statistics
    waits: list[float] = []
    total_times: list[float] = []
    service_times: list[float] = []

    for c in customers:
        waits.append(c.wait)
        total_times.append(c.wait + c.service_time)
        service_times.append(c.service_time)

    # Compute means and utilization
    mean_wait = mean(waits)
    mean_time = mean(total_times)
    mean_service_time = mean(service_times)

    utilisation = sum(service_times) / tick

    # output summary statistics to screen
    max_var_len = max(
        len(f"{float(len(customers)):.2f}"),
        len(f"{mean_service_time:.2f}"),
        len(f"{mean_wait:.2f}"),
        len(f"{mean_time:.2f}"),
        len(f"{utilisation:.2f}"),
    )
    print("Summary results:")
    print(f"  Number of customers: {float(len(customers)):>{max_var_len}.2f}")
    print(f"  Mean Service Time:   {mean_service_time:>{max_var_len}.2f}")
    print(f"  Mean Wait:           {mean_wait:>{max_var_len}.2f}")
    print(f"  Mean Time in System: {mean_time:>{max_var_len}.2f}")
    print(f"  Utilisation:         {utilisation:>{max_var_len}.2f}")

    print("")


def save_to_csv(
    customers: list[Customer],
    arrival_rate: int,
    service_rate: int,
    simulation_time: int,
) -> None:
    file_name = Path(
        f"MM1Q-output-({arrival_rate},{service_rate},{simulation_time}).csv"
    )
    with file_name.open(mode="w") as outfile:
        output = csv.writer(outfile)
        # write the header
        output.writerow(
            [
                "Customer",
                "Arrival_Date",
                "Wait",
                "Service_Start_Date",
                "Service_Time",
                "Service_End_Date",
            ]
        )
        # write the data
        for i, c in enumerate(customers, start=0):
            output.writerow(
                [
                    i,
                    c.arrival_date,
                    c.wait,
                    c.service_start_date,
                    c.service_time,
                    c.service_end_date,
                ]
            )


def QSim(
    arrival_rate: int | None = None,
    service_rate: int | None = None,
    simulation_time: int | None = None,
    output_file: bool | None = None,
) -> None:
    """
    This is the main function to call to simulate an MM1 queue.

    arrival_rate = λ
    service_rate = μ

    https://en.wikipedia.org/wiki/M/M/1_queue
    """

    # If parameters are not input prompt
    if arrival_rate is None:
        arrival_rate = int(input("Inter arrival rate: ")) or 1
    if service_rate is None:
        service_rate = int(input("Service rate: ")) or 2
    if simulation_time is None:
        simulation_time = int(input("Total simulation time: ")) or 10
    if output_file is None:
        output_file = bool(input("Output data to csv (True/False)? ")) or False

    customers, tick = simulation(simulation_time, arrival_rate, service_rate)

    print_stats(customers, tick)

    if output_file:
        save_to_csv(customers, arrival_rate, service_rate, simulation_time)


# %%
# run the simulation with some sane defaults
QSim(arrival_rate=3, service_rate=2, simulation_time=1000, output_file=True)

# %%
# run the simulation and ask the user for parameters
QSim()

# %%
