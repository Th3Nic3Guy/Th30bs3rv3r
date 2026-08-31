# Infra

GCP infrastructure-as-code for the FREE WILL simulation platform. See
[`docs/adr/0001-gcp-tech-stack.md`](../docs/adr/0001-gcp-tech-stack.md) for the tech-stack
decision this implements, and `docs/FREE_WILL_PRD.md` Sections 6/9 for how each resource
is used.

## Layout

- `terraform/` — provisions Cloud SQL (PostgreSQL run registry), Memorystore Redis
  (config/cache), Cloud Storage (checkpoints + event-log archive), the Compute Engine
  instance template for simulation runs, Cloud Logging config, networking, and IAM
  service accounts.
- `sql/schema.sql` — DDL for the Cloud SQL `runs` / `run_summaries` / `checkpoints`
  tables. Apply after `terraform apply` creates the instance/database:

  ```sh
  psql "host=<cloudsql_connection_name via Cloud SQL Auth Proxy> dbname=freewill" -f sql/schema.sql
  ```
- `docker/gcs-data/` — bucket-seed directories for the local dev stack's GCS emulator
  (`fsouza/fake-gcs-server`, see `../docker-compose.yml` and `../docs/LOCAL_DEV.md`); not
  used by the real Terraform-provisioned infra at all.

**Don't have a GCP project yet?** `../docs/LOCAL_DEV.md` runs the same three storage
backends (Postgres, Redis, a GCS emulator) locally via `docker compose up`, no
credentials needed — useful for developing the engine/mechanism code without waiting on
this section.

## Bringing the stack up

```sh
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in project_id, run_instance_source_image
terraform init
terraform plan
terraform apply
```

`run_instance_source_image` must already exist — build it from `python/Dockerfile` +
`go/Dockerfile.logshipper` (PRD Milestone M0.5, `docs/FREE_WILL_PRD.md` Section 10)
before the first `apply`.
