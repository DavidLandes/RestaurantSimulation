import simpy
import simpy.events
import random


# Restaurant class represents a Restaurant's drive thru process.
#            env: simpy simulation environment.
#   orderStation: simpy resource representing the order station.
#     payStation: simpy resource representing the pay station.
# pickoutStation: simpy resource representing the pickup station.
class Restaurant:

    NUM_OF_ORDER_STATIONS = 1
    NUM_OF_PAY_STATIONS = 1
    NUM_OF_PICKUP_STATIONS = 1

    restaurantNumber = 0

    # Action times in minutes.
    meanOrderTime = 3.0
    meanFoodPrepTime = 6.0
    meanPayTime = 2.0
    meanPickupTime = 2.0

    # Rate x / y where  x = number of customers for every y minutes.
    customerArrivalRate = 5.0 / 1.0

    def __init__(self, env, orderStation, payStation, pickupStation):
        self.env = env
        Restaurant.restaurantNumber += 1
        self.restaurantNumber = Restaurant.restaurantNumber
        self.customerList = []
        self.totalCustomers = 0
        self.numCustomersLeft = 0
        self.numCustomersStayed = 0

        # Stations.
        self.orderStation = orderStation
        self.payStation = payStation
        self.pickupStation = pickupStation

    # Generate new customers and send them through the drive thru line.
    def generate_customers(self, numOfCustomers):
        for c in range(numOfCustomers):
            # Generate customer.
            newCustomer = Customer(self.env, self)

            self.customerList.append(newCustomer)

            self.totalCustomers += 1
            env.process(newCustomer.start())

            # Customer arrives every x minutes
            t = random.expovariate(self.customerArrivalRate)
            yield env.timeout(t)
    
    # Average time a customer waited in the drive thru. Returns time in minutes.
    # NOTE: Value may not be accurate unless the simulation has already been ran.
    def calculateAverageDriveThruTime(self):
        averageTime = 0.0

        # customerList contains ALL potential customers, including those who entered the line AND those who left early..
        for person in self.customerList:
            if person.enterTime != -1.0 and person.exitTime != -1.0:
                timeSpent = person.exitTime - person.enterTime
                averageTime += timeSpent
        
        averageTime = float(averageTime / self.numCustomersStayed)
        return averageTime


    def printStats(self):
        print(f"--------------------------------------- Restaurant {self.restaurantNumber} Stats ---------------------------------------")
        print(f"{self.totalCustomers} potential customers..")
        print(f"{self.numCustomersLeft} customers left..")
        print(f"{self.numCustomersStayed} customers entered the line..\n")
        print(f"Average time spent in drive thru: {self.calculateAverageDriveThruTime()} minutes..")
        print("------------------------------------------------------------------------------------------------")



# Customer class represents one customer waiting in the queue.
#            env: simpy simulation environment.
#     restaurant: object of Restaurant class.
class Customer:
    
    # If true, print customer events to the console. Use for debugging.
    isEventStampingOn = True
    customerNumber = 0

    def __init__(self, env, restaurant):
        self.env = env
        self.restaurant = restaurant

        Customer.customerNumber += 1
        self.number = Customer.customerNumber

        # Track enter/exit in simulation time. 
        # Note: If the customer leaves because the line is too long, these values will remain -1.0
        self.enterTime = -1.0
        self.exitTime = -1.0

    # Start the simulation of customer going through drive thru line.
    def start(self):
        # Enter the drive thru if there is enough space. Max of 7 customers in line plus the 1 at each order station.
        if (len(self.restaurant.orderStation.queue) <= (7 + self.restaurant.orderStation.capacity)):

            self.event_stamp(f"Customer {self.number} enters the line. {len(self.restaurant.orderStation.queue)} customers in order line.")
            self.enterTime = env.now
            self.restaurant.numCustomersStayed += 1

            # Wait for an open order station.
            order = self.restaurant.orderStation.request()
            yield order

            # Enter the order station.
            self.event_stamp(f"Customer {self.number} is ordering.")
            delay = random.weibullvariate((1 / Restaurant.meanOrderTime), 1.5)
            orderTime = simpy.events.Timeout(env, delay)
            yield orderTime 

            # Start food prep.
            prepTimeDelay = random.weibullvariate((1 / Restaurant.meanFoodPrepTime), 2.0)
            prepTime = simpy.events.Timeout(env, prepTimeDelay)

            # Wait until there is enough space to move forward. Max 4 between order and pay station, plus 1 in the pay station.
            if (len(self.restaurant.payStation.queue) >= 5):
                self.event_stamp("pay station full... waiting...")
                yield self.restaurant.payStation.queue[0]

            # Finished ordering, leave the order station.
            self.restaurant.orderStation.release(order)


            # Wait for an open pay station.
            pay = self.restaurant.payStation.request()
            yield pay
            
            # Enter the pay station.
            self.event_stamp(f"Customer {self.number} is paying. {len(self.restaurant.payStation.queue)} customers in pay line.")
            delay = random.weibullvariate((1 / Restaurant.meanPayTime), 1.5)
            payTime = simpy.events.Timeout(env, delay)
            yield payTime

            # Wait until there is enough space to move forward. Max 1 between pay and pickup station, plus 1 in the pickup station.
            if (len(self.restaurant.pickupStation.queue) >= 2):
                self.event_stamp("pickup station full... waiting...")
                yield self.restaurant.pickupStation.queue[0]

            # Finished paying, leave the pay station.
            self.restaurant.payStation.release(pay)


            # Wait for an open pickup station.
            pickup = self.restaurant.pickupStation.request()
            yield pickup

            # Enter the pickup station.
            self.event_stamp(f"Customer {self.number} is picking up. {len(self.restaurant.pickupStation.queue)} customers in pickup line.")
            delay = random.weibullvariate((1 / Restaurant.meanPickupTime), 1.5)
            pickupTime = simpy.events.Timeout(env, delay)
            yield prepTime
            yield pickupTime

            # Finished picking up items, leave the pickup station.
            self.restaurant.pickupStation.release(pickup)
            self.event_stamp(f"Customer {self.number} exits the line.")
            self.exitTime = env.now
        else:
            self.event_stamp(f"Line too long. Customer {self.number} left.")
            self.restaurant.numCustomersLeft += 1
        return 1

        
    def event_stamp(self, eventMessage):
        if self.isEventStampingOn:
            # print(f"Order line: {len(self.restaurant.orderStation.queue)}\nPay line: {len(self.restaurant.payStation.queue)}\nPickup line: {len(self.restaurant.pickupStation.queue)}\n\n")
            print(f"{self.env.now} : {eventMessage}")



SIMULATION_ITERATIONS = 5
#random.seed(123456)

# Do we want to print customer events to the console window?
Customer.isEventStampingOn = False

# Run the simulation the given amount of times..
for iteration in range(0, SIMULATION_ITERATIONS):

    # Create the simulation environment.
    env = simpy.Environment()

    # Establish restaurant resources.
    orderStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_ORDER_STATIONS)
    payStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_PAY_STATIONS)
    pickupStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_PICKUP_STATIONS)

    # Generate the restaurant and the customers.
    restaurant = Restaurant(env, orderStation, payStation, pickupStation)
    customers = restaurant.generate_customers(50)
    env.process(customers)

    # Run for 120 minutes : 2 hours.
    env.run(120)
    restaurant.printStats()
