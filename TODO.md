# TODO List for RemScheduler

## Critical Issues

### 2. Timezone Mismatch Between Frontend and Backend
**Status**: IDENTIFIED
**Description**: When scheduling messages from Android (or any device), there's a 1-hour time difference between what the user selects and when the message is actually scheduled.

**Root Cause**: 
- User's device is in UTC+1 timezone (1 hour ahead of UTC)
- The datetime-local input shows local time (e.g., 19:23)
- JavaScript converts this to ISO/UTC format (becomes 18:23:00+00:00)
- Local Agent correctly uses UTC but this means messages are scheduled 1 hour earlier than intended

**Example**:
- User selects: 19:23 on Android
- Sent to backend as: 2025-08-01T18:23:00+00:00
- Local Agent logs: "Job 1: ... at 2025-08-01T18:23:00+00:00"
- Message scheduled for: 18:23 UTC (which is already past when user selected 19:23 local)

**Solution Options**:
1. Store and display all times in user's local timezone throughout the system
2. Add timezone selection to the scheduling form
3. Auto-detect user's timezone and adjust accordingly
4. Display both local and UTC times in the UI for clarity

## Critical Issues

### 1. OpenAI Whisper API Not Working on Heroku
**Status**: UNRESOLVED
**Description**: The OpenAI Whisper API fails to work on Heroku even with minimal audio input (single word "hello"). 

**What We've Tried**:
- Updated OpenAI SDK to v1.55.3 and httpx to v0.27.2 to fix proxy parameter errors
- Added comprehensive error handling
- Created custom httpx client with various timeout configurations
- Implemented file size limits (1MB)
- Set timeout to 25 seconds (under Heroku's 30s limit)
- Disabled retries to prevent timeout
- Forced English language for faster processing
- Added diagnostic endpoints
- Verified API key is correctly set in Heroku

**Error Pattern**:
- Initial error: "Client.__init__() got an unexpected keyword argument 'proxies'"
- After fixing SDK versions: "Connection error" after ~10 seconds
- Heroku logs show: "Transcription failed: Connection error."
- The error occurs even with extremely short audio (single word)

**Root Cause**: Unknown. The connection fails after about 10-12 seconds (not 30 seconds), suggesting this is NOT a Heroku timeout issue but rather a networking/DNS problem where Heroku cannot establish a connection to OpenAI's servers.

**Alternative Solutions to Consider**:
1. Use a different speech-to-text service that works better with Heroku
2. Implement client-side speech recognition as a fallback
3. Use a background job queue (like Celery) to handle transcription asynchronously
4. Deploy the transcription service on a different platform that doesn't have these networking limitations

**User Requirement**: Must use OpenAI Whisper specifically, not browser-based speech recognition.