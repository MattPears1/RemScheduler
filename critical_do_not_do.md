# CRITICAL DO NOT DO - Production Rules

## ⚠️ NEVER CHANGE THESE WITHOUT EXPLICIT APPROVAL

### 🔌 Ports & Network Configuration
- **DO NOT** change local dev ports from 3000 (frontend) and 5000 (backend)
- **DO NOT** add CORS configuration - it's already properly configured


### 🎨 UI/UX Elements

- **DO NOT** add social proof widgets or trust badges
- **DO NOT** implement pop-ups or modal overlays for marketing
- **DO NOT** add dark mode or have dark mode on default over light mode
- **DO NOT** add fake user data, statistics, or claims about active users - the application is NOT yet public
- **DO NOT** include "Trusted by X users" or similar claims - there are no public users yet
- **DO NOT** add success rates, active user counts, or usage statistics - application is in development

### 🔐 Security & Authentication
- **DO NOT** disable any security middleware
- **DO NOT** store sensitive data in localStorage
- **DO NOT** bypass authentication checks "temporarily"
- **DO NOT** commit .env files or secrets
- **DO NOT** reduce password requirements

### 📦 Dependencies & Build

- **DO NOT** add unnecessary npm packages for simple tasks
- **DO NOT** modify build scripts without understanding deployment
- **DO NOT** change Node version requirements
- **DO NOT** add global CSS that could break existing styles

### 🚀 Production & Deployment
- **DO NOT** change Heroku buildpacks or configuration
- **DO NOT** modify production environment variables locally
- **DO NOT** alter deployment scripts or CI/CD pipeline
- **DO NOT** change production database connection pooling

### 📊 Analytics & Tracking
- **DO NOT** add Google Analytics or tracking pixels
- **DO NOT** implement user behavior tracking
- **DO NOT** add third-party analytics without privacy review

### 🔧 Code Structure
- **DO NOT** reorganize file structure without team discussion
- **DO NOT** change naming conventions (camelCase for JS, snake_case for DB)
- **DO NOT** modify the routing structure
- **DO NOT** alter the API endpoint naming pattern
- **DO NOT** create new versions of existing pages/components - ALWAYS edit the existing files when transforming/optimizing
- **DO NOT** create duplicate pages with "Modern" or "New" suffixes - transform the original files directly

### ⚡ Performance
- **DO NOT** remove lazy loading where implemented
- **DO NOT** disable code splitting
- **DO NOT** add synchronous API calls in render methods
- **DO NOT** remove debouncing from search/filter inputs

## 📝 Notes
- Consider backward compatibility for any changes
- Test thoroughly in development before considering changes

---
Last Updated: August 01, 2025