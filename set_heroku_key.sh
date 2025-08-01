#!/bin/bash
# Script to set OpenAI API key in Heroku

echo "Setting OpenAI API key in Heroku..."
heroku config:set OPENAI_API_KEY=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

echo "Verifying key is set..."
heroku config:get OPENAI_API_KEY

echo "Restarting app..."
heroku restart

echo "Done! Check logs with: heroku logs --tail"