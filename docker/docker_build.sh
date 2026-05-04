#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker build -t go2_slam:humble -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"
