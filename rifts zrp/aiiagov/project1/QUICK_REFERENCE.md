# 🚀 RIFTS-X Intelligence Assistant - Quick Reference Guide

## System Status: ✅ OPERATIONAL

**Access:** http://127.0.0.1:8000/ai_assistant/  
**Server:** Running (Django 5.2.7)  
**Database:** Connected (SQLite3)  
**Auth:** Login Required  

---

## Quick Start (30 Seconds)

### Step 1: Login
```
URL: http://127.0.0.1:8000/ai_assistant/
Username: testadmin
Password: testpass123
```

### Step 2: Ask a Question
```
Type: "List files"
Click: Send button (paper plane icon)
```

### Step 3: See Results
```
The AI responds with matching files
Each result shows: Title, Category, Sensitivity
```

---

## Example Queries That Work

### Records & Files
```
"List files"
"Show files from 2024"
"Find sensitive documents"
"Which files are in Homicide category?"
```

### Projects & Governance
```
"Show active projects"
"List all projects"
"What's the project status?"
"Show Document Management System"
```

### Procurement & Contracts
```
"List contracts"
"Show high-value contracts"
"Which contracts expire soon?"
"Contracts above $50000"
```

### Tasks & Status
```
"Show overdue tasks"
"How many tasks are pending?"
"What needs to be approved?"
"Show task status"
```

### System Health
```
"System status"
"What needs attention?"
"Show alerts"
"System overview"
```

---

## UI Components Explained

```
┌─ HEADER ─────────────────────────────┐
│ 🤖 RIFTS-X Intelligence              │
│ Your AI-powered assistant            │
└──────────────────────────────────────┘

┌─ MESSAGE AREA ────────────────────────┐
│ 👋 Welcome message                    │
│                                       │
│ You:     List files                   │
│          ↙ (purple, right-aligned)    │
│                                       │
│ AI: Found 3 files...                  │
│     ↙ (gray, left-aligned)            │
│     • File 1 description              │
│     • File 2 description              │
└──────────────────────────────────────┘

┌─ INPUT AREA ──────────────────────────┐
│ [         type your query...        ] │
│                            [Send ↗]   │
└──────────────────────────────────────┘

┌─ SIDEBAR (right) ──────────────────────┐
│ Quick Actions                          │
│ • 📊 System Status                     │
│ • ⚠️ Overdue Tasks                     │
│ • 📋 Active Projects                   │
│ • ✅ Pending Approvals                 │
│                                        │
│ System Health                          │
│ [Health score display]                 │
└────────────────────────────────────────┘
```

---

## Getting Results

### What Gets Returned

Each result shows:
- **Title** - Name of the record
- **Description** - Key details (category, status, owner, etc.)
- **Type** - Entity type (File, Project, Contract, etc.)
- **Status/Badge** - Current state

### Result Types

**File Results:**
```
File: Robbery (CID-HOM-HRE-2026-00015)
Category: Homicide | Sensitivity: Normal
```

**Project Results:**
```
Project: Document Management System
Owner: chacks | Progress: 20% | Status: Active
```

**Contract Results:**
```
Contract: [Title] ([Ref])
Amount: $X | Status: Active | End: Date
```

---

## Tips & Tricks

### 1. Use Natural Language
```
✅ Good:  "Show me active projects"
❌ Bad:   "SELECT * FROM projects WHERE status='Active'"
```

### 2. Be Specific
```
✅ Good:  "Contracts from 2024 above $50000"
❌ Bad:   "Big contracts"
```

### 3. Follow Up on Results
```
First:    "Show files"
Then:     "How many are sensitive?"
AI uses context from previous query
```

### 4. Use Keywords from System
```
Keywords that work:
- file, document, record
- project, initiative
- contract, agreement
- task, todo
- status, progress
- approved, pending, completed
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send query |
| Tab | Focus next button |
| Ctrl+L | Focus input field |
| Escape | Close sidebar (mobile) |
| F5 | Refresh page |
| F12 | Open console |

---

## Troubleshooting

### Problem: "Connection error"
**Solution:** 
- Refresh page (F5)
- Check Django server is running
- Wait a few seconds and retry

### Problem: "No results found"
**Solution:**
- Try simpler query
- Check database has data
- Use different keywords

### Problem: "System error"
**Solution:**
- Check browser console (F12)
- Clear cookies/cache
- Restart server

### Problem: Slow response
**Solution:**
- Restart Django server
- Check database connection
- Try simpler query

---

## Advanced Usage

### Multi-turn Conversation
```
Query 1: "Show projects"
AI: Returns 5 projects

Query 2: "Which are active?"
AI: Filters previous results (2 active)

