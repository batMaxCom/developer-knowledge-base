import logging
from typing import Literal

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from publisher import RabbitMQProducer

from aio_pika import ExchangeType

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        exchange_type: Literal[ExchangeType.DIRECT, ExchangeType.FANOUT, ExchangeType.TOPIC],
        routing_key: str = "",
        timeout: int = 5

):
    # Принимаем соединение
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            async with RabbitMQProducer(exchange_type) as client:
                response = await client.publish(
                    event=data,
                    routing_key=routing_key,
                    timeout=timeout
                )
            await websocket.send_json(response)
    except WebSocketDisconnect:
        logging.info("Client disconnected gracefully")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
