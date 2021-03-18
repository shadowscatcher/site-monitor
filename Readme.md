# Description
This solution allows you to monitor website accessibility and store metrics in database

## Architecture
The project consists of two services:
 - Producer. Sends HTTP requests to website(s) with some interval and pushes metrics like response time and status code to Kafka topics
 - Consumer. Listens to Kafka topics and stores received data in Postgres tables

Project uses [pipenv](https://pipenv-fork.readthedocs.io/en/latest/) for dependency management. This allows having separate package lists for development and deploy. Project dependencies can be installed with the following commands:

```shell
pip3 install pipenv
pipenv install  # --dev to also install development packages
```

## Deploy
There are three variants available, all use docker-compose with local docker installation and have configs and simple `run.sh` scripts in `deploy` directory.
Services use environment variables for configuration, they should be set in `.env` file in corresponding directory. 

Here is the list of all used variables with example values:
```
POSTGRES_USER=monitoring # required for postgres container initialization
POSTGRES_PASSWORD=secret # required for postgres container initialization
POSTGRES_DSN=postgres://monitoring:secret@postgres:5432/postgres  # required to connect to postgres from worker

KAFKA_TOPIC_SUCCESS=checks-success  # name of topic with metrics
KAFKA_TOPIC_FAILURE=checks-failure  # name of topic with error
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# for local deployments, do not set these variables
# for prod deployment, create directory "certificates/kafka" in project root and put certificate files there
KAFKA_CAFILE=/var/certs/kafka/ca.pem
KAFKA_CERTFILE=/var/certs/kafka/service.cert
KAFKA_KEYILE=/var/certs/kafka/service.key

LOGURU_LEVEL=INFO
COMPOSE_PROJECT_NAME=local  # better have unique project names for all deploys
```

### Local deploy

Will deploy both workers, kafka and postgres within one network. Set up `deploy/local/.env` file (or leave as is) and run following command in project root:

```shell
bash deploy/local/run.sh
```

To clean up containers, run

```shell
bash deploy/local/cleanup.sh
```

### Test deploy

Will spin up kafka and postgres and run integration tests with pytest. One of the tests will require internet connection.

Set up `deploy/test/.env` file (or leave as is) and run following command in project root:

```shell
bash deploy/test/run.sh
```

This script will clean up containers after run.

### Prod deploy

This deployment will run only producer and consumer in a local docker and connect to cloud postgres and kafka. 
**Kafka topics are expected to exist**, postgres relations will be created in default schema.

This configuration uses SSL kafka authentication. In project root create `certificates` directory as following:

```

├── certificates
│   ├── kafka
│   │   ├── ca.pem
│   │   ├── service.cert
│   │   └── service.key
```

Set up your `.env` file (don't forget to add variables with cert paths) in `deploy/prod` and run following command in project root:

```shell
bash deploy/prod/run.sh
```

To clean up containers, run

```shell
bash deploy/prod/cleanup.sh
```

## Implementation details

Both services use the same concepts under hood:

- *Workers* are responsible for task processing. There are three kinds of workers present: *AsyncSitePoller*, *KafkaPublisher* and *DbWriter*.
- *TaskProviders* are responsible for sending tasks to first workers. Examples of providers in projects are *QueueTaskProvider* and *KafkaTaskProvider*.
- *Composer* creates a pipeline with task provider, processing and [optional] publishing workers and starts this pipeline in background tasks. *asyncio* queues are used for messaging between workers.
- *Scheduler* is responsible for running periodic code.

When each service starts, *main* function resolves necessary dependencies, sends them to *Composer* instance and waits indefinitely.

Producer workflow:
```
Scheduler -> QueueTaskProvider -> AsyncSitePoller -> KafkaPublisher -> [Kafka]
```

Consumer workflow:
```
[Kafka] -> KafkaTaskProvider -> DbWriter -> [Postgres]
```

### Configuration

Producer can be started with one site to watch with command like following:

```shell
python main.py --mode=producer --url=http://www.isdelphidead.com --seconds=30 --pattern="Yes"
```
Or with multiple target sites with config file (see example file in `configs`):

```shell
python main.py --mode=producer --targets-file=/var/configs/sites.yaml
```

Unit tests can be launched with the following command:

```shell
pytest src/tests -m "not integration"
```

This command will exclude integration tests, which require database and working internet connection.