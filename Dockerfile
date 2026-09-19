# Render worker: OpenSCAD + Go. linux/arm64. 3538 MB ~ 2 vCPU for tray+lid.
FROM --platform=linux/arm64 golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY web ./web
RUN CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -o /out/bootstrap ./web

FROM --platform=linux/arm64 openscad/openscad:dev
USER root
RUN (apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*) || true
RUN OP=$(command -v openscad || command -v openscad-nightly) \
 && test -n "$OP" \
 && ln -sf "$OP" /usr/bin/openscad \
 && ln -sf "$OP" /usr/local/bin/openscad \
 && /usr/bin/openscad --version
WORKDIR /var/task
COPY --from=build /out/bootstrap /var/task/bootstrap
COPY cad/case.scad cad/devices.scad /var/task/cad/
COPY library/devices.json /var/task/library/
ENV LAMBDA_TASK_ROOT=/var/task
ENV HOME=/tmp
ENV PANEL_ROLE=render
ENV OPENSCAD=/usr/bin/openscad
ENV LIBGL_ALWAYS_SOFTWARE=1
ENTRYPOINT ["/var/task/bootstrap"]
