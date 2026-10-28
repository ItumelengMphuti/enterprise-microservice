# Event Ticketing API

A Django REST Framework service for venues, seats, events, event seat offerings,
and ticket reservations. It uses PostgreSQL and runs locally with Docker Compose.
An event and its seats have a many-to-many relationship through `EventSeat`,
which stores each ticket's price.

## Requirements

- Docker Desktop with Docker Compose
- PowerShell on Windows (the examples below use `curl.exe`)

## Run locally

1. From the repository root, create `event-ticketing-api/.env`. Compose needs
   the three PostgreSQL values to start the database. For local development,
   the file can contain:

   ```dotenv
   POSTGRES_DB=event_ticketing
   POSTGRES_USER=ticketing
   POSTGRES_PASSWORD=change-this-local-password
   DJANGO_SECRET_KEY=change-this-local-development-key
   DJANGO_DEBUG=False
   ```

   Keep real credentials out of source control. The Compose configuration
   supplies the API container's database host and port.

2. Start the API and PostgreSQL from the repository root:

   ```powershell
   cd event-ticketing-api
   docker compose up --build -d
   ```

3. Apply database migrations and create an administrator account:

   ```powershell
   docker compose exec api python manage.py migrate
   docker compose exec api python manage.py createsuperuser
   ```

4. Check that the API can reach PostgreSQL:

   ```powershell
   curl.exe -i http://localhost:8000/health/
   ```

   The API is available at `http://localhost:8000`. Swagger UI is at
   `http://localhost:8000/api/docs/`, and the OpenAPI schema is at
   `http://localhost:8000/api/schema/`.

To stop the services while retaining the PostgreSQL data volume:

```powershell
docker compose down
```

## API routes and access

| Route | Purpose | Access |
|---|---|---|
| `/api/venues/` | List, retrieve, and manage venues | Reads are public; writes require staff |
| `/api/seats/` | List, retrieve, and manage venue seats | Reads are public; writes require staff |
| `/api/events/` | List, retrieve, and manage events | Reads are public; writes require staff |
| `/api/event-seats/` | List, retrieve, and manage event seat offerings | Reads are public; writes require staff |
| `/api/reservations/` | List and create reservations | Authentication required |
| `/api/reservations/{id}/cancel/` | Cancel a reservation | Authentication required; users can access their own reservations |
| `/api/token/` | Obtain a JWT access/refresh token pair | Public |
| `/api/token/refresh/` | Obtain a new access token | Public |
| `/health/` and `/api/health/` | Check service status, uptime, and database connectivity | Public |

Reservation creation assigns the reservation to the authenticated user and
starts it in `PENDING` status. The `user` and `status` fields in a reservation
request are read-only. A seat with an existing pending or confirmed reservation
cannot be reserved again.

## cURL examples (PowerShell)

Run these commands in the same PowerShell session after starting Compose.
Create the administrator account using `createsuperuser` as described above.

Set the API base URL, then request an access token:

```powershell
$api = "http://localhost:8000"
$tokenResponse = curl.exe -sS -X POST "$api/api/token/" -H "Content-Type: application/json" --data-raw '{"username":"admin","password":"your-admin-password"}' | ConvertFrom-Json
$token = $tokenResponse.access
```

Browse public resources:

```powershell
curl.exe -sS "$api/api/events/"
curl.exe -sS "$api/api/venues/"
curl.exe -sS "$api/api/event-seats/"
```

As an administrator, create a venue, one of its seats, an event at that venue,
and the event's seat offering. The response IDs are used to link each resource:

