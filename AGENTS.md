# Repository development

Read the README, WORKFLOW.md and current validation record before changing the app.
For a new website, new app interface or substantial visual redesign (including
“build me a beautiful website”), use the repository's
[reference-design skill](.agents/skills/reference-design/SKILL.md) and
[setup guide](docs/DESIGN_WORKFLOW.md). Complete requirements, visual references,
implementation and real desktop/mobile checks; ordinary backend fixes skip this.
Develop on dev or an explicit feature branch targeting dev. Preserve the configured
release policy; merging into main and publishing/deploying require release authorization.
An authorization already given for the current task remains effective.

Use [Graft](docs/GRAFT.md) for whole-repository discovery: application source,
Dockerfiles, Compose, CI, deployment scripts, configuration and documentation.
Use its bounded text search/read or direct source reads where graph coverage is absent.
Inspect status for the actual repository, branch, revision and excluded/untracked paths.
Do not treat graph results as proof that a behavior works or as authority to deploy.

For browser behavior, follow [runtime verification](docs/RUNTIME-VERIFICATION.md).
Keep Reticle available but use it only when requested for the task; do not ask every
time. A full pass with Reticle combines normal suites and selected browser flows.
Keep required tests and direct desktop/mobile inspection regardless. When Reticle
is selected, verify a connected session before claiming observations.
Record genuine failures and unknown observations; a missing connection is not a pass.
Keep context caches, runtime recordings, credentials and developer tooling out of
production images. Separate local, container, CI and live evidence in the validation record.
