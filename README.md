# cloudnotes-compute-network-lab

A local, ₹0, Docker-Compose-only lab that mimics a small GCP deployment
(Compute Engine VMs, VPC subnets, Cloud DNS, firewall rules, IAM policy)
for CloudNotes, a small notes app. **This repo intentionally ships with
three planted faults.** Your job is to find and fix them.

No GCP account, `gcloud`, Terraform, or billing is needed. Everything is
validated with `docker compose` and two stdlib-only Python scripts.

## Local stand-in → GCP concept mapping

| Local stand-in | Real GCP concept |
|---|---|
| `app` container (`docker-compose.yml`) | Compute Engine VM running the CloudNotes web app |
| `db` container (`docker-compose.yml`) | Compute Engine VM running the database |
| Custom Docker network `vpc-frontend` | Public-facing VPC subnet |
| Custom Docker network `vpc-backend` | Private VPC subnet (database tier) |
| Compose service-name resolution (e.g. `app` reaching `db` by name `db`) | Cloud DNS resolving internal names inside a VPC |
| `firewall.yaml` | GCP firewall rules (`name`, `direction`, `allowed`, `source_ranges`) |
| `iam-policy.json` | GCP IAM policy binding (`role`, `members`) |

## Intended working design

### Network / VPC / subnets / DNS
- `app` represents the CloudNotes web VM. It must serve frontend traffic
  **and** be able to reach the database VM, so it must be attached to
  **both** `vpc-frontend` and `vpc-backend`.
- `db` represents the database VM. It is private and must be attached to
  `vpc-backend` **only** — it should never be reachable from the public
  subnet directly.
- Service discovery works by Compose service name (Docker's embedded DNS),
  standing in for Cloud DNS: from inside `app`, the hostname `db` should
  resolve and be reachable, and vice versa where relevant.

### Firewall (`firewall.yaml`)
Modeled on GCP firewall rule fields (`name`, `direction`, `allowed`,
`source_ranges`). Intended shape:
- **HTTP/HTTPS (80, 443):** open to the world (`0.0.0.0/0`) — this is the
  public web tier.
- **SSH (22):** restricted to a trusted CIDR only (placeholder:
  `203.0.113.0/24`), **never** `0.0.0.0/0`.
- **DB port (5432):** never listed in any rule with a public
  (`0.0.0.0/0`) `source_ranges` — internal ranges only.

Validate with:
```bash
python3 security/validate_firewall.py firewall.yaml
```
This script fails (non-zero exit) if SSH or the DB port is open to
`0.0.0.0/0`, and passes otherwise. It's dependency-free: rather than
requiring PyYAML, it uses a small hand-rolled parser tailored to this
repo's flat `firewall.yaml` schema.

### IAM (`iam-policy.json`)
Modeled on a GCP IAM policy binding: `{ "bindings": [ { "role": ...,
"members": [...] } ] }`. The CloudNotes app service account
(`cloudnotes-app@...`) must be granted only the **narrowest role it
actually needs** (e.g. `roles/storage.objectViewer` or an app-specific
custom role) — **never** `roles/owner` or `roles/editor`.

Validate with:
```bash
python3 iam/validate_iam.py iam-policy.json
```
This script fails if any binding's role is `roles/owner` or
`roles/editor`, and passes otherwise. Stdlib `json` only.

## ⚠️ This repo is intentionally broken

There are **exactly three planted faults**, one covering each of:
1. VPC / subnet / DNS wiring (`docker-compose.yml`)
2. Firewall over-exposure (`firewall.yaml`)
3. IAM least-privilege violation (`iam-policy.json`)

Find them, fix them, and confirm with the commands below. No hints on
exact fixes are given in code comments — reason from the intended design
above.

## How to validate (local only, ₹0)

```bash
docker compose config
docker compose up -d
docker compose exec app ping -c 2 db      # should succeed once Task 1 is fixed
python3 security/validate_firewall.py firewall.yaml   # should exit 0 once Task 2 is fixed
python3 iam/validate_iam.py iam-policy.json            # should exit 0 once Task 3 is fixed
docker compose down
```

No GCP project, credentials, or API keys are used anywhere in this repo —
all values are placeholders.
