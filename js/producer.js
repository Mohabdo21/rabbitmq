import express from "express";
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

class RabbitMQProducer {
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

  async publishMessage(message) {
    try {
      const sent = this.channel.sendToQueue(QUEUE_NAME, Buffer.from(message), {
        persistent: true,
      });

      if (!sent) {
        throw new Error("Message rejected by RabbitMQ");
      }

      logger.info(`Message published: ${message}`);
      return true;
    } catch (err) {
      logger.error(`Message publish failed: ${err}`);
      throw err;
    }
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

// Express App Setup
const app = express();
const producer = new RabbitMQProducer();

// Health check endpoint
app.get("/health", (req, res) => {
  res.status(200).json({ status: "healthy" });
});

// Message endpoint
app.get("/send", async (req, res) => {
  const { msg } = req.query;

  if (!msg) {
    logger.warn("Message validation failed");
    return res.status(400).json({ error: "Message is required" });
  }

  try {
    await producer.publishMessage(msg);
    res.status(200).json({ message: msg, status: "success" });
  } catch (err) {
    logger.error(`API error: ${err}`);
    res.status(500).json({ error: "Failed to publish message" });
  }
});

// Startup and Shutdown
async function startServer() {
  try {
    await producer.connect();

    const server = app.listen(8080, () => {
      logger.info("Producer service running on port 8080");
    });

    // Graceful shutdown
    process.on("SIGTERM", async () => {
      logger.info("SIGTERM received - shutting down");
      await producer.close();
      server.close(() => {
        process.exit(0);
      });
    });

    process.on("SIGINT", async () => {
      logger.info("SIGINT received - shutting down");
      await producer.close();
      server.close(() => {
        process.exit(0);
      });
    });
  } catch (err) {
    logger.error(`Startup failed: ${err}`);
    process.exit(1);
  }
}

startServer();
