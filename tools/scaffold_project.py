"""MCP tool: scaffold_project — Generate a hexagonal architecture project.

This module defines the ``scaffold_project`` tool which accepts a project
name, a list of entity names, and optional configuration (stack, Python
version, database backend) and produces a complete hexagonal-architecture
project skeleton on disk.

Each entity generates files across all layers: domain model, repository
port, domain service, domain exceptions, use cases, application mapper,
ORM entity, infrastructure mapper, database repository, repository adapter,
controller, DI module, REST implementation, and test stubs.

The generated code follows the patterns defined in
``docs/hexagonal-architecture.md``.
"""

import logging
import re
import textwrap
from pathlib import Path

from utils.prompt_loader import load_prompt_cached

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PROMPT_FILENAME: str = "scaffold_project.md"
TOOL_NAME: str = "scaffold_project"
TOOL_DESCRIPTION: str = (
    "Generate a complete hexagonal-architecture Python project on disk. "
    "Accepts a project name, one or more entity names (comma-separated), "
    "an optional stack ('generic'), a Python version, and a "
    "database backend. Creates the full directory structure with boilerplate "
    "code for every layer: domain, application, infrastructure, REST, and "
    "tests — following the patterns defined in docs/hexagonal-architecture.md."
)

_SYSTEM_PROMPT: str = load_prompt_cached(PROMPT_FILENAME)

# ── Valid parameter values ───────────────────────────────────────────────────
VALID_STACKS: frozenset[str] = frozenset({"generic"})
VALID_DB_BACKENDS: frozenset[str] = frozenset({"postgresql", "mariadb", "sqlite"})

# ── Naming helpers ───────────────────────────────────────────────────────────


