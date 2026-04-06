import asyncio
import logging

from aio_pika import ExchangeType
from fastapi import APIRouter, WebSocket
from typing import Literal

from starlette.websockets import WebSocketDisconnect

from consumer import RabbitMQConsumer

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        exchange_type: Literal[ExchangeType.DIRECT, ExchangeType.FANOUT, ExchangeType.TOPIC],
        routing_key: str = ""
):
    # Принимаем соединение
    await websocket.accept()

    async with RabbitMQConsumer(exchange_type, routing_key) as consumer:
        consumer_task = asyncio.create_task(consumer.start_consuming(websocket))
        try:
            # Ждем, пока клиент не отключится (вызовет WebSocketDisconnect)
            while True:
                # Используем receive_text() просто для ожидания разрыва соединения
                # Полученные сообщения игнорируем
                data = await websocket.receive_text()
                logging.info(f"Received message (ignored): {data}")
        except WebSocketDisconnect:
            logging.info("Client disconnected gracefully")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
