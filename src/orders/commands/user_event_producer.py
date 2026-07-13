"""
Kafka user event producer.
"""

import json
from typing import Dict, Any

import config
from kafka import KafkaProducer
from logger import Logger
from singleton import Singleton


class UserEventProducer(metaclass=Singleton):
    """Singleton wrapper around KafkaProducer for user domain events."""

    def __init__(self):
        self.logger = Logger.get_instance("UserEventProducer")
        self.producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_HOST,
            value_serializer=lambda event: json.dumps(event).encode("utf-8"),
        )

    def publish(self, topic: str, event: Dict[str, Any]) -> None:
        """Publish one event and flush so it is visible quickly during the lab demo."""
        future = self.producer.send(topic, value=event)
        future.get(timeout=10)
        self.producer.flush()
        self.logger.debug(f"Événement Kafka publié dans {topic}: {event}")

    def get_instance(self):
        """Backward-compatible accessor used by the lab template."""
        return self.producer