```powershell
$venueBody = @{ name = "Example Arena"; address = "1 Main Street"; city = "Johannesburg" } | ConvertTo-Json -Compress
$venue = curl.exe -sS -X POST "$api/api/venues/" -H "Authorization: Bearer $token" -H "Content-Type: application/json" --data-raw $venueBody | ConvertFrom-Json

$seatBody = @{ venue = $venue.id; row_label = "A"; seat_number = 1 } | ConvertTo-Json -Compress
$seat = curl.exe -sS -X POST "$api/api/seats/" -H "Authorization: Bearer $token" -H "Content-Type: application/json" --data-raw $seatBody | ConvertFrom-Json

$startTime = (Get-Date).ToUniversalTime().AddDays(7).ToString("o")
$eventBody = @{ venue = $venue.id; title = "Example Concert"; description = "Local API demo"; start_time = $startTime; status = "SCHEDULED" } | ConvertTo-Json -Compress
$event = curl.exe -sS -X POST "$api/api/events/" -H "Authorization: Bearer $token" -H "Content-Type: application/json" --data-raw $eventBody | ConvertFrom-Json

$eventSeatBody = @{ event = $event.id; seat = $seat.id; price = "35.00" } | ConvertTo-Json -Compress
$eventSeat = curl.exe -sS -X POST "$api/api/event-seats/" -H "Authorization: Bearer $token" -H "Content-Type: application/json" --data-raw $eventSeatBody | ConvertFrom-Json
```

Create a reservation for that event seat. The authenticated administrator is
the reservation owner; for a customer reservation, obtain a token for that
customer instead:

```powershell
$reservationBody = @{ event_seat = $eventSeat.id } | ConvertTo-Json -Compress
curl.exe -i -sS -X POST "$api/api/reservations/" -H "Authorization: Bearer $token" -H "Content-Type: application/json" --data-raw $reservationBody
```

The API responds with `201 Created` for a successful reservation. A validation
error is returned if the seat is already reserved; a concurrent duplicate
reservation is rejected with `409 Conflict`.

Handled API errors use a consistent JSON envelope. For example, invalid input
returns a `400` response with the field-level validation details under `error`:

```json
{
  "error": {
    "code": "invalid",
    "message": "Request validation failed.",
    "details": {
      "event_seat": ["This seat has already been reserved for this event."]
    }
  }
}
```

The health endpoint includes `status`, database connectivity, a timestamp, and
process uptime in seconds; it returns `503` when the database check fails.

## Database indexes and constraints

Indexes are chosen to support the service's common lookups and ordering while
using uniqueness constraints to enforce important data rules in PostgreSQL.
The unique constraints also create database indexes.

| Model / index | Query or rule supported |
|---|---|
| `Event.start_time` (`event_start_time_idx`) | Events are ordered by `start_time`; the index supports ordered event listings and time-range lookups without scanning and sorting every event. |
| `Reservation(user, status)` (`reservation_user_status_idx`) | Customers' reservations are filtered by `user`; the composite index starts with `user` and also supports filtering those reservations by status. |
| `Seat(venue, row_label, seat_number)` (`uniq_seat_location`) | Prevents duplicate seat labels/numbers within one venue and supports finding seats for a venue in seat order. The venue-first order matches that access pattern. |
| `EventSeat(event, seat)` (`uniq_event_seat`) | Prevents offering the same seat twice for one event and supports looking up an event's seat offerings. |
| `Reservation(event_seat)` for `PENDING`/`CONFIRMED` rows (`uniq_active_res_eventseat`) | Prevents two active reservations for the same event seat, including concurrent requests. Cancelled reservations do not occupy the seat. |

Django also creates indexes for foreign-key fields by default, supporting
relationship joins and lookups such as a seat's venue or a reservation's event
seat. The explicit composite and partial indexes complement those defaults;
they are not intended as broad indexes on every column. Each additional index
uses storage and adds work to inserts and updates, so indexes should follow
real query patterns and be revisited as usage grows.

## Tests and CI

The GitHub Actions workflow at
[`event-ticketing-api/.github/workflows/ci.yml`](./event-ticketing-api/.github/workflows/ci.yml)
installs the development requirements, runs flake8, applies migrations to a
temporary PostgreSQL-backed CI database, runs the test suite, enforces at least
80% coverage for models, serializers, and API views, and builds the Docker
image.

To run the same checks locally from `event-ticketing-api/`, install the
development requirements and run:

```powershell
python -m pip install -r requirements-dev.txt
python -m flake8 config core events reservations manage.py --max-line-length=88 --extend-ignore=E203,W503 --extend-exclude='*/migrations/*'
python manage.py check
python manage.py migrate
python -m coverage run --source=venues,events,reservations,core manage.py test
python -m coverage report --include='*/views.py,*/models.py,*/serializers.py,core/exceptions.py' --fail-under=80
docker build --tag event-ticketing-api:local .
```
