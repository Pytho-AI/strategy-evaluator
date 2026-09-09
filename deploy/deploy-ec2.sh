#!/usr/bin/env bash
# Deploy the Strategy Evaluation Workbench to the EC2 box over SSH.
#
#   HOST=ubuntu@54.90.137.38 SSH_KEY=~/.ssh/ml-docker-test.pem ./deploy/deploy-ec2.sh
#
# It rsyncs the repository (minus .git, .venv, tests, workspace) to a directory of
# its own on the host and runs `docker compose up -d --build` there. It never touches
# any other stack on the box. The image builds on the host, so the host architecture
# is whatever the host is; nothing is cross-compiled or pushed to a registry.
set -euo pipefail

HOST="${HOST:-ubuntu@54.90.137.38}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/ml-docker-test.pem}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/strategy-evaluation-workbench}"
HOST_PORT="${HOST_PORT:-9010}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ssh_run() { ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$HOST" "$@"; }

echo "==> target $HOST:$REMOTE_DIR  (published on port $HOST_PORT)"

# The box runs other stacks. Record what is up before we touch anything, refuse to
# take a port another container already publishes, and verify afterwards that every
# one of those containers is still running. This script never prunes, never stops a
# container it did not create, and works only inside $REMOTE_DIR.
BEFORE="$(ssh_run "docker ps --format '{{.Names}}'" | sort)"
echo "==> other containers running now: $(echo "$BEFORE" | grep -v '^strategy-workbench$' | tr '\n' ' ')"

if ssh_run "docker ps --format '{{.Names}} {{.Ports}}' | grep -v '^strategy-workbench ' | grep -q ':$HOST_PORT->'"; then
  echo "refusing to deploy: port $HOST_PORT is already published by another container" >&2
  exit 1
fi

ssh_run "mkdir -p '$REMOTE_DIR'"

echo "==> syncing"
rsync -az --delete \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  --exclude 'app/tests' --exclude 'app/workspace' --exclude 'docs/reviews' \
  --exclude 'doctrine' --exclude '*.pyc' \
  "$REPO_ROOT/" "$HOST:$REMOTE_DIR/"

echo "==> building and starting"
ssh_run "cd '$REMOTE_DIR' && HOST_PORT=$HOST_PORT docker compose up -d --build"

echo "==> checking the other stacks are untouched"
AFTER="$(ssh_run "docker ps --format '{{.Names}}'" | sort)"
MISSING="$(comm -23 <(echo "$BEFORE" | grep -v '^strategy-workbench$') <(echo "$AFTER"))"
if [ -n "$MISSING" ]; then
  echo "STOPPED BY THIS DEPLOY: $MISSING" >&2
  echo "restart them before continuing" >&2
  exit 1
fi
echo "==> all pre-existing containers still running"

echo "==> waiting for health"
for i in $(seq 1 30); do
  if ssh_run "curl -fsS http://127.0.0.1:$HOST_PORT/api/health >/dev/null 2>&1"; then
    echo "==> healthy"
    ssh_run "curl -fsS http://127.0.0.1:$HOST_PORT/api/meta" | head -c 400; echo
    PUBLIC_HOST="${HOST#*@}"
    echo "==> open http://$PUBLIC_HOST:$HOST_PORT/"
    exit 0
  fi
  sleep 3
done

echo "==> did not become healthy; last 60 log lines:" >&2
ssh_run "cd '$REMOTE_DIR' && docker compose logs --tail 60" >&2
exit 1
