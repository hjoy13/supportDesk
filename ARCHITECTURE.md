# Architecture & Design Decisions — SupportDesk API

This document covers how the system is structured, the business rules it enforces, and the reasoning behind the more interesting engineering decisions. It's written both as project documentation and as interview prep material.

## Request flow

```text
Client
  ↓
/api/v1/
  ↓
Router
  ↓
ViewSet
  ↓
Queryset visibility / permissions / business rules
  ↓
Serializer
  ↓
Django ORM
  ↓
PostgreSQL
```

Architecture style: modular monolith — deliberately, not a missing feature. This project's scope doesn't justify microservices, and adding that complexity would obscure rather than demonstrate engineering judgment.

## Core design principle: security is not just serializer-level

A common mistake in DRF projects is treating the serializer as the only place permissions matter. This project enforces access control at every layer independently:

```text
queryset visibility     — what rows can this user even see?
+ object/resource visibility  — get_object_or_404 scoping to hide existence
+ input validation       — what fields can this role set on create/update?
+ update permissions      — what fields can this role change, and when?
+ output visibility       — what fields does this role see in the response?
```

No single layer is trusted to do all the work. For example, a customer's priority restriction is enforced independently at creation (reject explicit `priority` in the request), at update (locked after assignment for everyone), at output (`to_representation()` strips the field), and at query time (filtering/ordering by `priority` blocked for customers).

## Core models

**User** (`apps/accounts`) — custom `AbstractUser` with a `role` field (`CUSTOMER` / `AGENT`), kept deliberately separate from Django's built-in `is_staff`/`is_superuser`, which govern Django admin access, not application-level business roles.

**Ticket** — `title`, `description`, `status`, `priority`, `created_by` (`PROTECT`), `assigned_to` (`SET_NULL`), timestamps.

**TicketMessage** — `ticket`, `author`, `text`, `created_at`. Immutable through the public API — no edit or delete endpoints exist for messages, preserving conversation history as a permanent record.

## Business rules

### Ticket creation
- Customers create tickets; agents cannot (`POST` by an agent → 403).
- `created_by` always comes from `request.user`, never the client.
- If a customer explicitly sends `priority`, `status`, or `assigned_to`, the request is **rejected**, not silently ignored — silently dropping fields the client explicitly sent would hide a misunderstanding from the client instead of surfacing it.
- Omitted fields fall back to model defaults: `status=open`, `priority=medium`, `assigned_to=null`.

### Visibility
- Customers see only tickets they created.
- Agents see unassigned tickets **or** tickets assigned to themselves — never another agent's claimed tickets.
- Conceptually: `Q(assigned_to__isnull=True) | Q(assigned_to=request.user)`.

### Priority
- Completely hidden from customers — not in create input, not in update input, not in filtering, not in ordering, not in the response body.
- Visible to agents only within their own visible queryset.
- Locked for everyone (including the assigned agent) once a ticket is assigned — priority decisions happen while triaging unclaimed work, not after ownership is established.
- Priority ordering (`?ordering=priority`) uses **business-severity rank**, not alphabetical string order:
  ```text
  low = 1, medium = 2, high = 3, urgent = 4
  ```
  Implemented via a queryset annotation (`Case`/`When`/`Value`) mapped to a custom `BusinessOrderingFilter`, so `priority_rank` requires no database column or migration.

### Assignment
- An agent may claim a ticket only while it's unassigned, and only onto themselves — no assigning to another agent, no reassignment once claimed.
- Assignment is the ownership boundary that several other rules (status changes, priority locking) key off of.

### Status
- Only the currently assigned agent may change status.
- An unassigned ticket's status can't be changed until an agent claims it.
- Transitions between `open` / `in_progress` / `resolved` / `closed` are currently free-form — no enforced state machine (see Out of Scope).

### Title / description
- Customers can edit these only while the ticket is unassigned — once claimed, the original issue is locked, and further information goes through messages instead.
- Agents can never modify title/description, at any point.

### Messages
- Customers can read/post on their own ticket's conversation at any time, including after assignment.
- Agents can read/post only on tickets assigned to themselves; an unassigned ticket returns 403 on the messages endpoint (the agent can see the ticket exists, just not its conversation).
- A ticket belonging to another customer, or assigned to another agent, returns **404** via scoped `get_object_or_404()` lookups — this avoids leaking the existence of a resource the caller shouldn't know about.

