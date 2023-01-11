VIRT_ENV_PATH=$(shell poetry env info -p)
PYTHON_DIR=python3.10
BUILD_PATH=build/exe.linux-x86_64-3.10


build_server:
	poetry run python setup.py build	
	cp -r $(VIRT_ENV_PATH)/lib/$(PYTHON_DIR)/site-packages/sqlalchemy/ $(BUILD_PATH)/lib
	cp -r $(VIRT_ENV_PATH)/lib/$(PYTHON_DIR)/site-packages/PyQt6/Qt6/plugins/platforms/ $(BUILD_PATH)
