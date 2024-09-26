#  Assets market simulation with real-time arbitrage detection (Load balancing version)

Simulation of assets markets and service to detect arbitrage possibilities between markets.

(Arbitrage is a case, when buying price on one market is lower than selling price on a different market for the same asset)


## Consists of two applications: prices generator and prices analyzer

__1. Prices generator.__

Constantly updates prices for each asset on each market.

Provides read access to the current price of an asset on a specific market via API.


_In details:_ Having a list of assets (e.g. Copper, Oil, Corn) and markets (e.g. US, Asia, etc.) provided, randomly generates initial prices for each asset on each market, so that the initial price for the same asset is just slightly different across each market.
Then an infinite price update loop for each asset and market is started. On each iteration, the price is changed by a randomly generated value within the predefined range. Each loop runs independently using asynchronous tasks.


__2. Prices analyzer.__

Continuously queries for a current price for each asset on each market. If possibility for arbitrage is detected a message is output.

Accepts API endpoint URL, a list of assets and a list of markets as parameters.


# Deployment and infrastructure:

__1. Deployment__

Service deployment for the sample purpose is implemented via __Docker compose__.

Each service comes with its own environment variables that are injected when the container is spun up. It allows to use single image for spinning up several containers with different configuration parameters.

__2. Traffic routing__

Requests traffic is split between 2 groups of servers based on request API parameter leveraging Nginx.

__3. Load balancing__

Group 1 consists of 2 servers: assumed as 'strong' and 'weak' for this sample scenario. __Nginx__ used for __weighted load balancing__ between them with a ratio 3 to 1.

__4. Fault tolerance__

Implemented within Group 1 via Nginx. On 3 consecutive failed responses, traffic will be redirected to the 'healthy' server for 30 seconds, assuming this time is enough for a server to recover. After this timeout the traffic will be split according to the initial setup.


# Stack:

Business logic: __Python__

API interface: __FastAPI__

Concurrency: __Asyncio, multithreading__

Data typing: __Pydantic__

Deployment: __Docker__

Load balancing: __Nginx__

Traffic routing: __Nginx__

Fault tolerance: __Nginx__


# Prerequisites:

To run this project, you would need these frameworks / services installed:
Git, Python, PIP, Docker, Nginx, Make

# To install:

1. clone repo: 

`git clone git@github.com:evgenevolkov/arbitrage-detection.git`

2. If you are on MacOS or Linux: execute:

`make install`

Otherwise, manually create a virtual environment and install dependencies from `requirements.txt`.


# How to use:

The most recommended option is to spin up prices generation infrastructure leveraging Docker compose and Nginx.
Steps are:
1. Open terminal in the project root folder, execute `make` and select `Start generator with Nginx` option. This will build required Docker containers and spin them up. Once done you should be able to see  Nginx logs for each prices generation server.
2. Open separate terminal window and execute `make`. Select `Start analyzer`.  You should see logs of retrieved assets prices and updates. Once there is an opportunity of arbitrage, a dedicated message would be displayed.

Nginx logs report prices updates and incoming price requests processing. You can see that requests for markets UK, US, and Asia are routed to Group 2 server `prices_generator_2_1`, the rest are routed to Group 1 servers: `prices_generator_1_1` and `prices_generator_1_2` with ratio 1 to 3.


You can also spin each service separately using `make` menu, as well as `clean` once done to drop all containers and images created by Docker.

Also, you can initialize several `Price analyzer` instances in parallel, simulating higher load.


# Enjoy:)