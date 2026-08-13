# agentforge-agent-schema

**Status:** Phase 0 — the versioned JSON Schema contract for agent YAML is complete. See `../agentforge-docs/docs/architecture/12-implementation-plan.md` for the overall roadmap.

## What this repo is

This repo holds the single source of truth for the structure of an AgentForge
agent definition: `agent.schema.json`, a [JSON Schema draft
2020-12](https://json-schema.org/draft/2020-12/schema) document that every
agent YAML file in the platform must validate against.

It is consumed as a **pinned git dependency** by three other repos:

- `agentforge-frontend` — loads the schema into the Monaco editor on the
  `/agents/new` and `/agents/:id` pages to provide inline validation and
  autocomplete while a developer authors agent YAML.
- `agentforge-control-plane` — runs the schema as the first stage of its
  YAML Validator, before its own semantic validation layer.
- `agentforge-agent-execution-platform` — validates agent definitions
  fetched from the registry before constructing a runtime graph from them.

Having one schema package, pinned by tag in each consumer, guarantees that
the frontend's live validation, the control plane's deploy-time validation,
and the execution platform's runtime validation can never silently drift
apart.

## The two-layer validation model

Agent YAML is validated in two distinct layers that deliberately do not
overlap:

1. **Structural validation (this repo).** `agent.schema.json` checks
   *shape*: required fields, types, string patterns, numeric ranges, enum
   membership, and `additionalProperties: false` to reject unknown keys.
   This layer has no knowledge of what exists in any database or registry —
   it can tell you that `tools[0].permission` must be one of `read`,
   `write`, or `execute`, but it cannot tell you whether `tool_id:
   kubernetes` is a tool that has actually been registered.

2. **Semantic validation (`agentforge-control-plane`).** The control
   plane's YAML Validator runs structural validation first (using this
   schema) and then performs checks that JSON Schema cannot express, such
   as: does this `tool_id` exist in the Tool Registry and is the requested
   `permission` allowed for it; does this `knowledge_base_id` exist; does
   `model.model_id` correspond to a model actually enabled for this
   provider; is `approval.checkpoints` non-empty only when
   `execution.mode: human_in_loop`; does the caller's role satisfy
   `permissions.policy_refs`. These checks require a database round-trip
   and business logic, so they live in control-plane, not in this schema.

Both layers must pass before an agent definition can be deployed.

## Consuming this schema

### From Python (`agentforge-control-plane`, `agentforge-agent-execution-platform`)

Add it as a pinned git dependency with [uv](https://docs.astral.sh/uv/):

```bash
uv add "git+https://github.com/<org>/agentforge-agent-schema@v1.0.0"
```

Load and validate with any draft-2020-12-capable validator, e.g.
[`jsonschema`](https://pypi.org/project/jsonschema/):

```python
import json
import yaml
from jsonschema import Draft202012Validator

schema = json.load(open("agent.schema.json"))
Draft202012Validator.check_schema(schema)
instance = yaml.safe_load(open("my-agent.yaml"))
Draft202012Validator(schema).validate(instance)
```

### From TypeScript (`agentforge-frontend`)

Add it as a pinned git dependency with [pnpm](https://pnpm.io/):

```bash
pnpm add "git+https://github.com/<org>/agentforge-agent-schema.git#v1.0.0"
```

Feed `agent.schema.json` to Monaco's YAML language service (e.g. via
`monaco-yaml`) to get inline diagnostics and autocomplete driven directly by
this schema.

## Versioning and cutting a new release

`schema_version` inside every agent YAML document (e.g. `"1.0.0"`) tracks
the version of `agent.schema.json` it was written against. The two must be
bumped together:

1. Edit `agent.schema.json`. Follow semver: additive, backward-compatible
   changes (a new optional field) are a minor bump; anything that could
   invalidate previously-valid documents (a new required field, a removed
   enum value, tightening a pattern) is a major bump.
2. Update the example files under `examples/` to reflect the new
   `schema_version`.
3. Commit the change.
4. Tag the commit: `git tag v1.1.0 && git push origin v1.1.0`.
5. Bump the pinned tag in each consuming repo's dependency declaration
   (`pyproject.toml` / `package.json`) in a follow-up PR there.

Consumers intentionally pin to an exact tag rather than a branch or `main`,
so a schema change never silently breaks a downstream repo's CI.

## A note on secrets

No credentials may ever appear in agent YAML. Fields like `tools[].params`
and `model.params` are for non-secret configuration only. Anything
requiring a secret (an API token, a database password) is referenced by
name — e.g. a `secret_ref` string that the execution platform resolves
against its secrets backend at runtime — never embedded as a literal value.
This is a convention enforced by control-plane's semantic validation layer,
not something `additionalProperties: false` alone can guarantee, since a
secret could technically be typed into any permitted string field. Treat
all agent YAML as safe to display in the frontend, log, and store in this
git-backed registry in plaintext.

## Full rationale

For the design rationale behind this schema's shape and the two-layer
validation split, see
[`../agentforge-docs/docs/architecture/07-agent-yaml-schema.md`](../agentforge-docs/docs/architecture/07-agent-yaml-schema.md).

## Layout

```
agent.schema.json                       # the schema itself
examples/minimal-agent.yaml             # smallest valid instance
examples/incident-investigator-agent.yaml  # full-featured instance
```