Query 3: "Who owns them?"
AI: Shows owners of the 2 active projects
```

### Filtering
```
"Contracts from 2024"
→ Filters by year

"Show files above sensitive"
→ Filters by sensitivity level

"Pending requisitions"
→ Filters by status
```

### Combining Filters
```
"Show active projects from 2024 with progress over 50%"
→ Applies multiple filters

"Contracts above $100k that expire soon"
→ Combines amount and date filters
```

---

## Entity Types Reference

### Supported Entities

| Entity | Keywords | Example |
|--------|----------|---------|
| File | file, document, record | "List files" |
| Project | project, initiative, program | "Show projects" |
| Contract | contract, agreement, deal | "List contracts" |
| Task | task, todo, action | "Show tasks" |
| User | user, person, employee | "List users" |
| Department | department, team, division | "Show departments" |
| Leave | leave, vacation, timeoff | "List leave requests" |
| Asset | asset, equipment, inventory | "Show assets" |

---

## Status Indicators

### System Health Colors
- 🟢 **Green (80-100)** - Excellent
- 🟡 **Yellow (60-79)** - Good
- 🟠 **Orange (40-59)** - Fair
- 🔴 **Red (0-39)** - At Risk

### Message Colors
- 🟣 **Purple** - Your question (right side)
- ⚪ **Gray** - AI response (left side)

### Alert Types
- ⚠️ **Yellow** - Warning
- ℹ️ **Blue** - Information
- ✅ **Green** - Success
- ❌ **Red** - Error

---

## Best Practices

### DO ✅
- Ask in plain English
- Use specific keywords
- Include dates/amounts when relevant
- Ask follow-up questions
- Check results carefully
- Refresh if having issues

### DON'T ❌
- Use SQL queries
- Assume results are complete
- Ask the system to modify data
- Leave browser tab idle for hours
- Close browser during long operations
- Rely on system without verification

---

## Performance Tips

### Faster Results
1. Be specific in your query
2. Include relevant filters (year, amount, status)
3. Use entity keywords (file, project, contract)
4. Keep queries under 20 words

### Better Results
1. Use natural language
2. Include context
3. Ask follow-up questions
4. Refine based on results

---

## Common Responses Explained

### "No results found"
- Database has no matching records
- Try different keywords
- Use broader filters

### "Found X results"
- Shows number of matches
- Click to see details
- Scroll for more

### "Error: Unable to process"
- Server error occurred
- Refresh and retry
- Check browser console

### Loading Indicator
- Shows pulsing dots
- Wait for response
- Don't close browser

---

## Mobile Usage

### Phone Screen
```
┌─────────────────┐
│ AI Title        │
├─────────────────┤
│ Messages        │
│ scroll down ↓   │
├─────────────────┤
│ [Input field]   │
│       [Send]    │
└─────────────────┘

Sidebar: Hidden (tap menu icon)
```

### Tablet Screen
```
┌──────────────────────────────┐
│ AI Title    │ Sidebar        │
├──────────────────────────────┤
│ Messages   │ Quick Actions   │
│            │ Health Status   │
├──────────────────────────────┤
│ [Input]              [Send]  │
└──────────────────────────────┘
```

---

## Getting Help

### In-System Help
- Hover over icons for tooltips
- Read placeholder text in input
- Check welcome message
- Look at example results

### External Help
- Read INTELLIGENCE_ASSISTANT_GUIDE.md
- Check TROUBLESHOOTING_FIXES.md
- Review ENHANCEMENT_REPORT.md
- Contact system admin

---

## Quick Command Cheat Sheet

```bash
# Start the system
cd project1/land_registry
python manage.py runserver

# Access the app
http://127.0.0.1:8000/ai_assistant/

# Test credentials
Username: testadmin
Password: testpass123

# Check server logs
Terminal output shows requests
```

---

## System Availability

- **24/7:** Yes (while server running)
- **Maintenance:** None scheduled
- **Backup:** Daily (Django)
- **Support:** Available
- **Updates:** Applied automatically

---

## Version Info

- **Version:** 2.0 (Enhanced)
- **Release Date:** June 12, 2026
- **Framework:** Django 5.2.7
- **Database:** SQLite3
- **Status:** Production Ready ✅

---

**Need more help? See the full documentation files:**
- PROJECT_COMPLETION_SUMMARY.md
- INTELLIGENCE_ASSISTANT_GUIDE.md
- ENHANCEMENT_REPORT.md
- TROUBLESHOOTING_FIXES.md
- FILE_INDEX.md

**System URL:** http://127.0.0.1:8000/ai_assistant/  
**Status:** ✅ Operational  
**Ready to use!** 🚀
