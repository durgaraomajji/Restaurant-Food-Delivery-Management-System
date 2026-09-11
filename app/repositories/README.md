# Repository Layer

Repositories isolate common persistence operations from the API layer. The assignment routes use SQLAlchemy sessions directly for complex transactional queries, while these repositories provide reusable persistence primitives and demonstrate the intended Clean Architecture boundary. Complex domain workflows remain in `services/` and are transaction-safe.
