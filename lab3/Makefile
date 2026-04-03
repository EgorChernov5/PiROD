COMPOSE_FILE := docker-compose.yaml
SERVER_SRC := servers/minio
CONTAINER := pirodgreenplum
PXF_SERVERS_DIR := /data/pxf/servers
TARGET_SERVER_DIR := $(PXF_SERVERS_DIR)/minio

.PHONY: up down wait-pxf copy-minio check-export

up:
	@if ! docker compose version >/dev/null 2>&1; then \
		echo "docker compose or docker-compose is required"; \
		exit 1; \
	fi
	@docker compose -f $(COMPOSE_FILE) up -d
	@$(MAKE) wait-pxf
	@$(MAKE) copy-minio

wait-pxf:
	@echo "Waiting for $(PXF_SERVERS_DIR) in container $(CONTAINER)..."
	@until docker exec $(CONTAINER) test -d $(PXF_SERVERS_DIR) >/dev/null 2>&1; do \
		sleep 2; \
	done
	@echo "$(PXF_SERVERS_DIR) is available."

copy-minio:
	@echo "Copying $(SERVER_SRC) to $(CONTAINER):$(TARGET_SERVER_DIR)"
	@docker exec $(CONTAINER) mkdir -p $(TARGET_SERVER_DIR)
	@docker cp $(SERVER_SRC)/. $(CONTAINER):$(TARGET_SERVER_DIR)
	@echo "Copy completed."

check-export:
	@echo "Checking ext_patients data in database lab3..."
	@if ! docker ps --format '{{.Names}}' | grep -qx '$(CONTAINER)'; then \
		echo "Container $(CONTAINER) is not running."; \
		exit 1; \
	fi
	@docker exec $(CONTAINER) su - gpadmin -c "psql -v ON_ERROR_STOP=1 -d lab3 -c 'select * from ext_patients limit 3;'" || { \
		echo "Export check failed."; \
		exit 1; \
	}
	@echo "Data check passed."

down:
	@if ! docker compose version >/dev/null 2>&1; then \
		echo "docker compose or docker-compose is required"; \
		exit 1; \
	fi
	@docker compose -f $(COMPOSE_FILE) down
