# Red CLI Architecture Proposal

## Motivation

- Separate user interface concerns from business logic so the CLI stays thin and testable.
- Encapsulate Redmine HTTP details to make it easy to replace or mock during tests.
- Group domain concepts (issues, time entries, projects, sessions) together and provide reusable transformers.
- Create explicit seams for future features like automation, caching, or alternate front-ends (e.g., TUI, web).
- Establish a convention for tests, docs, and configuration so contributors can navigate quickly.

## Target Layout

```
src/red/
    cli/
        __init__.py
        app.py            # click (or typer) app factory
        main.py           # exposes "main" entry point
        commands/
            __init__.py
            auth.py
            issues.py
            overview.py
        presenters/
            __init__.py
            formatters.py # reusable rich/text rendering utilities
            tables.py
    application/
        __init__.py
        services/
            __init__.py
            auth_service.py
            issue_service.py
            overview_service.py
        dto/
            __init__.py
            overview.py
    domain/
        __init__.py
        models.py
        value_objects.py
        transformers.py
    infrastructure/
        __init__.py
        config/
            __init__.py
            repository.py    # read/write session data, env overrides, etc.
        redmine/
            __init__.py
            client.py        # wraps requests.Session
            mappers.py
        auth/
            __init__.py
            authenticator.py
    settings/
        __init__.py
        env.py              # load environment variables, defaults, constants

tests/
    cli/
    application/
    domain/
    infrastructure/
```

### Layer Responsibilities

- **CLI layer** – glue code tying click commands to application services. No HTTP or file IO aside from delegating to services.
- **Application layer** – orchestrates use-cases (login, fetch overview, list issues). Depends on domain and infrastructure contracts, not concrete implementations.
- **Domain layer** – pure dataclasses/value objects and transformation logic derived from API payloads. No framework imports.
- **Infrastructure layer** – concrete implementations for persistence (config file), HTTP clients, auth adapters. Exposes interfaces consumed by application layer.
- **Settings** – centralizes configuration loading to keep environment handling consistent.

## Supporting Practices

- Introduce typed DTOs for application responses so CLI commands render well-known structures (e.g., `OverviewSummary`, `IssueSnapshot`).
- Provide interface contracts (Protocols or ABCs) in `application.services` and have infrastructure register concrete implementations via simple factories.
- Use dependency injection helpers (simple factory functions) in `cli/app.py` to create a ready-to-use service container.
- Add unit tests per layer: domain (pure functions), application (service logic with fakes), CLI (click command runner), infrastructure (HTTP with responses).

## Migration Strategy

1. **Namespace prep** – move existing modules into the new directories without changing behavior; update imports and entry points.
2. **Service extraction** – convert procedural helpers in `overview.py`, `auth.py`, and `api.py` into application services with clear interfaces.
3. **Presenter separation** – migrate formatting routines from `cli.py` to `cli/presenters/formatters.py` so they can be reused (and later swapped with Rich/TUI presenters).
4. **Contract enforcement** – define protocols in `application` and refactor infrastructure to depend on them, enabling easier test doubles.
5. **Testing & CI** – add pytest scaffolding under the mirrored `tests/` tree with focused unit tests. Wire into an automated workflow later.
6. **Documentation** – maintain architecture decisions in `docs/` (including ADRs) as the structure evolves.

## Immediate Next Steps

- Create the folder skeletons (empty `__init__.py` files) and move existing modules gradually, adjusting imports.
- Add a small `ServiceRegistry` or factory in `cli/app.py` that wires up `RedmineClient`, `AuthService`, and `OverviewService`.
- Update `pyproject.toml` entry point to point to `red.cli.main:main` once the new CLI shell is in place.
- Draft ADR-001 documenting why the layered structure was chosen (clean separation, testability, future extensibility).

Once these steps are complete, future enhancements (e.g., caching, alternative UIs, background sync) can live in dedicated modules without further churn in the CLI entry points.
