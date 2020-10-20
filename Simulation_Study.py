# Simulation code in Python is written by William Hirschfeldt

""" This code was used in a simulation study article called
    "Simulation Study in Python with SimPy - Modelling a 
    simple M/M/1 Queue System". The simulation is a model of 
    an M/M/1 queueing system using SimPy. Packets are being 
    generated at random and form a queue before being processed 
    by the server. Each individuall packet and the queue will 
    be recorded. From different experimental data, different 
    outputs will be produced for evaluation.
"""

# The necessary libraries to perform the simulation study.
import simpy
import random
import matplotlib.pyplot as plt

# Experimental data for the simulation study.
SERVER_RATE = 1000          # The rate for handling packet sizes in bits (server processing).
TIME_ARRIVAL = 1.0          # Mean arrival time (incoming packets).
SIZE_PACKET = 100           # Mean packet size in bytes (affects processing time).
RANDOM_SEED = 42            # Seed for random number.
SIMULATION_TIME = 100000    # Simulation time.
NUMBER_PACKETS = 999999     # The number of packages to be sent.
QUEUE_LIMIT = 100000        # Limited amount of packages or bytes in buffer queue.
LIMIT_BYTES = True          # Should buffer queue size be limited in terms of bytes?
SAMPLING_INTERVALL = 1.0    # Sampling intervall (1/samp) used to monitor the buffer queue.

# To store data collected from simulation.
queue = None            # The buffer queue used.
byte_size = 0           # The current size of the buffer queue in bytes.
packets_sent = 0        # The number of packages generated.
packets_rec = 0         # The number of packages received.
packets_drop = 0        # The number of packages dropped.
packets_queue = 0       # The number of packages entered buffer.
queue_times = []        # Contains the time each packet spend in buffer queue.
queue_sizes = []        # Contains the number of packages in buffer queue.
byte_sizes = []         # Contains the size in bytes for each package in buffer queue.
packet_times = []       # Contains the time each packet was processed by server.
samp_time = []          # Contains the time after each sample intervall.
packets_recorded = 0    # The number of packages processed by server.
bytes_recorded = 0      # The number of bytes processed by server.
queue_avg_sizes = []    # Contains the average number of packages in buffer queue.
queue_avg_times = []    # Contains the average time packages spend in buffer queue.

# Class to represent a basic packet.
class Packet:
    def __init__(self, id, size, time):
        self.id = id
        self.time = time
        self.size = size

    def __repr__(self):
        return "id: {}, size: {}, time: {:3f}".format(self.id, self.size, self.time)

# Function for generating packets at random according to the Poisson process.
def generator(env):
    global packets_sent
    for i in range(NUMBER_PACKETS): # This could be changed to a While-loop for infinite packages.
        yield env.timeout(random.expovariate(1/TIME_ARRIVAL))
        packets_sent += 1
        packet = Packet(packets_sent, int(random.expovariate(1/SIZE_PACKET)), env.now)
        toQueue(packet)

# Function to represent a server that handles packages from FIFO buffer queue.
def server(env):
    global queue, byte_size
    while True:
        packet = (yield queue.get())
        byte_size -= packet.size
        yield env.timeout(packet.size*8.0/SERVER_RATE)
        recorder(env, packet)
        print("Processed packet:", packet)

# Function to put packets into a buffer queue.
def toQueue(packet):
    global packets_rec, packets_drop, packets_queue, byte_size, queue
    packets_rec += 1
    queue_byte_count = byte_size + packet.size
    if LIMIT_BYTES and (queue_byte_count >= QUEUE_LIMIT):
        packets_drop += 1
        return
    elif (not LIMIT_BYTES) and (len(queue.items) >= QUEUE_LIMIT):
        packets_drop += 1
        return
    else:
        byte_size = queue_byte_count
        packets_queue += 1
        return queue.put(packet)

