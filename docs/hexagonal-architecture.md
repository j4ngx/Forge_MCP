# Hexagonal Architecture Reference — Python Projects

> This document defines the hexagonal (ports & adapters) architecture pattern
> as implemented in Inditex Python services. It serves as the canonical
> reference for the `scaffold_project` MCP tool and for any developer
> building or extending a hexagonal project.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Directory Structure](#directory-structure)
- [Layer Specifications](#layer-specifications)
  - [Domain Layer](#domain-layer)
  - [Application Layer](#application-layer)
  - [Infrastructure Layer](#infrastructure-layer)
  - [REST Layer](#rest-layer)
- [Naming Conventions](#naming-conventions)
- [Dependency Rules](#dependency-rules)
- [Dependency Injection](#dependency-injection)
- [Test Structure](#test-structure)
- [Stack Variants](#stack-variants)
- [Code Patterns](#code-patterns)

---

## Architecture Overview

```
                       ┌─────────────────────────────┐
                       │        REST / HTTP           │
                       │    (FastAPI routes/DTOs)      │
                       └──────────┬──────────────────┘
                                  │
                       ┌──────────▼──────────────────┐
                       │    Infrastructure Layer       │
                       │  Controllers • REST Impl      │
                       └──────────┬──────────────────┘
                                  │
                       ┌──────────▼──────────────────┐
                       │     Application Layer         │
                       │   Use Cases • Mappers (DTO)   │
                       └──────────┬──────────────────┘
                                  │
              ┌───────────────────▼───────────────────────┐
              │              Domain Layer                  │
              │  Models • Services • Repository Ports      │
              │         (pure business logic)              │
              └───────────────────┬───────────────────────┘
                                  │ (port interface)
              ┌───────────────────▼───────────────────────┐
              │          Infrastructure Layer              │
              │  Repository Adapters • ORM Entities        │
              │   Mappers (Domain↔Entity) • DI Modules     │
              └───────────────────────────────────────────┘
```

**Request flow:**

```
HTTP Request
  → REST Route (FastAPI)
    → REST Implementation (extends generated/base API)
      → Controller (infrastructure)
        → Use Case (application)
          → Domain Service (domain)
            → Repository Port (domain, ABC)
              → Repository Adapter (infrastructure, implements port)
                → Database Repository (infrastructure, raw SQL/ORM)
                  → ORM Entity (infrastructure)
```

---

## Directory Structure

All source code lives under a `code/` directory. The main package is named
after the project (e.g., `carmen/`, `sugus/`, `boman/`).

```
<project_root>/
├── code/
│   ├── pyproject.toml
│   ├── uv.lock
│   │
│   ├── <project_name>/                    # Main application package
│   │   ├── __init__.py                    # Entry point (startup, DI registration)
│   │   ├── __main__.py                    # Server launch
│   │   │
│   │   ├── domain/                        # ── DOMAIN LAYER ──
│   │   │   ├── __init__.py
│   │   │   ├── model/                     # Pure domain models
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>.py            # @dataclass <Entity>
│   │   │   ├── repository/                # Repository ports (ABC interfaces)
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_repository_port.py
│   │   │   ├── port/                      # Cross-domain ports (optional)
│   │   │   │   └── <context>_<action>_port.py
│   │   │   ├── service/                   # Domain services (business logic)
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_domain_service.py
│   │   │   └── exception/                 # Domain exceptions
│   │   │       ├── __init__.py
│   │   │       └── domain_exceptions.py
│   │   │
│   │   ├── application/                   # ── APPLICATION LAYER ──
│   │   │   ├── __init__.py
│   │   │   ├── mapper/                    # DTO ↔ Domain mappers
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_mapper.py     # <Entity>ApplicationMapper
│   │   │   └── use_case/                  # Use cases grouped by entity
│   │   │       ├── __init__.py
│   │   │       └── <entity>/
│   │   │           ├── __init__.py
│   │   │           ├── create_<entity>_use_case.py
│   │   │           ├── get_<entity>_use_case.py
│   │   │           ├── update_<entity>_use_case.py
│   │   │           ├── delete_<entity>_use_case.py
│   │   │           └── search_<entities>_use_case.py
│   │   │
│   │   ├── infrastructure/                # ── INFRASTRUCTURE LAYER ──
│   │   │   ├── __init__.py
│   │   │   ├── di/                        # Dependency injection modules
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_module.py
│   │   │   ├── controller/                # Hexagonal controllers
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_controller.py
│   │   │   ├── mapper/                    # Domain ↔ Entity mappers
│   │   │   │   ├── __init__.py
│   │   │   │   └── <entity>_domain_mapper.py
│   │   │   └── repository/                # Repository adapters & ORM
│   │   │       ├── __init__.py
│   │   │       ├── <entity>_repository.py          # Adapter (implements port)
│   │   │       ├── model/                          # ORM entities
│   │   │       │   ├── __init__.py
│   │   │       │   ├── base.py                     # SQLAlchemy DeclarativeBase
│   │   │       │   └── <entity>/
│   │   │       │       ├── __init__.py
│   │   │       │       └── <entity>_entity.py      # SQLAlchemy model
│   │   │       └── database/                       # Raw database repositories
│   │   │           ├── __init__.py
│   │   │           ├── factory.py                  # DatabaseFactory (session mgmt)
│   │   │           ├── read_only_database_repository.py
│   │   │           ├── read_write_database_repository.py
│   │   │           └── <entity>/
│   │   │               ├── __init__.py
│   │   │               └── <entity>_database_repository.py
│   │   │
│   │   ├── rest_impl/                     # REST API implementations
│   │   │   ├── __init__.py
│   │   │   └── <entity>_api_impl.py
│   │   │
│   │   └── exception/                     # Shared exceptions
│   │       └── __init__.py                # NotFoundException, ConflictException, ...
│   │
│   ├── <project_name>_rest_server/        # Generated REST server (optional)
│   │   ├── main.py
│   │   ├── apis/
│   │   └── dto/
│   │
│   └── tests/                             # ── TEST SUITE ──
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       │   └── <project_name>/
│       │       ├── domain/
│       │       │   ├── model/
│       │       │   ├── service/
│       │       │   └── repository/
│       │       ├── application/
│       │       │   ├── mapper/
│       │       │   └── use_case/<entity>/
│       │       └── infrastructure/
│       │           ├── mapper/
│       │           ├── repository/
│       │           ├── controller/
│       │           └── di/
│       └── integration/
│           └── <project_name>/
│               └── infrastructure/
│                   └── repository/
```

---

## Layer Specifications

### Domain Layer

The **heart** of the application. Pure business logic, zero framework dependencies.

#### Domain Models

Pure Python `@dataclass` classes. No ORM annotations, no Pydantic.

```python
# <project>/domain/model/<entity>.py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Catalog:
    """Domain model representing a security catalog."""

    catalog_id: Optional[int] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    version: Optional[str] = None
    total_controls: int = 0

    def validate(self) -> None:
        """Validate business rules."""
        if not self.title or not self.title.strip():
            raise ValueError("Catalog title must not be empty")
```

**Rules:**
- All fields `Optional` by default (supports PATCH operations)
- IDs are `Optional[int]` (not set before persistence)
- Include `validate()` for business rules
- Include behavioral methods (`is_active()`, `deactivate()`)
- Use `@dataclass`, not Pydantic — domain must be framework-free

#### Enums

```python
from enum import Enum

class ComponentType(str, Enum):
    SOFTWARE = "SOFTWARE"
    HARDWARE = "HARDWARE"
    SERVICE = "SERVICE"

    @classmethod
    def from_string(cls, value: str) -> "ComponentType":
        try:
            return cls(value.upper())
        except ValueError as exc:
            raise ValueError(f"Invalid ComponentType: {value}") from exc
```

#### Repository Ports (Interfaces)

Abstract Base Classes in `domain/repository/`. These define the **contract** —
the domain says *what* it needs, infrastructure provides *how*.

```python
# <project>/domain/repository/<entity>_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from <project>.domain.model.<entity> import <Entity>


class <Entity>RepositoryPort(ABC):
    """Port for <Entity> persistence operations."""

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[<Entity>]:
        ...

    @abstractmethod
    async def search(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[<Entity>], int]:
        ...

    @abstractmethod
    async def create(
        self, db: AsyncSession, entity: <Entity>, *, auto_commit: bool = True
    ) -> <Entity>:
        ...

    @abstractmethod
    async def update(
        self, db: AsyncSession, entity: <Entity>, *, auto_commit: bool = True
    ) -> <Entity>:
        ...

    @abstractmethod
    async def delete(
        self, db: AsyncSession, entity_id: int, *, auto_commit: bool = True
    ) -> None:
        ...
```

**Key pattern:** All methods receive `AsyncSession` as first arg after `self`.

#### Domain Services

Orchestrate business logic using repository ports. Constructor-injected dependencies.

```python
# <project>/domain/service/<entity>_domain_service.py
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from <project>.domain.model.<entity> import <Entity>
from <project>.domain.repository.<entity>_repository_port import <Entity>RepositoryPort
from <project>.domain.exception.domain_exceptions import DomainNotFoundException

logger = logging.getLogger(__name__)


class <Entity>DomainService:
    """Domain service for <Entity> business logic."""

    def __init__(self, repository: <Entity>RepositoryPort) -> None:
        self._repository = repository

    async def get(self, db: AsyncSession, entity_id: int) -> <Entity>:
        result = await self._repository.get_by_id(db, entity_id)
        if result is None:
            raise DomainNotFoundException(f"<Entity> with id {entity_id} not found")
        return result

    async def create(self, db: AsyncSession, entity: <Entity>) -> <Entity>:
        entity.validate()
        return await self._repository.create(db, entity)
```

**Rules:**
- Accept `AsyncSession` as parameter (do NOT create sessions)
- Use repository ports via constructor injection
- Validate first → check constraints → set metadata → persist
- Raise domain exceptions, never HTTP exceptions

#### Domain Exceptions

```python
# <project>/domain/exception/domain_exceptions.py

class DomainException(Exception):
    """Base exception for domain layer."""

class DomainNotFoundException(DomainException):
    """Raised when a domain entity is not found."""

class DomainEntityAlreadyExistsException(DomainException):
    """Raised when attempting to create a duplicate entity."""

class DomainValidationException(DomainException):
    """Raised when domain validation fails."""
```

---

### Application Layer

Orchestrates data flow between REST controllers and the domain layer.
Thin coordinators — no business logic.

#### Use Cases

One class per operation, with a single `execute()` method.

```python
# <project>/application/use_case/<entity>/get_<entity>_use_case.py
from sqlalchemy.ext.asyncio import AsyncSession

from <project>.domain.model.<entity> import <Entity>
from <project>.domain.service.<entity>_domain_service import <Entity>DomainService


class Get<Entity>UseCase:
    """Retrieve a single <Entity> by ID."""

    def __init__(self, service: <Entity>DomainService) -> None:
        self._service = service

    async def execute(self, db: AsyncSession, entity_id: int) -> <Entity>:
        return await self._service.get(db, entity_id)
```

**Naming pattern:** `<Verb><Entity>UseCase`
- `Create<Entity>UseCase`, `Get<Entity>UseCase`, `Update<Entity>UseCase`
- `Delete<Entity>UseCase`, `Search<Entities>UseCase`

#### Application Mappers

Stateless `@staticmethod` methods. Map between REST DTOs and domain models.

```python
# <project>/application/mapper/<entity>_mapper.py
from <project>.domain.model.<entity> import <Entity>


class <Entity>ApplicationMapper:
    """Maps between REST DTOs and <Entity> domain model."""

    @staticmethod
    def to_domain(dto: "<Entity>Request") -> <Entity>:
        return <Entity>(
            title=dto.title,
            description=dto.description,
        )

    @staticmethod
    def to_response(entity: <Entity>) -> "<Entity>Response":
        return <Entity>Response(
            entityId=entity.entity_id,      # snake_case → camelCase
            title=entity.title or "",
        )

    @staticmethod
    def to_response_list(entities: list[<Entity>]) -> list["<Entity>Response"]:
        return [<Entity>ApplicationMapper.to_response(e) for e in entities]
```

**Rules:**
- All methods are `@staticmethod`
- Handle `snake_case` (domain) ↔ `camelCase` (DTO) conversion
- Never access infrastructure layer directly

---

### Infrastructure Layer

Handles all external concerns: database persistence, external APIs, framework glue.

#### ORM Entities (SQLAlchemy 2.0)

```python
# <project>/infrastructure/repository/model/base.py
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy ORM entities."""
    pass
```

```python
# <project>/infrastructure/repository/model/<entity>/<entity>_entity.py
from sqlalchemy import Column, Integer, String
from <project>.infrastructure.repository.model.base import Base


class <Entity>Entity(Base):
    """ORM entity for the <entity> table."""

    __tablename__ = "<entity>"

    <entity>_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    description = Column(String(4096), nullable=True)
```

#### Infrastructure Mappers (Domain ↔ Entity)

```python
# <project>/infrastructure/mapper/<entity>_domain_mapper.py
from typing import Optional

from <project>.domain.model.<entity> import <Entity>
from <project>.infrastructure.repository.model.<entity>.<entity>_entity import <Entity>Entity


class <Entity>DomainMapper:
    """Maps between <Entity> domain model and ORM entity."""

    @staticmethod
    def to_domain(entity: Optional[<Entity>Entity]) -> Optional[<Entity>]:
        if entity is None:
            return None
        return <Entity>(
            <entity>_id=entity.<entity>_id,
            title=entity.title,
            description=entity.description,
        )

    @staticmethod
    def to_entity(domain: <Entity>) -> <Entity>Entity:
        return <Entity>Entity(
            <entity>_id=domain.<entity>_id,
            title=domain.title,
            description=domain.description,
        )

    @staticmethod
    def to_domain_list(entities: list[<Entity>Entity]) -> list[<Entity>]:
        return [<Entity>DomainMapper.to_domain(e) for e in entities if e is not None]
```

#### Repository Adapters

Implement domain ports. Compose database repositories.

```python
# <project>/infrastructure/repository/<entity>_repository.py
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from <project>.domain.model.<entity> import <Entity>
from <project>.domain.repository.<entity>_repository_port import <Entity>RepositoryPort
from <project>.infrastructure.mapper.<entity>_domain_mapper import <Entity>DomainMapper
from <project>.infrastructure.repository.database.<entity>.<entity>_database_repository import (
    <Entity>DatabaseRepository,
)


class <Entity>Repository(<Entity>RepositoryPort):
    """Adapter implementing <Entity>RepositoryPort with SQLAlchemy."""

    def __init__(self, db_repo: <Entity>DatabaseRepository) -> None:
        self._db_repo = db_repo

    async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[<Entity>]:
        entity = await self._db_repo.get_by_id(db, entity_id)
        return <Entity>DomainMapper.to_domain(entity)

    async def create(
        self, db: AsyncSession, domain: <Entity>, *, auto_commit: bool = True
    ) -> <Entity>:
        orm_entity = <Entity>DomainMapper.to_entity(domain)
        created = await self._db_repo.create(db, orm_entity, auto_commit=auto_commit)
        return <Entity>DomainMapper.to_domain(created)
```

#### Controllers

Glue between REST layer and use cases. Inject use cases, call application mappers.

```python
# <project>/infrastructure/controller/<entity>_controller.py
from sqlalchemy.ext.asyncio import AsyncSession

from <project>.application.mapper.<entity>_mapper import <Entity>ApplicationMapper
from <project>.application.use_case.<entity>.get_<entity>_use_case import Get<Entity>UseCase
from <project>.application.use_case.<entity>.create_<entity>_use_case import Create<Entity>UseCase


class <Entity>Controller:
    """Hexagonal controller for <Entity> operations."""

    def __init__(
        self,
        get_use_case: Get<Entity>UseCase,
        create_use_case: Create<Entity>UseCase,
    ) -> None:
        self._get_use_case = get_use_case
        self._create_use_case = create_use_case

    async def get(self, db: AsyncSession, entity_id: int):
        entity = await self._get_use_case.execute(db, entity_id)
        return <Entity>ApplicationMapper.to_response(entity)

    async def create(self, db: AsyncSession, request):
        domain = <Entity>ApplicationMapper.to_domain(request)
        created = await self._create_use_case.execute(db, domain)
        return <Entity>ApplicationMapper.to_response(created)
```

#### DI Modules

```python
# <project>/infrastructure/di/<entity>_module.py
from opyoid import Module

from <project>.domain.repository.<entity>_repository_port import <Entity>RepositoryPort
from <project>.domain.service.<entity>_domain_service import <Entity>DomainService
from <project>.infrastructure.repository.<entity>_repository import <Entity>Repository
from <project>.infrastructure.controller.<entity>_controller import <Entity>Controller
from <project>.application.use_case.<entity>.get_<entity>_use_case import Get<Entity>UseCase
from <project>.application.use_case.<entity>.create_<entity>_use_case import Create<Entity>UseCase


class <Entity>Module(Module):
    """DI module binding <Entity> components."""

    def configure(self) -> None:
        # Port → Adapter
        self.bind(<Entity>RepositoryPort, to_class=<Entity>Repository)

        # Domain services
        self.bind(<Entity>DomainService)

        # Use cases
        self.bind(Get<Entity>UseCase)
        self.bind(Create<Entity>UseCase)

        # Controller
        self.bind(<Entity>Controller)
```

---

### REST Layer

Extends generated (or manually written) base API classes. Delegates to controllers.

```python
# <project>/rest_impl/<entity>_api_impl.py
from fastapi import Request

from <project>.infrastructure.controller.<entity>_controller import <Entity>Controller


class <Entity>ApiImpl:
    """REST implementation for <Entity> endpoints."""

    def __init__(self, controller: <Entity>Controller) -> None:
        self._controller = controller

    async def get_entity(self, request: Request, entity_id: int):
        db = request.state.db
        return await self._controller.get(db, entity_id)
```

---

## Naming Conventions

| Artifact | Class Name | File Name |
|----------|------------|-----------|
| Domain Model | `<Entity>` | `<entity>.py` |
| Domain Enum | `<Entity>Type` | `<entity>.py` or `<entity>_type.py` |
| Repository Port | `<Entity>RepositoryPort` | `<entity>_repository_port.py` |
| Cross-Domain Port | `<Context><Action>Port` | `<context>_<action>_port.py` |
| Domain Service | `<Entity>DomainService` | `<entity>_domain_service.py` |
| Use Case | `<Verb><Entity>UseCase` | `<verb>_<entity>_use_case.py` |
| Application Mapper | `<Entity>ApplicationMapper` | `<entity>_mapper.py` |
| Infrastructure Mapper | `<Entity>DomainMapper` | `<entity>_domain_mapper.py` |
| ORM Entity | `<Entity>Entity` | `<entity>_entity.py` |
| Repository Adapter | `<Entity>Repository` | `<entity>_repository.py` |
| Database Repository | `<Entity>DatabaseRepository` | `<entity>_database_repository.py` |
| Controller | `<Entity>Controller` | `<entity>_controller.py` |
| REST Implementation | `<Entity>ApiImpl` | `<entity>_api_impl.py` |
| DI Module | `<Entity>Module` | `<entity>_module.py` |
| Domain Exception | `Domain<Type>Exception` | `domain_exceptions.py` |

**File system conventions:**
- All files and directories: `snake_case`
- Entity directories under `use_case/`, `model/` (for sub-models): `<entity>/`
- Test files: `test_<source_file>.py`

---

## Dependency Rules

| Layer | Can Import | Cannot Import |
|-------|-----------|---------------|
| **Domain** | Domain models, domain exceptions, repository ports, `AsyncSession` | REST DTOs, ORM entities, infrastructure, application |
| **Application** | Domain models, domain services, REST DTOs, application exceptions | Infrastructure, ORM entities, repositories directly |
| **Infrastructure** | Domain models, domain ports, ORM entities, infra mappers, `AsyncSession` | REST DTOs, application use cases (except via controller) |
| **REST Impl** | Controllers, REST DTOs | Domain models, domain services, repositories |

**Critical rule:** Domain layer has ZERO outward dependencies. It only imports
from itself and the standard library (plus `AsyncSession` for type hints).

---

## Dependency Injection

### AMIGA Stack (opyoid)

```python
# <project>/__init__.py
from amiga.startup import AmigaStartup
from <project>.infrastructure.di import <Entity>Module, AnotherModule

@AmigaStartup(modules=[<Entity>Module, AnotherModule])
def main():
    from <project> import __main__
    __main__.main()
```

### Generic Stack (manual / dependency-injector)

```python
# <project>/__init__.py
from <project>.infrastructure.repository.database.factory import DatabaseFactory
from <project>.infrastructure.repository.<entity>_repository import <Entity>Repository
from <project>.domain.service.<entity>_domain_service import <Entity>DomainService
from <project>.application.use_case.<entity>.get_<entity>_use_case import Get<Entity>UseCase
from <project>.infrastructure.controller.<entity>_controller import <Entity>Controller

# Wire dependencies manually
db_factory = DatabaseFactory()
<entity>_repo = <Entity>Repository(<Entity>DatabaseRepository())
<entity>_service = <Entity>DomainService(repository=<entity>_repo)
get_<entity>_uc = Get<Entity>UseCase(service=<entity>_service)
<entity>_controller = <Entity>Controller(get_use_case=get_<entity>_uc)
```

---

## Test Structure

Tests **mirror** the source structure. Mock at boundaries.

```
tests/unit/<project>/
├── domain/
│   ├── model/              → test domain model validation & behavior
│   ├── service/            → test business logic (mock repository ports)
│   └── repository/         → test port contracts (optional)
├── application/
│   ├── mapper/             → test DTO↔domain mapping
│   └── use_case/<entity>/  → test use case orchestration (mock services)
└── infrastructure/
    ├── mapper/             → test domain↔entity mapping
    ├── repository/         → test adapter (mock database repos)
    ├── controller/         → test controller (mock use cases)
    └── di/                 → test DI module bindings
```

**Testing patterns:**
- `pytest` + `pytest-asyncio` + `unittest.mock`
- `AsyncMock` for async repository ports
- AAA pattern: Arrange → Act → Assert
- Mock at the boundary: services mock repos, use cases mock services, controllers mock use cases

---

## Stack Variants

| Aspect | AMIGA Stack | Generic Stack |
|--------|-------------|---------------|
| **Framework** | AMIGA Python + FastAPI | Vanilla FastAPI |
| **DI** | `opyoid.Module` + `@AmigaStartup` | Manual wiring or `dependency-injector` |
| **Database** | AMIGA `AmigaSQLBuilder` + `DatabaseFactory` | Vanilla SQLAlchemy async session |
| **Auth** | `@user_permissions_check` decorator | Custom middleware or FastAPI `Depends` |
| **Config** | `application.yml` (AMIGA metadata) | `.env` + `pydantic-settings` |
| **API Generation** | OpenAPI Generator → `*_rest_server/` | Manual FastAPI routes |
| **Dependencies** | `fwk-amigapython[rest-server,database-sql]` | `fastapi`, `sqlalchemy[asyncio]`, `uvicorn` |
| **Build** | `hatchling` | `hatchling` |
| **ORM Entity Base** | `Base(AsyncAttrs, DeclarativeBase)` | Same |
| **Session Management** | `DatabaseFactory.get_session()` | `async_sessionmaker` context manager |

---

## Code Patterns

### Shared Exception Hierarchy

```python
# <project>/exception/__init__.py

class NotFoundException(Exception):
    """HTTP 404 — requested resource not found."""

class ConflictException(Exception):
    """HTTP 409 — resource already exists or conflicts."""

class BadRequestException(Exception):
    """HTTP 400 — invalid input or parameters."""

class ForbiddenException(Exception):
    """HTTP 403 — insufficient permissions."""
```

### Database Factory (Generic Stack)

```python
# <project>/infrastructure/repository/database/factory.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class DatabaseFactory:
    """Manages async database sessions."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self):
        async with self._session_factory() as session:
            yield session
```

### Generic Base Database Repositories

```python
# Read-only base
class ReadOnlyDatabaseRepository(ABC, Generic[T]):
    @abstractmethod
    def get_entity_class(self) -> type[T]: ...
    @abstractmethod
    def get_id_field_name(self) -> str: ...

    async def get_by_id(self, db: AsyncSession, entity_id: int) -> Optional[T]:
        stmt = select(self.get_entity_class()).where(
            getattr(self.get_entity_class(), self.get_id_field_name()) == entity_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

# Read-write base (extends read-only)
class ReadWriteDatabaseRepository(ReadOnlyDatabaseRepository[T]):
    async def create(self, db: AsyncSession, entity: T, *, auto_commit: bool = True) -> T:
        db.add(entity)
        if auto_commit:
            await db.commit()
            await db.refresh(entity)
        return entity

    async def delete(self, db: AsyncSession, entity_id: int, *, auto_commit: bool = True) -> None:
        entity = await self.get_by_id(db, entity_id)
        if entity:
            await db.delete(entity)
            if auto_commit:
                await db.commit()
```

---

> **This document is the canonical reference for the `scaffold_project` MCP tool.**
> All generated projects MUST follow the patterns defined here.
