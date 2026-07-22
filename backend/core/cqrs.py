# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""CQRS primitives for SafeVixAI Backend.

Enforces clean separation between Command (write/mutate) and Query (read/filter) pipelines.
"""
from __future__ import annotations

import abc
from typing import Generic, TypeVar

from fastapi import Request

T = TypeVar("T")
R = TypeVar("R")


class Command(Generic[R]):
    """Base class for all CQRS Commands (mutating state)."""


class Query(Generic[R]):
    """Base class for all CQRS Queries (non-mutating reading)."""


class CommandHandler(Generic[T, R], metaclass=abc.ABCMeta):
    """Base class for handling CQRS Commands."""

    @abc.abstractmethod
    async def handle(self, command: T) -> R:
        """Execute the command."""


class QueryHandler(Generic[T, R], metaclass=abc.ABCMeta):
    """Base class for handling CQRS Queries."""

    @abc.abstractmethod
    async def handle(self, query: T) -> R:
        """Execute the query."""


class CQRSBus:
    """In-memory dispatcher for CQRS Commands and Queries."""

    def __init__(self) -> None:
        self._command_handlers: dict[type, CommandHandler] = {}
        self._query_handlers: dict[type, QueryHandler] = {}

    def register_command_handler(self, command_type: type, handler: CommandHandler) -> None:
        self._command_handlers[command_type] = handler

    def register_query_handler(self, query_type: type, handler: QueryHandler) -> None:
        self._query_handlers[query_type] = handler

    async def execute_command(self, command: Command[R]) -> R:
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise NotImplementedError(f"No handler registered for command {type(command).__name__}")
        return await handler.handle(command)

    async def execute_query(self, query: Query[R]) -> R:
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise NotImplementedError(f"No handler registered for query {type(query).__name__}")
        return await handler.handle(query)


# Module-level default bus (backward compatible).
# For per-app-state isolation, use init_cqrs_bus(app) + get_cqrs_bus(request) instead.
cqrs_bus = CQRSBus()


def get_cqrs_bus(request: Request) -> CQRSBus:
    """FastAPI dependency — returns the per-app CQRSBus from request.app.state."""
    bus: CQRSBus | None = getattr(request.app.state, 'cqrs_bus', None)
    if bus is None:
        return cqrs_bus
    return bus


def init_cqrs_bus(app: FastAPI) -> CQRSBus:
    """Factory: creates a per-app CQRSBus, registers handlers, stores on app.state."""
    from services.roadwatch_service import (
        SubmitReportCommand,
        SubmitReportHandler,
        VerifyReportCommand,
        VerifyReportHandler,
    )

    bus = CQRSBus()
    bus.register_command_handler(SubmitReportCommand, SubmitReportHandler())
    bus.register_command_handler(VerifyReportCommand, VerifyReportHandler())
    app.state.cqrs_bus = bus
    return bus
