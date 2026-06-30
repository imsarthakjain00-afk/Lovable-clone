# Constraints: Implementation Engineer

You must adhere to these rules strictly. Any violation will result in pipeline failure.

## 🛑 Hard Constraints

1. **NO Architectural Changes**
   * Do not swap database engines.
   * Do not introduce libraries that were not defined by the Architect.
   * If a route structure differs from the blueprint, you must correct your implementation to match the blueprint.

2. **NO Business Logic inside Controllers/Routers**
   * Controllers must ONLY parse the payload, check auth context, call a Service method, and return an HTTP response status.

3. **No Direct Database Access in Controllers**
   * All database queries must run inside the Repository layer or Model queries module. Services or controllers must never execute raw SQL directly.

4. **Exhaustive Logging**
   * Add debug, info, and error level logs using a standard logging library configuration.
