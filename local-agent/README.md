# RemScheduler Local Agent

## Quick Start

**To run the agent:**
1. Double-click `run_agent_v2.bat`
2. The agent will automatically:
   - Stop any running instances
   - Check database integrity
   - Create fresh database if needed
   - Start the agent

## Files

- `run_agent_v2.bat` - The ONLY file you need to run the agent
- `agent_v2.py` - Main agent code
- `config.ini` - Configuration (server URL, etc.)
- `requirements-windows.txt` - Python dependencies
- `local_messages.db` - Local database (created automatically)

## Troubleshooting

If the agent won't start:
1. Close all Python windows
2. Delete `local_messages.db` if it exists
3. Run `run_agent_v2.bat` again

The agent will automatically handle database corruption and create a fresh database when needed.