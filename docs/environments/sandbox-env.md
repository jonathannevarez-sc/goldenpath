# Sandbox environment

Use an **isolated GCP project** for testing Golden Path without touching production resources.

## Setup

1. Configure `config/enterprise.env` (copy from `config/enterprise.env.example`)
2. Set `GCP_SANDBOX_PROJECT` to a dedicated project ID
3. Set `PARENT_PROJECT_ID` and `BILLING_ACCOUNT_ID` for billing linkage
4. List production projects in `PROTECTED_PROJECTS`

## Stand up

**Script:**

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_GCP_SANDBOX_PROJECT

./scripts/standup-teardown-env.sh --yes
```

**Wizard:** `./scripts/goldenpath-setup-bash.sh` (or `-py.sh`, `-ui.sh`) → menu **3**

Creates the sandbox project (if needed), links billing, and runs `platform/bootstrap` Terraform.

## Teardown

Sandbox only — requires `personal_test = true` in `platform/bootstrap/terraform.tfvars`. Not used on the enterprise bootstrap-once path.

```bash
# Destroy bootstrap resources (WIF, AR, etc.) — GCP project remains
./scripts/teardown-personal-test.sh --yes

# Also delete the GCP project (irreversible)
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes
```

Projects in `PROTECTED_PROJECTS` are blocked on `--delete-project`.