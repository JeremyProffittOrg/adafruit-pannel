.PHONY: build-WebFunction
build-WebFunction:
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o $(ARTIFACTS_DIR)/bootstrap ./web
	mkdir -p $(ARTIFACTS_DIR)/static $(ARTIFACTS_DIR)/cad $(ARTIFACTS_DIR)/library
	cp -a web/static/. $(ARTIFACTS_DIR)/static/
	cp cad/case.scad cad/devices.scad $(ARTIFACTS_DIR)/cad/
	cp library/devices.json $(ARTIFACTS_DIR)/library/