### Existence-hiding principle
404 vs 403 is a deliberate distinction throughout the API, not an accident of DRF defaults:
- **404** — the resource is completely outside the caller's universe; its existence itself is not confirmed.
- **403** — the caller is allowed to know the resource exists, just not to act on it (e.g., an agent can see an unassigned ticket exists, but can't read its messages until claiming it).

## Design decisions worth discussing

### Unified error envelope
DRF's default error shapes disagree: field validation errors return `{"field": ["msg"]}`, while permission/auth/not-found errors return `{"detail": "..."}`. A single API consumer would need to branch on status code just to know which shape to expect.

**Decision:** normalize everything into one envelope via a custom `EXCEPTION_HANDLER`:
```json
// 403 / 404 / 401 — unchanged
{"detail": "Customers cannot modify this field."}

// 400 — normalized
{"detail": "Validation failed.", "errors": {"title": ["This field may not be blank."]}}
```
The `errors` key is **omitted entirely** (not `null`, not `{}`) when there's no field-level detail — following Stripe/GitHub convention, where key *presence* is itself the signal a consumer checks for, avoiding per-status-code special-casing.

### AI-suggested replies — ephemeral by design
`POST /api/v1/tickets/{id}/suggest-reply/` — agent-assigned-only, generates a draft reply via Gemini, built from the ticket's title, description, and full ordered message thread.

**Decision:** the suggestion is **never persisted** — no new model, response is `{"suggested_reply": "..."}` and nothing more. Reasoning: persisting AI drafts raises questions (are they audit-logged? editable? shown to customers?) that are out of scope for what this feature is meant to demonstrate — an on-demand drafting aid, not an audit trail. The prompt explicitly forbids the model from deciding or mentioning status, priority, or assignment, keeping AI influence scoped to reply text only, not business state.

Gemini failures are wrapped in a custom `SuggestionServiceUnavailable(APIException)` → 503, flowing through the same unified exception handler as every other error, with no special-casing needed.

### Swagger/OpenAPI's static-schema limitation
`drf-spectacular` performs **static** introspection of serializer classes — it never executes a request, so it can't represent runtime, per-request logic like `TicketSerializer.to_representation()` stripping `priority` for customers.

This was verified directly: Swagger's example schema always lists `priority` (the field exists on the serializer class), but a real `GET /tickets/` executed as a customer — confirmed via `curl`, not just the Swagger UI's own "Try it out" — correctly omits it. This is a known, industry-wide limitation of OpenAPI's static schema model, not a bug. Common mitigations (accept + document, split serializers per role, manual `@extend_schema` annotations) were considered; **accept + document** was chosen as appropriate for this project's scope.

### `requirements.txt` convention
Lists only directly-installed packages, not the full output of `pip freeze`. `pip freeze` captures every transitive sub-dependency pinned to whatever version happened to be resolved at install time — versions nobody explicitly chose, bloating the file and making future upgrades harder to reason about. Pip resolves sub-dependencies automatically from each package's own metadata at install time, so only direct dependencies need to be listed.

## Known limitations / out of scope

- **No enforced status state machine** — transitions between `open`/`in_progress`/`resolved`/`closed` are currently free-form (e.g., `closed → open` is technically allowed). A stricter transition graph is a reasonable extension, deferred to keep the initial rule set legible.
- **Concurrency** — two agents claiming the same ticket, or changing priority, at nearly the same time currently resolves via last-write-wins. A stronger solution would use database transactions and/or `select_for_update()`. Deferred as out of scope for current project size.
- **No manager/lead role**, no agent auto-assignment or load balancing, no agent-to-agent ticket recommendation.
- **No microservices** — deliberate; a modular monolith is the right scope for this project's size.

## Testing approach

34 tests across ticket visibility, creation, updates, messages, blank-field validation, and AI-suggested-reply access control — organized as one file per concern rather than one giant test file, so failures are easy to localize.

The AI-suggested-reply tests mock at the **import site in the calling module** (`apps.tickets.views.get_suggested_reply`), not deep inside the Gemini client — this keeps the tests coupled to view-layer access control (who can call this, under what conditions) rather than to prompt-building internals, and keeps the suite hermetic (no real network calls, no dependency on a live API key to pass).
