# GLOBAL GITHUB RESEARCH CORPUS POLICY

Status: binding RAE-8.8 source policy.

## Scope

Every repository accessible through the connected GitHub account is a potential research source for the project-wide Research Entity.

This includes, when accessible and relevant:
- repository files and documentation;
- branches and tags;
- commit history and diffs;
- issues and issue discussions;
- pull requests, reviews and review comments;
- releases;
- GitHub Actions workflow results, logs and artifacts;
- tests and benchmark outputs;
- repository metadata and dependency/configuration files.

The dedicated repository `gschaidergabriel/clay-global-research-entity` is different: it is the canonical STATE BACKEND. Its state files are projections/ledgers of evidence, not independent external evidence merely because they exist in Git.

## Evidence classes

Repository code / committed artifact: PRIMARY_IMPLEMENTATION_EVIDENCE

Executable test / CI result: EXECUTION_EVIDENCE

Commit diff: CHANGE_HISTORY_EVIDENCE

Issue / PR discussion: CLAIM_OR_ENGINEERING_CONTEXT unless backed by executable evidence

README / design document: DOCUMENTED_CLAIM unless independently tested

Generated Research-Entity summary: DERIVED_STATE, never raw evidence

## Retrieval

Do not load the whole account every session.
Maintain per-repository cursors: repo_id, default_branch, last_seen_commit, last_seen_issue_update, last_seen_pr_update, last_seen_workflow_run, last_census_at.

Boot:
1. load global corpus registry;
2. classify current system layer and research domain;
3. search only relevant repositories and cross-domain neighbours;
4. perform incremental scan from stored cursors;
5. promote only justified findings through the Global Promotion Gate.

## Cross-system architecture use

Repository evidence should be used not only for Synthetic Clay, but for any relevant part of the complete system: Linux host/runtime, cross-platform portability, storage, networking, security, model runtimes, agents, UI/tooling, deployment, observability, formal methods, FRANK/GWT, XENO/ClayCode and competing architectures.

## Safety / privacy

- Never copy credentials, tokens, private keys, passwords, cookies or secret values into the Research Entity.
- Secret-like material is metadata-only: record that a secret dependency exists, not its value.
- Private repository content remains private research material and must not be published merely because the Research Entity can read it.
- Repository access does not imply authority to change production code.
- Source repositories are read as evidence unless the user separately requests a write.

## Anti-contamination

A source stays scoped to its repository/domain until a typed transfer relation is justified.
Analogy is not replication.
Documentation is not runtime evidence.
CI passing is not proof of the larger scientific claim.

## Account-wide rule

`all_accessible_repositories = true`

This means eligible for research retrieval, not eagerly imported into every context.