# Function used to record information about individuall processed packets.
def recorder(env, packet):
    global queue_times, packets_recorded, bytes_recorded, packet_times
    arrive_time = env.now
    queue_times.append(arrive_time - packet.time)
    packet_times.append(arrive_time)
    queue_avg_times.append(sum(queue_times)/len(queue_times))
    packets_recorded += 1
    bytes_recorded += packet.size

# Monitor the buffer queue sizes at sampling intervall time.
def monitor(env):
    global byte_sizes, byte_size, queue_sizes, samp_time, queue, queue_avg_sizes
    while True:
        yield env.timeout(1/SAMPLING_INTERVALL)
        byte_sizes.append(byte_size)
        queue_sizes.append(len(queue.items))
        queue_avg_sizes.append(sum(queue_sizes)/len(queue_sizes))
        samp_time.append(env.now)

# For defining and running the simulation.
random.seed(RANDOM_SEED)        # Specified seed for random number.
env = simpy.Environment()       # Creating the SimPy environment.
queue = simpy.Store(env)        # Creating the buffer queue.
env.process(generator(env))     # Creating the generator process.
env.process(server(env))        # Creating the server process.
env.process(monitor(env))       # Creating the monitor process.
env.run(until=SIMULATION_TIME)  # Running simulation until specified time.

# Printing out some interesting collected data from simulation.
# Some data might be unnecessary but still collected.
print("\nNumber of packets sent from generator: {}".format(packets_sent))
print("Number of packets received: {}".format(packets_rec))
print("Number of packets dropped: {}".format(packets_drop))
print("Number of packets entered buffer: {}".format(packets_queue))
print("Number of packets processed: {}".format(packets_recorded))
print("Total amount of bytes processed: {}".format(bytes_recorded))

print("\nAverage time for packets in buffer: {:3f}".format(sum(queue_times)/len(queue_times)))
print("Average number of packets in buffer: {:3f}".format(sum(queue_sizes)/len(queue_sizes)))
print("Average amount of bytes in buffer: {:3f}".format(sum(byte_sizes)/len(byte_sizes)))

print("\nPercentage of packet loss: {:3f} %".format((float(packets_drop)/packets_rec)*100))
print("Percentage of packets entering buffer: {:3f} %".format((float(packets_queue)/packets_rec)*100))

# Is the mean buffer queuing delay accurate?
# Does it match the average time packages spend in the buffer?
mean_arrival_rate = 1.0/TIME_ARRIVAL
mean_service_requirement = 1.0/(SIZE_PACKET*8)
service_capacity = SERVER_RATE
mean_service_rate = mean_service_requirement*service_capacity
if (mean_service_rate - mean_arrival_rate == 0):
    mean_delay = 0
else:
    mean_delay = 1.0/(mean_service_rate - mean_arrival_rate)
print("\nMean infinite buffer queuing delay from calculation: {:3f}".format(mean_delay))

# Plotting some interesting grafs from simulation.
# Figure 1
fig, ax = plt.subplots(2, 2)
ax[0, 0].hist(queue_sizes, bins=100)
ax[0, 0].set_title("Buffer queue size in number of packets")
ax[0, 0].set_ylabel("Frequency of occurence")
ax[0, 0].set_xlabel("Number of packets")
ax[0, 0].grid()
# Figure 2
ax[0, 1].plot(samp_time, queue_avg_sizes)
ax[0, 1].set_title("Average buffer queue size in number of packets")
ax[0, 1].set_ylabel("Queue average size")
ax[0, 1].set_xlabel("Time")
ax[0, 1].grid()
# Figure 3
ax[1, 0].hist(queue_times, bins=100)
ax[1, 0].set_title("Amount of time each packet spend in buffer queue")
ax[1, 0].set_ylabel("Frequency of occurence")
ax[1, 0].set_xlabel("Time spent in queue")
ax[1, 0].grid()
# Figure 4
ax[1, 1].plot(packet_times, queue_avg_times)
ax[1, 1].set_title("Average amount of time each packet spend in buffer queue")
ax[1, 1].set_ylabel("Queue average times")
ax[1, 1].set_xlabel("Time")
ax[1, 1].grid()
# Show plotted graphs
plt.show()
