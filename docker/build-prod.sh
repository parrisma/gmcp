#!/bin/bash

docker build \
-f docker/Dockerfile.prod \
-t gofr-plot_prod:latest \
.