# ─────────────────────────────────────────────────
#  EcoVerify-Prime · Development Makefile
# ─────────────────────────────────────────────────

.PHONY: backend-install backend-dev mcp-dev frontend-install frontend-dev dev test lint clean

# ── Backend ──────────────────────────────────────
backend-install:
	cd backend && uv sync

backend-dev:
	cd backend && uv run uvicorn ecoverify.main:app --reload --port 8000

mcp-dev:
	cd backend && uv run python -m ecoverify.mcp.server

# ── Frontend ─────────────────────────────────────
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

# ── Combined ─────────────────────────────────────
dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  Terminal 1:  make backend-dev"
	@echo "  Terminal 2:  make frontend-dev"

install: backend-install frontend-install

# ── Quality ──────────────────────────────────────
test:
	cd backend && uv run pytest tests/ -v

lint:
	cd backend && uv run ruff check src/ tests/
	cd backend && uv run ruff format --check src/ tests/

format:
	cd backend && uv run ruff format src/ tests/

typecheck:
	cd backend && uv run mypy src/ecoverify/

# ── Cleanup ──────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.venv frontend/node_modules
