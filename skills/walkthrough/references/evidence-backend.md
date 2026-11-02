# Evidence: backend services

For web APIs, workers and services: the evidence is a real request travelling through the code, with what each layer received and returned.

## Run the service in isolation

- Prefer the framework's in-process test client: FastAPI / Starlette `TestClient`, Flask `app.test_client()`, Django `Client`, Express with `supertest`. No port, no network, and the same code path as production.
- Otherwise start the server on a scratch port with throwaway dependencies (docker containers for the database, cache and queue, see evidence-data.md) and drive it with `curl` or `httpx`.
- Configure it only through its own settings (environment variables, a test settings module). Use test users and generated data. Point nothing at production.

## Trace one request per chapter or step

For each endpoint the walkthrough teaches, capture in order:

1. The request: method, path, headers that matter (auth, content type), body. `OUT` the curl command and `KV` the parsed body.
2. Routing and validation: what the handler received after parsing (log or return the model object); the 4xx response for one invalid input.
3. The business logic: inputs and outputs of the service function, captured with `Runner` on the real function or by calling it directly.
4. Persistence: the SQL actually sent (enable the ORM's echo / query logging into a buffer) and the rows before and after, via `SELECT` on the scratch database. `T` blocks.
5. The response: status code, headers, JSON body.

Steps can follow the request across files: `ST(..., file="app/routes/users.py")`.

## Also capture

- Error paths: the exception, how the error handler shaped it, the status code the client saw.
- Auth: a request without credentials and with a valid test token.
- Background work: the message put on the queue and the worker's log line when it consumed it.
- Timing only when the text discusses performance, measured on the scratch setup and labelled as such.

## Code display

Pygments highlights any language (TypeScript, Go, SQL, YAML) as long as the project's Python has Pygments installed; the file extension picks the lexer.
