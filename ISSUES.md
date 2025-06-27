# ElPyFi PM Claude - Issues Dashboard

*Last Updated: 2025-06-26*

## Active Issues

### 🔴 High Priority

#### Core Engine Issues
- **[ENGINE-001]** Database schema mismatch: `positions` table missing `order_id` column
  - **Service**: elpyfi-core/elpyfi-engine
  - **Impact**: Positions recorded but with missing data
  - **Status**: Open
  - **Details**: Engine tries to write order_id but table schema doesn't have it. Positions still get recorded via internal events.

#### API Service Issues
- **[API-001]** Service documentation missing
  - **Service**: elpyfi-api
  - **Impact**: No clear integration docs
  - **Status**: Open
  - **Details**: No README.md or API documentation found

### 🟡 Medium Priority

#### AI Service Issues
- **[AI-001]** Replace print statements with proper logging
  - **Service**: elpyfi-ai
  - **Impact**: Poor production debugging
  - **Status**: Open
  - **Details**: Use Python's logging module with DEBUG/INFO/ERROR levels

- **[AI-002]** Environment variable validation missing
  - **Service**: elpyfi-ai
  - **Impact**: Runtime failures instead of clear startup errors
  - **Status**: Open
  - **Details**: Validate ANTHROPIC_API_KEY and other required env vars on startup (~10 lines)

- **[AI-003]** Update Pydantic .dict() to .model_dump()
  - **Service**: elpyfi-ai
  - **Impact**: Deprecation warnings
  - **Status**: Open
  - **Details**: main.py lines 157-158 use deprecated .dict() method (2-line fix)

#### Dashboard Issues
- **[DASH-001]** Missing loading states and error handling
  - **Service**: elpyfi-dashboard
  - **Impact**: Poor UX when API is slow/down
  - **Status**: Open
  - **Details**: SWR hooks need loading spinners and error displays (~20 lines)

- **[DASH-002]** No error boundary components
  - **Service**: elpyfi-dashboard
  - **Impact**: App crashes instead of graceful error handling
  - **Status**: Open
  - **Details**: Add React error boundaries to PositionsTable, SignalsTable, PerformanceChart (~50 lines)

### 🟢 Low Priority

#### Infrastructure Issues
- **[INFRA-001]** Remove local venv directories
  - **Services**: elpyfi-engine, elpyfi-ai
  - **Impact**: Confusion about which Python environment to use
  - **Status**: Open
  - **Details**: Delete local venv/ dirs, use shared PM Claude venv

- **[INFRA-002]** Add PM Claude service status checks
  - **Service**: elpyfi-engine
  - **Impact**: No coordination between services
  - **Status**: Open
  - **Details**: Check PM_CLAUDE_SERVICE_STATUS env var or call status endpoint

## Resolved Issues

### ✅ Recently Resolved
- **[DASH-003]** Hydration warning with Dark Reader extension
  - **Service**: elpyfi-dashboard
  - **Resolution**: Fixed SVG elements in Navigation.tsx
  - **Resolved**: 2025-06-25

## Issue Management

### Priorities
- 🔴 **High**: Blocks functionality or causes data loss
- 🟡 **Medium**: Affects UX or development workflow
- 🟢 **Low**: Nice-to-have improvements

### Service Codes
- **ENGINE**: elpyfi-core/elpyfi-engine
- **AI**: elpyfi-ai
- **API**: elpyfi-api
- **DASH**: elpyfi-dashboard
- **INFRA**: PM Claude infrastructure

### Status Tracking
- **Open**: Issue identified, needs work
- **In Progress**: Currently being worked on
- **Blocked**: Waiting on external dependency
- **Resolved**: Issue fixed and verified

## Quick Actions

### Create New Issue
```bash
# Add to this file with format:
# [SERVICE-###] Brief description
# - Service: service-name
# - Impact: user/system impact
# - Status: Open
# - Details: technical details
```

### Close Issue
Move from Active to Resolved section with resolution details and date.

---

*This dashboard replaces the scattered issue tracking in individual CLAUDE.md files*