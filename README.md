# Project Aether (RemScheduler)

A sophisticated remote command scheduling and execution system that bridges mobile devices with Windows desktop computers through a cloud-based hub.

## Overview

Project Aether allows you to:
- Dictate commands via voice from your Android device
- Schedule commands to execute on your Windows computer
- Manage complex sequences of commands
- Handle API rate limits intelligently
- Monitor and control execution remotely

## Architecture

The system consists of three components:

1. **Heroku Web Application** - Central hub for scheduling and coordination
2. **Windows Local Agent** - Executes commands on your desktop
3. **Mobile Web Interface** - Control center accessible from any device

## Setup Instructions

### 1. Deploy to Heroku

```bash
# Login to Heroku
heroku login

# Add Heroku remote (if not already added)
heroku git:remote -a remscheduler

# Deploy
git push heroku main
```

### 2. Set Environment Variables

Set these in Heroku dashboard or via CLI:

```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set OPENAI_API_KEY="your-openai-api-key"
```

### 3. Setup Local Agent

1. Navigate to `local-agent` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `config.ini.example` to `config.ini`
4. Update `config.ini` with your Heroku app URL and API key
5. Run: `python agent.py`

### 4. Generate Agent API Key

1. Login to the web interface
2. Go to Settings
3. Generate a new API key for your agent
4. Copy the key to your `config.ini`

## Features

- **Voice Dictation**: Convert speech to text commands
- **Flexible Scheduling**: Single or sequential message execution
- **Rate Limit Handling**: Automatic postponement when limits are hit
- **Real-time Updates**: WebSocket-based communication
- **Job Management**: Edit, reschedule, or cancel pending jobs
- **PWA Support**: Install as an app on Android devices

## Security

- All passwords and API keys are hashed
- HTTPS encryption for all communications
- Agent authentication via secure tokens
- User isolation for multi-tenant usage

## Development

To run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run the application
python app.py
```

## License

Private project - All rights reserved