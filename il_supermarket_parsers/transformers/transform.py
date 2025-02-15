from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Dict, Type
from pydantic import BaseModel
from typing import Type, TypeVar


T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


def map_model(source_cls: Type[T], destination_cls: Type[U], data: dict) -> U:
    data = source_cls.model_validate(data).model_dump()
    return destination_cls.model_validate(data)

