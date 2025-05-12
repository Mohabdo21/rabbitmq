import amqp from "amqplib";
import winston from "winston";

// Configure logging
const logger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json(),
  ),
  transports: [new winston.transports.Console()],
});

const QUEUE_NAME = "Server1Queue";
const RABBITMQ_URL = "amqp://guest:guest@localhost:5672";

class RabbitMQConsumer {
  constructor() {
    this.connection = null;
    this.channel = null;
  }

  async connect() {
    try {
      this.connection = await amqp.connect(RABBITMQ_URL);
      this.channel = await this.connection.createChannel();

      await this.channel.assertQueue(QUEUE_NAME, {
        durable: true,
      });

      logger.info("RabbitMQ connection established");
    } catch (err) {
      logger.error(`RabbitMQ connection failed: ${err}`);
      throw err;
    }
  }

  async startConsuming() {
    try {
      await this.channel.consume(QUEUE_NAME, (message) => {
        if (message !== null) {
          try {
            const content = message.content.toString();
            logger.info(`Received message: ${content}`);

            // Process message here
            this.processMessage(content);

            this.channel.ack(message);
          } catch (err) {
            logger.error(`Message processing failed: ${err}`);
            this.channel.nack(message);
          }
        }
      });

      logger.info(`Waiting for messages in queue: ${QUEUE_NAME}`);
    } catch (err) {
      logger.error(`Consuming failed: ${err}`);
      throw err;
    }
  }

  processMessage(content) {
    // Implement your message processing logic
    logger.info(`Processing message: ${content}`);
  }

  async close() {
    try {
      if (this.channel) await this.channel.close();
      if (this.connection) await this.connection.close();
      logger.info("RabbitMQ connection closed");
    } catch (err) {
      logger.error(`Error closing connection: ${err}`);
    }
  }
}

// Main execution
const consumer = new RabbitMQConsumer();

async function main() {
  try {
    await consumer.connect();
    await consumer.startConsuming();

    // Graceful shutdown
    process.on("SIGTERM", async () => {
      logger.info("SIGTERM received - shutting down");
      await consumer.close();
      process.exit(0);
    });

    process.on("SIGINT", async () => {
      logger.info("SIGINT received - shutting down");
      await consumer.close();
      process.exit(0);
    });
  } catch (err) {
    logger.error(`Consumer failed: ${err}`);
    process.exit(1);
  }
}

main();
