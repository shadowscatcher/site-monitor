from common.funcs import getenv


class EnvSettings:
    """
    Searches for env variables only when properties are accessed
    """
    @property
    def kafka_bootstrap_servers(self): return getenv('KAFKA_BOOTSTRAP_SERVERS')

    @property
    def kafka_cafile(self): return getenv('KAFKA_CAFILE', '')

    @property
    def kafka_certfile(self): return getenv('KAFKA_CERTFILE', '')

    @property
    def kafka_keyile(self): return getenv('KAFKA_KEYILE', '')

    @property
    def kafka_topic_failure(self): return getenv('KAFKA_TOPIC_FAILURE', 'checks-failure')

    @property
    def kafka_topic_success(self): return getenv('KAFKA_TOPIC_SUCCESS', 'checks-success')

    @property
    def kafka_consumer_group(self): return getenv('KAFKA_CONSUMER_GROUP', 'checks-consumer')

    @property
    def postgres_dsn(self): return getenv('POSTGRES_DSN')

    @property
    def certs_directory(self): return getenv('CERTIFICATES_DIR', 'certificates')

    @property
    def message_encoding(self): return getenv('MESSAGE_ENCODING', 'utf-8')

    @property
    def user_agent(self): return getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                                      '(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36')