def _to_snake_case(name: str) -> str:
    """Convert a PascalCase or camelCase name to snake_case.

    Args:
        name: Entity name in any casing.

    Returns:
        The snake_case representation.
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_pascal_case(name: str) -> str:
    """Convert a snake_case or plain name to PascalCase.

    Args:
        name: Entity name in any casing.

    Returns:
        The PascalCase representation.
    """
    return "".join(word.capitalize() for word in re.split(r"[_\s-]+", name))


def _parse_entity_names(raw: str) -> list[tuple[str, str]]:
    """Parse a comma-separated entity string into (PascalCase, snake_case) tuples.

    Args:
        raw: Comma-separated entity names (e.g. "Catalog, Control, Framework").

    Returns:
        A list of (PascalCase, snake_case) name tuples.

    Raises:
        ValueError: If the input is empty or contains invalid names.
    """
    entities: list[tuple[str, str]] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        pascal = _to_pascal_case(token)
        snake = _to_snake_case(pascal)
        if not re.match(r"^[a-z][a-z0-9_]*$", snake):
            msg = f"Invalid entity name '{token}' — must be a valid Python identifier."
            raise ValueError(msg)
        entities.append((pascal, snake))
    if not entities:
        msg = "entity_names must not be empty. Provide at least one entity name."
        raise ValueError(msg)
    return entities


# ── File generators ──────────────────────────────────────────────────────────


def _w(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: Target file path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    logger.debug("Created: %s", path)


def _touch_init(directory: Path) -> None:
    """Create an empty ``__init__.py`` in the given directory.

    Args:
        directory: Target directory.
    """
    directory.mkdir(parents=True, exist_ok=True)
    init = directory / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")


# ---------------------------------------------------------------------------
# Domain layer
# ---------------------------------------------------------------------------


def _gen_domain_model(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a domain model file.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "domain" / "model" / f"{snake}.py"
    _w(
        p,
        f'''\
        """Domain model for {pascal}."""

        from dataclasses import dataclass
        from typing import Optional


        @dataclass
        class {pascal}:
            """{pascal} domain entity."""

            {snake}_id: Optional[int] = None
            name: Optional[str] = None
            description: Optional[str] = None

            def validate(self) -> None:
                """Validate business rules for {pascal}."""
                if not self.name or not self.name.strip():
                    raise ValueError("{pascal} name must not be empty")
        ''',
    )
    return p


def _gen_repository_port(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a repository port (ABC interface).

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "domain" / "repository" / f"{snake}_repository_port.py"
    _w(
        p,
        f'''\
        """Repository port for {pascal}."""

        from abc import ABC, abstractmethod
        from typing import Optional

        from sqlalchemy.ext.asyncio import AsyncSession

        from {proj}.domain.model.{snake} import {pascal}


        class {pascal}RepositoryPort(ABC):
            """Abstract port defining persistence operations for {pascal}."""

            @abstractmethod
            async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[{pascal}]:
                ...

            @abstractmethod
            async def search(
                self, db: AsyncSession, *, offset: int = 0, limit: int = 20
            ) -> tuple[list[{pascal}], int]:
                ...

            @abstractmethod
            async def create(
                self, db: AsyncSession, entity: {pascal}, *, auto_commit: bool = True
            ) -> {pascal}:
                ...

            @abstractmethod
            async def update(
                self, db: AsyncSession, entity: {pascal}, *, auto_commit: bool = True
            ) -> {pascal}:
                ...

            @abstractmethod
            async def delete(
                self, db: AsyncSession, entity_id: int, *, auto_commit: bool = True
            ) -> None:
                ...
        ''',
    )
    return p


def _gen_domain_service(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a domain service.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "domain" / "service" / f"{snake}_domain_service.py"
    _w(
        p,
        f'''\
        """Domain service for {pascal} business logic."""

        import logging
        from typing import Optional

        from sqlalchemy.ext.asyncio import AsyncSession

        from {proj}.domain.exception.domain_exceptions import (
            DomainNotFoundException,
        )
        from {proj}.domain.model.{snake} import {pascal}
        from {proj}.domain.repository.{snake}_repository_port import {pascal}RepositoryPort

        logger = logging.getLogger(__name__)


        class {pascal}DomainService:
            """Orchestrates business logic for {pascal}."""

            def __init__(self, repository: {pascal}RepositoryPort) -> None:
                self._repository = repository

            async def get(self, db: AsyncSession, entity_id: int) -> {pascal}:
                """Retrieve a {pascal} by ID.

                Args:
                    db: Async database session.
                    entity_id: Primary key of the entity.

                Returns:
                    The matching {pascal} domain model.

                Raises:
                    DomainNotFoundException: If no entity matches the given ID.
                """
                result = await self._repository.get_by_id(db, entity_id)
                if result is None:
                    raise DomainNotFoundException(f"{pascal} with id {{entity_id}} not found")
                return result

            async def search(
                self, db: AsyncSession, *, offset: int = 0, limit: int = 20
            ) -> tuple[list[{pascal}], int]:
                """Search {pascal} entities with pagination.

                Args:
                    db: Async database session.
                    offset: Number of records to skip.
                    limit: Maximum records to return.

                Returns:
                    A tuple of (entities, total_count).
                """
                return await self._repository.search(db, offset=offset, limit=limit)

            async def create(self, db: AsyncSession, entity: {pascal}) -> {pascal}:
                """Create a new {pascal}.

                Args:
                    db: Async database session.
                    entity: Domain model to persist.

                Returns:
                    The persisted {pascal} with assigned ID.
                """
                entity.validate()
                return await self._repository.create(db, entity)

            async def update(self, db: AsyncSession, entity: {pascal}) -> {pascal}:
                """Update an existing {pascal}.

                Args:
                    db: Async database session.
                    entity: Domain model with updated fields.

                Returns:
                    The updated {pascal}.
                """
                entity.validate()
                return await self._repository.update(db, entity)

            async def delete(self, db: AsyncSession, entity_id: int) -> None:
                """Delete a {pascal} by ID.

                Args:
                    db: Async database session.
                    entity_id: Primary key of the entity to remove.
                """
                await self._repository.delete(db, entity_id)
        ''',
    )
    return p


def _gen_domain_exceptions(pkg: Path) -> Path:
    """Generate domain exception classes.

    Args:
        pkg: Project package root path.

    Returns:
        The generated file path.
    """
    p = pkg / "domain" / "exception" / "domain_exceptions.py"
    _w(
        p,
        '''\
        """Domain-level exceptions."""


        class DomainException(Exception):
            """Base exception for domain layer."""


        class DomainNotFoundException(DomainException):
            """Raised when a domain entity is not found."""


        class DomainEntityAlreadyExistsException(DomainException):
            """Raised when attempting to create a duplicate entity."""


        class DomainValidationException(DomainException):
            """Raised when domain validation fails."""
        ''',
    )
    return p


# ---------------------------------------------------------------------------
# Application layer
# ---------------------------------------------------------------------------


def _gen_use_cases(pkg: Path, proj: str, pascal: str, snake: str) -> list[Path]:
    """Generate CRUD use cases for an entity.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        A list of generated file paths.
    """
    uc_dir = pkg / "application" / "use_case" / snake
    _touch_init(uc_dir)

    cases = [
        ("Get", "entity_id: int", f"return await self._service.get(db, entity_id)"),
        ("Create", f"entity: {pascal}", f"return await self._service.create(db, entity)"),
        ("Update", f"entity: {pascal}", f"return await self._service.update(db, entity)"),
        ("Delete", "entity_id: int", f"await self._service.delete(db, entity_id)\n        return None"),
    ]

    paths: list[Path] = []
    for verb, param, body in cases:
        verb_lower = verb.lower()
        ret = pascal if verb != "Delete" else "None"
        ret_import = (
            f"from {proj}.domain.model.{snake} import {pascal}\n" if verb in ("Create", "Update") else ""
        )
        p = uc_dir / f"{verb_lower}_{snake}_use_case.py"
        _w(
            p,
            f'''\
            """{verb} {pascal} use case."""

            from sqlalchemy.ext.asyncio import AsyncSession

            {ret_import}from {proj}.domain.service.{snake}_domain_service import {pascal}DomainService


            class {verb}{pascal}UseCase:
                """Use case: {verb.lower()} a {pascal}."""

                def __init__(self, service: {pascal}DomainService) -> None:
                    self._service = service

                async def execute(self, db: AsyncSession, {param}) -> {ret}:
                    """Execute the {verb.lower()} operation.

                    Args:
                        db: Async database session.
                        {param.split(':')[0].strip()}: {"Primary key" if "id" in param else "Domain model"}.

                    Returns:
                        {"The matching or persisted " + pascal if verb != "Delete" else "None"}.
                    """
                    {body}
            ''',
        )
        paths.append(p)
    return paths


def _gen_application_mapper(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate an application-layer mapper (DTO <-> domain).

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "application" / "mapper" / f"{snake}_mapper.py"
    _w(
        p,
        f'''\
        """Application mapper for {pascal} (DTO <-> domain model)."""

        from {proj}.domain.model.{snake} import {pascal}


        class {pascal}ApplicationMapper:
            """Maps between REST DTOs and {pascal} domain model."""

            @staticmethod
            def to_domain(dto: object) -> {pascal}:
                """Convert a request DTO to a {pascal} domain model.

                Args:
                    dto: Incoming request DTO.

                Returns:
                    A {pascal} domain model instance.
                """
                return {pascal}(
                    name=getattr(dto, "name", None),
                    description=getattr(dto, "description", None),
                )

            @staticmethod
            def to_response(entity: {pascal}) -> dict:
                """Convert a {pascal} domain model to a response dict.

                Args:
                    entity: {pascal} domain model.

                Returns:
                    A dict suitable for JSON serialisation.
                """
                return {{
                    "{snake}Id": entity.{snake}_id,
                    "name": entity.name or "",
                    "description": entity.description or "",
                }}

            @staticmethod
            def to_response_list(entities: list[{pascal}]) -> list[dict]:
                """Convert a list of domain models to response dicts.

                Args:
                    entities: List of {pascal} domain models.

                Returns:
                    A list of response dicts.
                """
                return [{pascal}ApplicationMapper.to_response(e) for e in entities]
        ''',
    )
    return p


# ---------------------------------------------------------------------------
# Infrastructure layer
# ---------------------------------------------------------------------------


def _gen_orm_base(pkg: Path) -> Path:
    """Generate the shared SQLAlchemy ``DeclarativeBase``.

    Args:
        pkg: Project package root path.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "repository" / "model" / "base.py"
    _w(
        p,
        '''\
        """Shared SQLAlchemy DeclarativeBase for all ORM entities."""

        from sqlalchemy.ext.asyncio import AsyncAttrs
        from sqlalchemy.orm import DeclarativeBase


        class Base(AsyncAttrs, DeclarativeBase):
            """Base class for all SQLAlchemy ORM entities."""
        ''',
    )
    return p


