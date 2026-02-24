.PHONY: help install build clean test dist run stop

PYINSTALLER := pyinstaller
VERSION := $(shell python3 -c "import sys; sys.path.insert(0, 'src'); from wacht import __version__; print(__version__)")

help:
	@echo "Wacht - Live Reload Server"
	@echo ""
	@echo "Available targets:"
	@echo "  make build    - Build binary with pyinstaller"
	@echo "  make install  - Install binary to /usr/local/bin/"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove build files"
	@echo "  make run      - Run wacht"
	@echo "  make stop     - Stop running daemon"

build:
	@echo "Building wacht v$(VERSION)..."
	$(PYINSTALLER) --onefile --name wacht --distpath dist src/wacht/__init__.py
	@echo "Binary created: dist/wacht"

install: build
	@echo "Installing to /usr/local/bin/..."
	sudo cp dist/wacht /usr/local/bin/wacht
	sudo chmod +x /usr/local/bin/wacht
	@echo "Installed. Run 'wacht' to start."

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -rf src/wacht/__pycache__ __.pytest_cache .ruff_cache build *.spec __pycache__ build/ *.spec __pycache__/ src/__pycache__/ src/wacht/__pycache__/ tests/.pytest_cache tests/__pycache__/

run:
	python3 wacht.py

stop:
	python3 wacht.py --stop

dist: build
	@echo "Binary ready in dist/wacht"
