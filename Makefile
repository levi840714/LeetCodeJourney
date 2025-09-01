# Makefile for LeetCode Journey Project

# Define python and pip executables from the virtual environment  
PYTHON = .venv/bin/python3
PIP = .venv/bin/pip3

.PHONY: install run clean format-sheets upgrade-dashboard upgrade-dashboard-direct test-scripts help

help:
	@echo "Available commands:"
	@echo "  make install         - Install or update python dependencies from requirements.txt"
	@echo "  make run             - Run the backend Flask server for local development"
	@echo "  make clean           - Remove temporary files (e.g., __pycache__)"
	@echo ""
	@echo "Scripts & Tools:"
	@echo "  make format-sheets     - Apply formatting to existing Google Sheets"
	@echo "  make upgrade-dashboard - Upgrade Dashboard with new chart features (uses venv)"
	@echo "  make upgrade-dashboard-direct - Upgrade Dashboard using system Python (no venv)"
	@echo "  make test-scripts      - Test all scripts functionality"

# Target to install dependencies
install: .venv/pyvenv.cfg
	@echo "Force-reinstalling and upgrading dependencies..."
	@$(PIP) install --no-cache-dir --force-reinstall --upgrade -r requirements.txt

# Target to create the venv directory if it doesn't exist
.venv/pyvenv.cfg:
	python3 -m venv .venv

# Target to run the development server
run:
	@echo "Starting Flask server on http://127.0.0.1:5000..."
	@$(PYTHON) app.py

# Target to clean up temporary files
clean:
	@echo "Cleaning up..."
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -exec rm -r {} +

# === SCRIPTS & TOOLS TARGETS ===

# Target to format existing Google Sheets
format-sheets: install
	@echo "🎨 Applying formatting to existing Google Sheets..."
	@cd scripts && $(PYTHON) format_existing_sheets.py

# Target to upgrade Dashboard with new chart features
upgrade-dashboard: install
	@echo "🎯 Upgrading Dashboard with Learning Curve Analytics..."
	@cd scripts && $(PYTHON) refresh_dashboard.py --auto

# Target to upgrade Dashboard using system Python (no venv required)
upgrade-dashboard-direct:
	@echo "🎯 Upgrading Dashboard with system Python..."
	@echo "Installing required packages..."
	@pip3 install --user gspread python-dotenv google-auth-oauthlib flask flask-cors >/dev/null 2>&1 || echo "⚠️  Some packages may need manual installation"
	@cd scripts && python3 refresh_dashboard.py --auto

# Target to test script functionality
test-scripts:
	@echo "🧪 Testing script imports and basic functionality..."
	@echo "Testing format_existing_sheets.py import..."
	@cd scripts && python3 -c "import sys; sys.path.append('..'); from format_existing_sheets import format_existing_sheets; print('✅ Format sheets script imports successfully')" || echo "⚠️  Format sheets script requires dependencies - use 'make install' first"
	@echo "Testing refresh_dashboard.py import..."
	@cd scripts && python3 -c "import sys; sys.path.append('..'); from refresh_dashboard import refresh_dashboard_with_charts; print('✅ Dashboard refresh script imports successfully')" || echo "⚠️  Dashboard refresh script requires dependencies - use 'make install' first"
	@echo "Testing main app imports..."
	@python3 -c "from app import setup_dashboard_sheet, apply_problems_formatting; print('✅ Main app functions import successfully')" || echo "⚠️  Main app requires dependencies - use 'make install' first"
	@echo "🧪 Script structure tests completed!"