def _gen_orm_entity(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate an ORM entity.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "repository" / "model" / snake / f"{snake}_entity.py"
    _w(
        p,
        f'''\
        """ORM entity for {pascal}."""

        from sqlalchemy import Column, Integer, String

        from {proj}.infrastructure.repository.model.base import Base


        class {pascal}Entity(Base):
            """SQLAlchemy ORM entity for the {snake} table."""

            __tablename__ = "{snake}"

            {snake}_id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String(255), nullable=False)
            description = Column(String(4096), nullable=True)
        ''',
    )
    return p


def _gen_infra_mapper(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate an infrastructure mapper (domain <-> ORM entity).

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "mapper" / f"{snake}_domain_mapper.py"
    _w(
        p,
        f'''\
        """Infrastructure mapper between {pascal} domain model and ORM entity."""

        from typing import Optional

        from {proj}.domain.model.{snake} import {pascal}
        from {proj}.infrastructure.repository.model.{snake}.{snake}_entity import {pascal}Entity


        class {pascal}DomainMapper:
            """Maps between {pascal} domain model and ORM entity."""

            @staticmethod
            def to_domain(entity: Optional[{pascal}Entity]) -> Optional[{pascal}]:
                """Convert an ORM entity to a domain model.

                Args:
                    entity: ORM entity (may be None).

                Returns:
                    The corresponding domain model, or None.
                """
                if entity is None:
                    return None
                return {pascal}(
                    {snake}_id=entity.{snake}_id,
                    name=entity.name,
                    description=entity.description,
                )

            @staticmethod
            def to_entity(domain: {pascal}) -> {pascal}Entity:
                """Convert a domain model to an ORM entity.

                Args:
                    domain: {pascal} domain model.

                Returns:
                    The corresponding ORM entity.
                """
                return {pascal}Entity(
                    {snake}_id=domain.{snake}_id,
                    name=domain.name,
                    description=domain.description,
                )

            @staticmethod
            def to_domain_list(entities: list[{pascal}Entity]) -> list[{pascal}]:
                """Convert a list of ORM entities to domain models.

                Args:
                    entities: List of ORM entities.

                Returns:
                    List of domain models.
                """
                return [
                    mapped
                    for e in entities
                    if (mapped := {pascal}DomainMapper.to_domain(e)) is not None
                ]
        ''',
    )
    return p


def _gen_database_repository(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a concrete database repository for an entity.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "repository" / "database" / snake / f"{snake}_database_repository.py"
    _w(
        p,
        f'''\
        """Database repository for {pascal} ORM operations."""

        from {proj}.infrastructure.repository.database.read_write_database_repository import (
            ReadWriteDatabaseRepository,
        )
        from {proj}.infrastructure.repository.model.{snake}.{snake}_entity import {pascal}Entity


        class {pascal}DatabaseRepository(ReadWriteDatabaseRepository[{pascal}Entity]):
            """Concrete database repository for {pascal}Entity."""

            def get_entity_class(self) -> type[{pascal}Entity]:
                """Return the ORM entity class.

                Returns:
                    The {pascal}Entity class.
                """
                return {pascal}Entity

            def get_id_field_name(self) -> str:
                """Return the primary key field name.

                Returns:
                    The column name used as primary key.
                """
                return "{snake}_id"
        ''',
    )
    return p


def _gen_repository_adapter(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a repository adapter that implements the domain port.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "repository" / f"{snake}_repository.py"
    _w(
        p,
        f'''\
        """Repository adapter implementing {pascal}RepositoryPort."""

        from typing import Optional

        from sqlalchemy.ext.asyncio import AsyncSession

        from {proj}.domain.model.{snake} import {pascal}
        from {proj}.domain.repository.{snake}_repository_port import {pascal}RepositoryPort
        from {proj}.infrastructure.mapper.{snake}_domain_mapper import {pascal}DomainMapper
        from {proj}.infrastructure.repository.database.{snake}.{snake}_database_repository import (
            {pascal}DatabaseRepository,
        )


        class {pascal}Repository({pascal}RepositoryPort):
            """Adapter bridging the domain port and the database repository."""

            def __init__(self, db_repo: {pascal}DatabaseRepository) -> None:
                self._db_repo = db_repo

            async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[{pascal}]:
                """Retrieve by ID and map to domain model."""
                entity = await self._db_repo.get_by_id(db, entity_id)
                return {pascal}DomainMapper.to_domain(entity)

            async def search(
                self, db: AsyncSession, *, offset: int = 0, limit: int = 20
            ) -> tuple[list[{pascal}], int]:
                """Search with pagination and map results to domain models."""
                entities, total = await self._db_repo.search(db, offset=offset, limit=limit)
                return {pascal}DomainMapper.to_domain_list(entities), total

            async def create(
                self, db: AsyncSession, domain: {pascal}, *, auto_commit: bool = True
            ) -> {pascal}:
                """Persist a new entity."""
                orm_entity = {pascal}DomainMapper.to_entity(domain)
                created = await self._db_repo.create(db, orm_entity, auto_commit=auto_commit)
                return {pascal}DomainMapper.to_domain(created)  # type: ignore[return-value]

            async def update(
                self, db: AsyncSession, domain: {pascal}, *, auto_commit: bool = True
            ) -> {pascal}:
                """Update an existing entity."""
                orm_entity = {pascal}DomainMapper.to_entity(domain)
                updated = await self._db_repo.update(db, orm_entity, auto_commit=auto_commit)
                return {pascal}DomainMapper.to_domain(updated)  # type: ignore[return-value]

            async def delete(
                self, db: AsyncSession, entity_id: int, *, auto_commit: bool = True
            ) -> None:
                """Delete an entity by ID."""
                await self._db_repo.delete(db, entity_id, auto_commit=auto_commit)
        ''',
    )
    return p


def _gen_controller(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a hexagonal controller.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "controller" / f"{snake}_controller.py"
    _w(
        p,
        f'''\
        """Hexagonal controller for {pascal} operations."""

        from sqlalchemy.ext.asyncio import AsyncSession

        from {proj}.application.mapper.{snake}_mapper import {pascal}ApplicationMapper
        from {proj}.application.use_case.{snake}.create_{snake}_use_case import Create{pascal}UseCase
        from {proj}.application.use_case.{snake}.delete_{snake}_use_case import Delete{pascal}UseCase
        from {proj}.application.use_case.{snake}.get_{snake}_use_case import Get{pascal}UseCase
        from {proj}.application.use_case.{snake}.update_{snake}_use_case import Update{pascal}UseCase


        class {pascal}Controller:
            """Hexagonal controller for {pascal} CRUD operations."""

            def __init__(
                self,
                get_use_case: Get{pascal}UseCase,
                create_use_case: Create{pascal}UseCase,
                update_use_case: Update{pascal}UseCase,
                delete_use_case: Delete{pascal}UseCase,
            ) -> None:
                self._get_use_case = get_use_case
                self._create_use_case = create_use_case
                self._update_use_case = update_use_case
                self._delete_use_case = delete_use_case

            async def get(self, db: AsyncSession, entity_id: int) -> dict:
                """Get a {pascal} by ID and return as response dict.

                Args:
                    db: Async database session.
                    entity_id: Primary key.

                Returns:
                    Response dict.
                """
                entity = await self._get_use_case.execute(db, entity_id)
                return {pascal}ApplicationMapper.to_response(entity)

            async def create(self, db: AsyncSession, request: object) -> dict:
                """Create a {pascal} from a request DTO.

                Args:
                    db: Async database session.
                    request: Incoming request DTO.

                Returns:
                    Response dict of the created entity.
                """
                domain = {pascal}ApplicationMapper.to_domain(request)
                created = await self._create_use_case.execute(db, domain)
                return {pascal}ApplicationMapper.to_response(created)

            async def update(self, db: AsyncSession, entity_id: int, request: object) -> dict:
                """Update a {pascal}.

                Args:
                    db: Async database session.
                    entity_id: Primary key of the entity to update.
                    request: Incoming request DTO with updated fields.

                Returns:
                    Response dict of the updated entity.
                """
                domain = {pascal}ApplicationMapper.to_domain(request)
                domain.{snake}_id = entity_id
                updated = await self._update_use_case.execute(db, domain)
                return {pascal}ApplicationMapper.to_response(updated)

            async def delete(self, db: AsyncSession, entity_id: int) -> None:
                """Delete a {pascal} by ID.

                Args:
                    db: Async database session.
                    entity_id: Primary key of the entity to delete.
                """
                await self._delete_use_case.execute(db, entity_id)
        ''',
    )
    return p


def _gen_di_module(pkg: Path, proj: str, pascal: str, snake: str, stack: str) -> Path:
    """Generate a DI module (stack-dependent).

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.
        stack: ``"generic"``.

    Returns:
        The generated file path.
    """
    p = pkg / "infrastructure" / "di" / f"{snake}_module.py"
    if stack == "generic":
        _w(
            p,
            f'''\
            """DI wiring for {pascal} (generic stack)."""

            from {proj}.application.use_case.{snake}.create_{snake}_use_case import Create{pascal}UseCase
            from {proj}.application.use_case.{snake}.delete_{snake}_use_case import Delete{pascal}UseCase
            from {proj}.application.use_case.{snake}.get_{snake}_use_case import Get{pascal}UseCase
            from {proj}.application.use_case.{snake}.update_{snake}_use_case import Update{pascal}UseCase
            from {proj}.domain.service.{snake}_domain_service import {pascal}DomainService
            from {proj}.infrastructure.controller.{snake}_controller import {pascal}Controller
            from {proj}.infrastructure.repository.{snake}_repository import {pascal}Repository
            from {proj}.infrastructure.repository.database.{snake}.{snake}_database_repository import (
                {pascal}DatabaseRepository,
            )


            def wire_{snake}() -> {pascal}Controller:
                """Manually wire all {pascal} dependencies and return the controller.

                Returns:
                    A fully wired {pascal}Controller instance.
                """
                db_repo = {pascal}DatabaseRepository()
                repository = {pascal}Repository(db_repo=db_repo)
                service = {pascal}DomainService(repository=repository)

                get_uc = Get{pascal}UseCase(service=service)
                create_uc = Create{pascal}UseCase(service=service)
                update_uc = Update{pascal}UseCase(service=service)
                delete_uc = Delete{pascal}UseCase(service=service)

                return {pascal}Controller(
                    get_use_case=get_uc,
                    create_use_case=create_uc,
                    update_use_case=update_uc,
                    delete_use_case=delete_uc,
                )
            ''',
        )
    return p


def _gen_rest_impl(pkg: Path, proj: str, pascal: str, snake: str) -> Path:
    """Generate a REST API implementation stub.

    Args:
        pkg: Project package root path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        The generated file path.
    """
    p = pkg / "rest_impl" / f"{snake}_api_impl.py"
    _w(
        p,
        f'''\
        """REST implementation for {pascal} endpoints."""

        from {proj}.infrastructure.controller.{snake}_controller import {pascal}Controller


        class {pascal}ApiImpl:
            """REST API implementation delegating to {pascal}Controller."""

            def __init__(self, controller: {pascal}Controller) -> None:
                self._controller = controller
        ''',
    )
    return p


# ---------------------------------------------------------------------------
# Shared / infrastructure files
# ---------------------------------------------------------------------------


def _gen_shared_exceptions(pkg: Path) -> Path:
    """Generate shared HTTP exception classes.

    Args:
        pkg: Project package root path.

    Returns:
        The generated file path.
    """
    p = pkg / "exception" / "__init__.py"
    _w(
        p,
        '''\
        """Shared application-level exceptions."""


        class NotFoundException(Exception):
            """HTTP 404 — requested resource not found."""


        class ConflictException(Exception):
            """HTTP 409 — resource already exists or conflicts."""


        class BadRequestException(Exception):
            """HTTP 400 — invalid input or parameters."""


        class ForbiddenException(Exception):
            """HTTP 403 — insufficient permissions."""
        ''',
    )
    return p


def _gen_base_database_repos(pkg: Path) -> list[Path]:
    """Generate read-only and read-write base database repository classes.

    Args:
        pkg: Project package root path.

    Returns:
        A list of generated file paths.
    """
    db_dir = pkg / "infrastructure" / "repository" / "database"
    _touch_init(db_dir)

    paths: list[Path] = []

    # Read-only base
    ro = db_dir / "read_only_database_repository.py"
    _w(
        ro,
        '''\
        """Abstract read-only database repository base."""

        from abc import ABC, abstractmethod
        from typing import Generic, Optional, TypeVar

        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import AsyncSession

        T = TypeVar("T")


        class ReadOnlyDatabaseRepository(ABC, Generic[T]):
            """Base class for read-only database operations."""

            @abstractmethod
            def get_entity_class(self) -> type[T]:
                """Return the ORM entity class."""
                ...

            @abstractmethod
            def get_id_field_name(self) -> str:
                """Return the primary key field name."""
                ...

            async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[T]:
                """Retrieve a single entity by primary key.

                Args:
                    db: Async database session.
                    entity_id: Primary key value.

                Returns:
                    The entity or None if not found.
                """
                entity_cls = self.get_entity_class()
                id_field = getattr(entity_cls, self.get_id_field_name())
                stmt = select(entity_cls).where(id_field == entity_id)
                result = await db.execute(stmt)
                return result.scalar_one_or_none()

            async def search(
                self, db: AsyncSession, *, offset: int = 0, limit: int = 20
            ) -> tuple[list[T], int]:
                """Search with pagination.

                Args:
                    db: Async database session.
                    offset: Number of records to skip.
                    limit: Maximum records to return.

                Returns:
                    A tuple of (entities, total_count).
                """
                entity_cls = self.get_entity_class()
                count_stmt = select(func.count()).select_from(entity_cls)
                total = (await db.execute(count_stmt)).scalar() or 0

                stmt = select(entity_cls).offset(offset).limit(limit)
                result = await db.execute(stmt)
                return list(result.scalars().all()), total
        ''',
    )
    paths.append(ro)

    # Read-write base
    rw = db_dir / "read_write_database_repository.py"
    _w(
        rw,
        '''\
        """Abstract read-write database repository base."""

        from typing import TypeVar

        from sqlalchemy.ext.asyncio import AsyncSession

        from .read_only_database_repository import ReadOnlyDatabaseRepository

        T = TypeVar("T")


        class ReadWriteDatabaseRepository(ReadOnlyDatabaseRepository[T]):
            """Base class for read-write database operations."""

            async def create(self, db: AsyncSession, entity: T, *, auto_commit: bool = True) -> T:
                """Persist a new entity.

                Args:
                    db: Async database session.
                    entity: ORM entity to insert.
                    auto_commit: Whether to commit the transaction.

                Returns:
                    The persisted entity with assigned PK.
                """
                db.add(entity)
                if auto_commit:
                    await db.commit()
                    await db.refresh(entity)
                return entity

            async def update(self, db: AsyncSession, entity: T, *, auto_commit: bool = True) -> T:
                """Merge an existing entity.

                Args:
                    db: Async database session.
                    entity: ORM entity with updated fields.
                    auto_commit: Whether to commit the transaction.

                Returns:
                    The merged entity.
                """
                merged = await db.merge(entity)
                if auto_commit:
                    await db.commit()
                    await db.refresh(merged)
                return merged

            async def delete(self, db: AsyncSession, entity_id: int, *, auto_commit: bool = True) -> None:
                """Delete an entity by primary key.

                Args:
                    db: Async database session.
                    entity_id: Primary key value.
                    auto_commit: Whether to commit the transaction.
                """
                entity = await self.get_by_id(db, entity_id)
                if entity:
                    await db.delete(entity)
                    if auto_commit:
                        await db.commit()
        ''',
    )
    paths.append(rw)

    # Database factory
    factory = db_dir / "factory.py"
    _w(
        factory,
        '''\
        """Database session factory."""

        from contextlib import asynccontextmanager
        from typing import AsyncIterator

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


        class DatabaseFactory:
            """Manages async database engine and sessions."""

            def __init__(self, database_url: str) -> None:
                self._engine = create_async_engine(database_url, echo=False)
                self._session_factory = async_sessionmaker(
                    self._engine, expire_on_commit=False
                )

            @asynccontextmanager
            async def get_session(self) -> AsyncIterator[AsyncSession]:
                """Provide a transactional async session.

                Yields:
                    An ``AsyncSession`` instance.
                """
                async with self._session_factory() as session:
                    yield session
        ''',
    )
    paths.append(factory)

    return paths


def _gen_pyproject(code_dir: Path, proj: str, stack: str, python_version: str, db_backend: str) -> Path:
    """Generate ``pyproject.toml`` for the scaffolded project.

    Args:
        code_dir: The ``code/`` directory path.
        proj: Project name (snake_case).
        stack: ``"generic"``.
        python_version: Target Python version (e.g. ``"3.11"``).
        db_backend: Database backend (``"postgresql"``, ``"mariadb"``, ``"sqlite"``).

    Returns:
        The generated file path.
    """
    db_drivers = {
        "postgresql": '"asyncpg>=0.29.0"',
        "mariadb": '"aiomysql>=0.2.0"',
        "sqlite": '"aiosqlite>=0.20.0"',
    }
    driver_dep = db_drivers.get(db_backend, '"asyncpg>=0.29.0"')

    if stack == "generic":
        deps = f"""\
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    {driver_dep},
]"""

    p = code_dir / "pyproject.toml"
    _w(
        p,
        f'''\
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        name = "{proj}"
        version = "0.1.0"
        requires-python = ">={python_version}"
        {deps}

        [project.optional-dependencies]
        dev = [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.24.0",
            "pytest-cov>=6.0.0",
            "ruff>=0.8.0",
        ]

        [tool.ruff]
        line-length = 120
        target-version = "py{python_version.replace('.', '')}"

        [tool.ruff.lint]
        select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

        [tool.pytest.ini_options]
        asyncio_mode = "auto"
        testpaths = ["tests"]
        ''',
    )
    return p


def _gen_conftest(tests_dir: Path) -> Path:
    """Generate a shared ``conftest.py`` with common test fixtures.

    Args:
        tests_dir: The ``tests/`` directory path.

    Returns:
        The generated file path.
    """
    p = tests_dir / "conftest.py"
    _w(
        p,
        '''\
        """Shared test fixtures."""

        import pytest
        from unittest.mock import AsyncMock


        @pytest.fixture
        def mock_async_session():
            """Provide a mocked AsyncSession for unit tests."""
            session = AsyncMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            session.execute = AsyncMock()
            session.add = AsyncMock()
            session.delete = AsyncMock()
            session.merge = AsyncMock()
            return session
        ''',
    )
    return p


def _gen_test_stubs(tests_dir: Path, proj: str, pascal: str, snake: str) -> list[Path]:
    """Generate test stubs for an entity across all layers.

    Args:
        tests_dir: The ``tests/`` directory path.
        proj: Project name (snake_case).
        pascal: Entity name in PascalCase.
        snake: Entity name in snake_case.

    Returns:
        A list of generated test file paths.
    """
    paths: list[Path] = []

    # Domain model test
    base = tests_dir / "unit" / proj

    dm_test = base / "domain" / "model" / f"test_{snake}.py"
    _w(
        dm_test,
        f'''\
        """Tests for {pascal} domain model."""

        import pytest

        from {proj}.domain.model.{snake} import {pascal}


        class Test{pascal}:
            """Unit tests for the {pascal} domain model."""

            def test_create_valid_entity(self):
                """Test creating a valid {pascal} instance."""
                entity = {pascal}(name="Test {pascal}")
                assert entity.name == "Test {pascal}"
                assert entity.{snake}_id is None

            def test_validate_raises_on_empty_name(self):
                """Test that validate raises ValueError for empty name."""
                entity = {pascal}(name="")
                with pytest.raises(ValueError, match="must not be empty"):
                    entity.validate()

            def test_validate_passes_for_valid_entity(self):
                """Test that validate passes for a well-formed entity."""
                entity = {pascal}(name="Valid Name")
                entity.validate()  # Should not raise
        ''',
    )
    paths.append(dm_test)

    # Domain service test
    ds_test = base / "domain" / "service" / f"test_{snake}_domain_service.py"
    _w(
        ds_test,
        f'''\
        """Tests for {pascal}DomainService."""

        import pytest
        from unittest.mock import AsyncMock

        from {proj}.domain.exception.domain_exceptions import DomainNotFoundException
        from {proj}.domain.model.{snake} import {pascal}
        from {proj}.domain.service.{snake}_domain_service import {pascal}DomainService


        class Test{pascal}DomainService:
            """Unit tests for {pascal}DomainService."""

            @pytest.fixture
            def mock_repository(self):
                """Provide a mocked repository port."""
                return AsyncMock()

            @pytest.fixture
            def service(self, mock_repository):
                """Provide a service instance with mocked repository."""
                return {pascal}DomainService(repository=mock_repository)

            async def test_get_existing_entity(self, service, mock_repository, mock_async_session):
                """Test retrieving an existing entity by ID."""
                expected = {pascal}({snake}_id=1, name="Test")
                mock_repository.get_by_id.return_value = expected

                result = await service.get(mock_async_session, entity_id=1)

                assert result == expected
                mock_repository.get_by_id.assert_called_once_with(mock_async_session, 1)

            async def test_get_nonexistent_entity_raises(self, service, mock_repository, mock_async_session):
                """Test that getting a nonexistent entity raises DomainNotFoundException."""
                mock_repository.get_by_id.return_value = None

                with pytest.raises(DomainNotFoundException):
                    await service.get(mock_async_session, entity_id=999)
        ''',
    )
    paths.append(ds_test)

    # Use case test
    uc_test = base / "application" / "use_case" / snake / f"test_get_{snake}_use_case.py"
    _w(
        uc_test,
        f'''\
        """Tests for Get{pascal}UseCase."""

        import pytest
        from unittest.mock import AsyncMock

        from {proj}.domain.model.{snake} import {pascal}
        from {proj}.application.use_case.{snake}.get_{snake}_use_case import Get{pascal}UseCase


        class TestGet{pascal}UseCase:
            """Unit tests for Get{pascal}UseCase."""

            @pytest.fixture
            def mock_service(self):
                """Provide a mocked domain service."""
                return AsyncMock()

            @pytest.fixture
            def use_case(self, mock_service):
                """Provide a use case instance with mocked service."""
                return Get{pascal}UseCase(service=mock_service)

            async def test_execute_returns_entity(self, use_case, mock_service, mock_async_session):
                """Test that execute delegates to the domain service."""
                expected = {pascal}({snake}_id=1, name="Test")
                mock_service.get.return_value = expected

                result = await use_case.execute(mock_async_session, entity_id=1)

                assert result == expected
                mock_service.get.assert_called_once_with(mock_async_session, 1)
        ''',
    )
    paths.append(uc_test)

    return paths


# ── Main function ────────────────────────────────────────────────────────────


def scaffold_project(  # noqa: PLR0913
    project_name: str,
    entity_names: str,
    stack: str = "generic",
    python_version: str = "3.11",
    db_backend: str = "postgresql",
    base_path: str = "",
    repo_context: str = "",
) -> str:
    """Generate a hexagonal-architecture Python project on disk.

    Creates a complete directory structure with boilerplate code for every
    layer (domain, application, infrastructure, REST, tests) following the
    patterns defined in ``docs/hexagonal-architecture.md``.

    Args:
        project_name: Name of the project (used for the Python package).
            Will be normalised to snake_case.
        entity_names: Comma-separated list of entity names
            (e.g. ``"Catalog, Control, Framework"``).
        stack: Target stack — ``"generic"`` for vanilla FastAPI.
            Defaults to ``"generic"``.
        python_version: Target Python version (e.g. ``"3.11"``).
            Defaults to ``"3.11"``.
        db_backend: Database backend — ``"postgresql"`` (default),
            ``"mariadb"``, or ``"sqlite"``.
        base_path: Root directory where the project will be created.
            Defaults to the current working directory.
        repo_context: Free-text description of additional project context
            such as existing coding conventions or architectural decisions
            (optional).

    Returns:
        A structured Markdown report containing the system prompt,
        scaffold summary, and next steps.

    Raises:
        ValueError: If ``project_name`` is empty, ``entity_names`` is empty
            or contains invalid names, ``stack`` is not recognised, or
            ``db_backend`` is not supported.
        OSError: If file or directory creation fails (permissions, disk, etc.).
    """
    # ── Validate inputs ──────────────────────────────────────────────────
    if not project_name or not project_name.strip():
        msg = "project_name must not be empty. Provide a valid Python package name."
        raise ValueError(msg)

    proj = _to_snake_case(project_name.strip())
    if not re.match(r"^[a-z][a-z0-9_]*$", proj):
        msg = f"project_name '{project_name}' is not a valid Python package name."
        raise ValueError(msg)

    if stack not in VALID_STACKS:
        msg = f"Invalid stack '{stack}'. Must be one of: {sorted(VALID_STACKS)}"
        raise ValueError(msg)

    if db_backend not in VALID_DB_BACKENDS:
        msg = f"Invalid db_backend '{db_backend}'. Must be one of: {sorted(VALID_DB_BACKENDS)}"
        raise ValueError(msg)

    entities = _parse_entity_names(entity_names)

    logger.info(
        "scaffold_project invoked — project=%s, stack=%s, entities=%s, db=%s",
        proj,
        stack,
        [e[0] for e in entities],
        db_backend,
    )

    # ── Resolve paths ────────────────────────────────────────────────────
    root = Path(base_path).resolve() if base_path else Path.cwd()
    code_dir = root / "code"
    pkg = code_dir / proj
    tests_dir = code_dir / "tests"

    # ── Create package directories ───────────────────────────────────────
    for subdir in [
        "domain/model",
        "domain/repository",
        "domain/service",
        "domain/exception",
        "application/mapper",
        "infrastructure/di",
        "infrastructure/controller",
        "infrastructure/mapper",
        "infrastructure/repository/model",
        "infrastructure/repository/database",
        "rest_impl",
        "exception",
    ]:
        _touch_init(pkg / subdir)

    _touch_init(tests_dir)
    _touch_init(tests_dir / "unit" / proj)
    _touch_init(tests_dir / "integration" / proj)

    # ── Generate shared files ────────────────────────────────────────────
    generated_files: list[str] = []

    p = _gen_domain_exceptions(pkg)
    generated_files.append(str(p.relative_to(root)))

    p = _gen_shared_exceptions(pkg)
    generated_files.append(str(p.relative_to(root)))

    p = _gen_orm_base(pkg)
    generated_files.append(str(p.relative_to(root)))

    for p in _gen_base_database_repos(pkg):
        generated_files.append(str(p.relative_to(root)))

    p = _gen_pyproject(code_dir, proj, stack, python_version, db_backend)
    generated_files.append(str(p.relative_to(root)))

    p = _gen_conftest(tests_dir)
    generated_files.append(str(p.relative_to(root)))

    # ── Generate per-entity files ────────────────────────────────────────
    for pascal, snake in entities:
        # Ensure entity-specific subdirectories
        _touch_init(pkg / "infrastructure" / "repository" / "model" / snake)
        _touch_init(pkg / "infrastructure" / "repository" / "database" / snake)
        _touch_init(tests_dir / "unit" / proj / "domain" / "model")
        _touch_init(tests_dir / "unit" / proj / "domain" / "service")
        _touch_init(tests_dir / "unit" / proj / "application" / "use_case" / snake)

        # Domain layer
        p = _gen_domain_model(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_repository_port(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_domain_service(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        # Application layer
        for uc_path in _gen_use_cases(pkg, proj, pascal, snake):
            generated_files.append(str(uc_path.relative_to(root)))

        p = _gen_application_mapper(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        # Infrastructure layer
        p = _gen_orm_entity(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_infra_mapper(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_database_repository(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_repository_adapter(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_controller(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_di_module(pkg, proj, pascal, snake, stack)
        generated_files.append(str(p.relative_to(root)))

        p = _gen_rest_impl(pkg, proj, pascal, snake)
        generated_files.append(str(p.relative_to(root)))

        # Tests
        for t_path in _gen_test_stubs(tests_dir, proj, pascal, snake):
            generated_files.append(str(t_path.relative_to(root)))

    # ── Assemble output ──────────────────────────────────────────────────
    sections: list[str] = [_SYSTEM_PROMPT]

    # Scaffold summary
    entity_list = ", ".join(f"`{e[0]}`" for e in entities)
    summary_lines = [
        f"## Scaffold Summary for `{proj}`\n",
        "### Configuration\n",
        f"- **Stack**: {stack}",
        f"- **Database**: {db_backend}",
        f"- **Python**: {python_version}",
        f"- **Entities**: {entity_list}",
        f"- **Output directory**: `{root}`",
    ]
    sections.append("\n".join(summary_lines))

    # File list table
    table_lines = ["### Files Generated\n", "| # | Path | Description |", "|---|------|-------------|"]
    for i, fpath in enumerate(generated_files, 1):
        desc = _describe_file(fpath)
        table_lines.append(f"| {i} | `{fpath}` | {desc} |")
    sections.append("\n".join(table_lines))

    # Repo context
    if repo_context and repo_context.strip():
        sections.append(f"## Repository Context\n\n{repo_context.strip()}")

    # Next steps
    next_steps = (
        "## Next Steps\n\n"
        "1. Review and customise the generated domain models — add real fields.\n"
        "2. Add business-specific validation logic to `validate()` methods.\n"
        "3. Define real database column types in ORM entities.\n"
        "4. Implement search/filter logic in database repositories.\n"
        "5. Run `uv sync` to install dependencies.\n"
        "6. Run `uv run pytest` to verify the test skeleton passes."
    )
    sections.append(next_steps)

    total = len(generated_files)
    logger.info("scaffold_project completed — %d files generated under %s", total, root)
    return "\n\n---\n\n".join(sections)


def _describe_file(path: str) -> str:
    """Return a human-readable description for a generated file path.

    Args:
        path: Relative file path.

    Returns:
        A short description string.
    """
    name = Path(path).name
    if name == "pyproject.toml":
        return "Project metadata and dependencies"
    if name == "conftest.py":
        return "Shared test fixtures"
    if name == "domain_exceptions.py":
        return "Domain exception classes"
    if name == "__init__.py" and "exception" in path:
        return "Shared HTTP exceptions"
    if name == "base.py":
        return "SQLAlchemy DeclarativeBase"
    if name == "factory.py":
        return "Database session factory"
    if name == "read_only_database_repository.py":
        return "Abstract read-only repository base"
    if name == "read_write_database_repository.py":
        return "Abstract read-write repository base"

    # Per-entity files
    if "domain/model/" in path:
        return "Domain model"
    if "_repository_port.py" in path:
        return "Repository port (ABC)"
    if "_domain_service.py" in path:
        return "Domain service"
    if "_use_case.py" in path:
        return "Use case"
    if "application/mapper/" in path:
        return "Application mapper (DTO ↔ domain)"
    if "_entity.py" in path:
        return "ORM entity"
    if "_domain_mapper.py" in path:
        return "Infrastructure mapper (domain ↔ entity)"
    if "_database_repository.py" in path:
        return "Database repository"
    if "infrastructure/repository/" in path and "_repository.py" in name:
        return "Repository adapter"
    if "_controller.py" in path:
        return "Hexagonal controller"
    if "_module.py" in path:
        return "DI module"
    if "_api_impl.py" in path:
        return "REST API implementation"
    if path.startswith("code/tests/") or "test_" in name:
        return "Test stub"

    return "Generated file"
