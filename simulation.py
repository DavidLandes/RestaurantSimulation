import simpy
import simpy.events
import random

# StationQueue class represents the line of a station in a Restaurant's drive thru. Certain queues can only hold a maximum number of customers.
#     Stores a first-in first-out line of Customer objects.
#            env: simpy simulation environment.
#        maxSize: maximum number of customers that will fit in this queue.
class StationQueue:
    def __init__(self, env, maxSize):
        self.env = env
        self.maxSize = maxSize
        self.queue = []

    # Push a customer to the back of the queue. 
    # Note: ONLY accepts Customer objects. Will not push customer if the queue is full.
    # Return True if customer was successfully added.
    def enqueue(self, customer):
        if (type(customer) == Customer and self.length() < self.maxSize):
            self.queue.append(customer)
            return True
        else:
            return False
    
    # Remove a customer from the front of the queue.
    # Return True if customer was successfully removed.
    def dequeue(self):
        if (len(self.queue) > 0):
            self.queue.remove(0)
            return True
        else:
            return False

    # Return the current number of customers waiting in this queue.
    def length(self):
        return len(self.queue)




# Restaurant class represents a Restaurant's drive thru process.
#            env: simpy simulation environment.
#   orderStation: simpy resource representing the order station.
#     payStation: simpy resource representing the pay station.
# pickoutStation: simpy resource representing the pickup station.
class Restaurant:

    NUM_OF_ORDER_STATIONS = 1
    NUM_OF_PAY_STATIONS = 1
    NUM_OF_PICKUP_STATIONS = 1
    meanOrderTime = 3.0
    meanFoodPrepTime = 6.0
    meanPayTime = 2.0
    meanPickupTime = 2.0
    # Rate x / y where  x = number of customers for every y units of time.
    customerArrivalRate = 1.0 / 2.0

    def __init__(self, env, orderStation, payStation, pickupStation):
        self.env = env

        # Queues for stations.
        self.orderQueue = StationQueue(env, 7)
        self.payQueue = StationQueue(env, 4)
        self.pickupQueue = StationQueue(env, 1)

        # Stations.
        self.orderStation = orderStation
        self.payStation = payStation
        self.pickupStation = pickupStation

    # Generate new customers and send them through the drive thru line.
    def generate_customers(self, numOfCustomers):
        for c in range(numOfCustomers):
            # Generate customer.
            newCustomer = Customer(self.env, self)
           # c = newCustomer.begin
            env.process(newCustomer.start())

            # Customer arrives every x minutes
            t = random.expovariate(self.customerArrivalRate)
            yield env.timeout(t)



# Customer class represents one customer waiting in the queue.
#            env: simpy simulation environment.
#     restaurant: object of Restaurant class.
class Customer:
    # TODO: prevent 
    customerNumber = 0

    def __init__(self, env, restaurant):
        self.env = env
        self.restaurant = restaurant
        Customer.customerNumber += 1
        self.number = Customer.customerNumber

    # Start the simulation of customer going through drive thru line.
    def start(self):
        self.event_stamp(f"Customer {self.number} enters the line.")
        # Wait for an open order station.
        order = self.restaurant.orderStation.request()
        yield order

        # Enter the order station.
        self.event_stamp(f"Customer {self.number} is ordering.")
        delay = random.weibullvariate((1 / Restaurant.meanOrderTime), 1.5)
        orderTime = simpy.events.Timeout(env, delay)
        yield orderTime 

        # Finished ordering, leave the order station.
        self.restaurant.orderStation.release(order)

        # Start food prep.
        prepTimeDelay = random.weibullvariate((1 / Restaurant.meanFoodPrepTime), 2.0)
        prepTime = simpy.events.Timeout(env, prepTimeDelay)


        # Wait for an open pay station.
        pay = self.restaurant.payStation.request()
        yield pay
        
        # Enter the pay station.
        self.event_stamp(f"Customer {self.number} is paying.")
        delay = random.weibullvariate((1 / Restaurant.meanPayTime), 1.5)
        payTime = simpy.events.Timeout(env, delay)
        yield payTime

        # Finished paying, leave the pay station.
        self.restaurant.payStation.release(pay)


        # Wait for an open pickup station.
        pickup = self.restaurant.pickupStation.request()
        yield pickup

        # Enter the pickup station.
        self.event_stamp(f"Customer {self.number} is picking up.")
        delay = random.weibullvariate((1 / Restaurant.meanPickupTime), 1.5)
        pickupTime = simpy.events.Timeout(env, delay)
        yield prepTime
        yield pickupTime

        # Finished picking up items, leave the pickup station.
        self.restaurant.pickupStation.release(pickup)
        self.event_stamp(f"Customer {self.number} exits the line.")

    
    def event_stamp(self, eventMessage):
        print(f"{self.env.now} : {eventMessage}")


random.seed(123456)

# Create the simulation environment.
env = simpy.Environment()

# Establish resources.
orderStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_ORDER_STATIONS)
payStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_PAY_STATIONS)
pickupStation = simpy.Resource(env, capacity=Restaurant.NUM_OF_PICKUP_STATIONS)

restuarant = Restaurant(env, orderStation, payStation, pickupStation)
customers = restuarant.generate_customers(10)
env.process(customers)

env.run()