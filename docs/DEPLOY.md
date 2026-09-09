# Deploy

One process serves the operator UI at `/` and the API at `/api`. It needs no cloud
account, no model key and no network at run time. All scenario content is fictional
and marked `UNCLASSIFIED — SYNTHETIC`.

## Run locally

```sh
make app-run          # http://127.0.0.1:8765/
make image            # build the container image
make image-run        # run it on http://127.0.0.1:8790/
```

## Deploy to the box (EC2, docker compose)

```sh
HOST=ubuntu@54.90.137.38 SSH_KEY=~/.ssh/ml-docker-test.pem HOST_PORT=8790 ./deploy/deploy-ec2.sh
```

The script rsyncs the repository to `/home/ubuntu/strategy-evaluation-workbench` on the
host, builds the image there and starts it with `docker compose up -d --build`, then
waits for `/api/health`. It uses its own directory, its own compose project and its own
named volume, so it does not touch the `pytho-app` stack on the same box. The image is
built on the host, so nothing is cross-compiled and no registry is needed.

Result: `http://54.90.137.38:8790/`. Port 8790 must be open in the security group for
whoever needs to reach it.

| Variable | Default | Meaning |
|---|---|---|
| `HOST` | `ubuntu@54.90.137.38` | ssh target |
| `SSH_KEY` | `~/.ssh/ml-docker-test.pem` | ssh key |
| `REMOTE_DIR` | `/home/ubuntu/strategy-evaluation-workbench` | where the repo lands |
| `HOST_PORT` | `8790` | published port on the host |
| `STRATEGY_WORKSPACE_DIR` | `/data/workspace` (in the image) | product state; a named volume |

## Redeploy after a new UI artifact

```sh
./deploy/swap-ui.sh ~/Downloads/UI_V3.html    # decode and stage the new bundle
# place the recovered tree, run the UI tests, then:
HOST=ubuntu@54.90.137.38 ./deploy/deploy-ec2.sh
```

## Verify a deployment

```sh
curl -s http://54.90.137.38:8790/api/health
curl -s http://54.90.137.38:8790/api/meta
curl -s 'http://54.90.137.38:8790/api/snapshot?batch=1'   # str_blue_1 invalid, ranking str_blue_2, str_blue_3
```

Then walk `docs/QA_CHEATSHEET.md` in a browser.

## State and reset

Product state (ingested reports, proposed claims, review decisions, collection drafts,
audit log) lives in the `workbench-state` volume, not in the repository, and survives
container restarts. `POST /api/workspace/reset` clears one workspace. The frozen
`dataset/` directory is never written.

## Security

The application has no authentication. Anyone who can reach the port can use it and can
ingest documents into its workspace. For anything beyond a demo, put it behind the
existing reverse proxy with basic auth or restrict the security group to known
addresses. Do not place real classified or sensitive material in it: the ingestion path
stores the full text of whatever is uploaded.
