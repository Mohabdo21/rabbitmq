import logging
from contextlib import asynccontextmanager
from typing import Optional

import pika
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pika.adapters.blocking_connection import BlockingChannel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_NAME = "Server1Queue"
RABBITMQ_URL = "amqp://guest:guest@localhost:5672"


def setup_rabbitmq() -> BlockingChannel:
    """Establish RabbitMQ Connection and channel"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        return channel
    except pika.exceptions.AMQPError as e:
        logger.error(f"RabbitMQ connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RabbitMQ connection error",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and clean up RabbitMQ resources"""
    app.state.rabbitmq_channel = setup_rabbitmq()
    yield

    if hasattr(app.state, "rabbitmq_channel"):
        app.state.rabbitmq_channel.close()
        logger.info("RabbitMQ connection closed")


app = FastAPI(lifespan=lifespan, title="RabbitMQ Producer API", version="1.0.0")


@app.get("/send")
async def send_message(msg: Optional[str] = None):
    """Publish a message to RabbitMQ queue"""
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )
    try:
        app.state.rabbitmq_channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=msg.encode(),
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        logger.info(f"Message sent: {msg}")
        return JSONResponse(
            content={"message": msg, "status": "Message sent"},
            status_code=status.HTTP_200_OK,
        )
    except pika.exceptions.AMQPError as e:
        logger.error(f"Message publish failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message publish failed",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
