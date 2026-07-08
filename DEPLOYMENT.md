# How I run this pattern in production

This repo is a clean-room reference. Its production sibling (a private multi-agent
platform I operate) runs on AWS, and this is the deployment discipline it follows.
The pattern matters more than the vendor.

## Release flow: health-gated deploys

1. **Every image is tagged by git SHA, never `:latest`.** A mutable tag overwrites
   your rollback target; a SHA tag means you can always point back to a known-good build.
2. **Images go to a registry (ECR), the box only pulls.** The running instance reads
   the image reference from a pointer file, so a deploy never rebuilds or replaces the machine.
3. **New image boots on a staging port first** and must pass a health check
   (`/api/health`) before it is allowed near live traffic.
4. **The previous image reference is saved before the swap.** Then the pointer flips,
   the service restarts, and live health is checked again.
5. **If live health fails, the deploy auto-rolls-back** to the saved reference.
   There is also a one-command manual rollback for everything else.

## Operating principles

- **Design for failure by default.** Every guardrail has an explicit fail-open or
  fail-closed decision, made per case: an AI-safety classifier fails OPEN (an outage
  must never block the core product; structural defenses carry the guarantee), while
  auth and money paths fail CLOSED.
- **Blast radius before features.** A connection-level fault holds a batch instead of
  burning per-item retries; a bad deploy affects the staging port, not users.
- **Structured logs with correlation IDs.** One request ID follows a task across API
  routes, background jobs, and webhooks, or 3am debugging is guesswork.
- **Spend caps on every user-triggerable model path.** LLM cost is a failure mode;
  a runaway loop should hit a circuit breaker, not a credit card.
- **Accumulating tables are read paginated.** Database clients silently cap result
  sets; an unbounded read that truncates is a correctness bug you find in production.

## What this repo carries of that

- A deterministic **offline mode**, so tests never depend on a network or a vendor.
- **CI runs the suite on every push** (see `.github/workflows/tests.yml`).
- A **Dockerfile** whose default command is the test suite: a container that proves
  itself healthy before you ship it anywhere.
- Secrets stay in the environment (`.env.example`), never in the image or the repo.
