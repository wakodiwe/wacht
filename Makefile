.PHONY: help install build clean test dist run stop publish testpypi

PYINSTALLER := pyinstaller
VERSION := $(shell python3 -c "from wacht import __version__; print(__version__)")

help:
	@echo "Wacht - Live Reload Server v$(VERSION)"
	@echo ""
	@echo "Available targets:"
	@echo " make test       - Run tests"
	@echo " make run        - Run wacht"
	@echo " make stop       - Stop daemon"
	@echo " make build      - Build binary with pyinstaller"
	@echo " make install    - Install binary to /usr/local/bin/"
	@echo " make publish    - Build and upload to PyPI"
	@echo " make testpypi   - Build and upload to TestPyPI"
	@echo " make clean      - Remove build files"

test:
	python3 -m unittest discover -s tests -v

run:
	python3 wacht.py

stop:
	python3 wacht.py --stop

build:
	@echo "Building wacht v$(VERSION)..."
	$(PYINSTALLER) --onefile --name wacht --distpath dist wacht/__init__.py
	@echo "Binary created: dist/wacht"

install: build
	@echo "Installing to /usr/local/bin/..."
	sudo cp dist/wacht /usr/local/bin/wacht
	sudo chmod +x /usr/local/bin/wacht
	@echo "Installed. Run 'wacht' to start."

publish:
	@echo "Building and publishing to PyPI..."
	python3 -m build
	twine upload dist/*

testpypi:
	@echo "Building and uploading to TestPyPI..."
	python3 -m build
	twine upload --repository testpypi dist/*

clean:
	rm -rf build/ dist/ *.spec
	rm -rf __pycache__/ wacht/__pycache__/ tests/__pycache__/
	rm -rf .pytest_cache/ .ruff_cache/

dist: build
	@echo "Binary ready in dist/wacht"
