import logging
import signal
import sys
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_NAME = "Server1Queue"
RABBITMQ_URL = "amqp://guest:guest@localhost:5672"


class RabbitMQConsumer:
    def __init__(self):
        self._connection: BlockingConnection = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel = None
        self._should_connect = False
        self._closing = False

    def connect(self) -> None:
        """Extablish RabbitMQ Connection"""
        try:
            self._connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=QUEUE_NAME, durable=True)
            logger.info("RabbitMQ connection established")
        except pika.exceptions.AMQPError as e:
            logger.error(f"RabbitMQ connection error: {e}")
            raise

    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        try:
            self._channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=self._process_message,
                auto_ack=True,
            )
            logger.info("Waiting for messages...")
            self._channel.start_consuming()
        except pika.exceptions.AMQPError as e:
            logger.error(f"Error while consuming messages: {e}")
            self.reconnect()

    def _process_message(
        self, channel: BlockingConnection, method: Any, properties: Any, body: bytes
    ) -> None:
        """Process incoming messages"""
        try:
            message = body.decode()
            logger.info(f"Received message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def reconnect(self) -> None:
        """Reconnect to RabbitMQ in not closing"""
        if self._closing:
            return
        self._should_connect = True
        self.stop()

    def stop(self) -> None:
        """Cleanly stop the consumer"""
        if self._channel and self._channel.is_open:
            logger.info("Closing RabbitMQ channel")
            self._channel.close()
        if self._connection and self._connection.is_open:
            logger.info("Closing RabbitMQ connection")
            self._connection.close()
        if self._should_connect:
            logger.info("Reconnecting to RabbitMQ")
            self.connect()
            self.start_consuming()


def main():
    """Main function to run RabbitMQ consumer"""
    consumer = RabbitMQConsumer()
    consumer.connect()

    def shutdown_handler(signum, frame):
        """Handle shutdown signal"""
        logger.info("Received shutdown signal")
        consumer._closing = True
        consumer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        shutdown_handler(None, None)


if __name__ == "__main__":
    main()
