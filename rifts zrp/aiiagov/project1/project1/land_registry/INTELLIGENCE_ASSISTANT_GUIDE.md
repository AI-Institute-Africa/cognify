## 🤖 RIFTS-X Intelligence Assistant - Quick Start Guide

### What's New?

Your RIFTS-X Intelligence Assistant has been completely enhanced to work like ChatGPT or Gemini with:
- **ChatGPT-like Interface** - Modern conversation panel with smooth animations
- **Intelligent Understanding** - Understands intent, context, and relationships
- **System Insights** - Real-time health monitoring and alerts
- **Multi-Entity Search** - Finds records, projects, contracts, tasks, and more
- **Natural Language** - Ask questions in plain English, no special syntax needed

---

### Getting Started

#### 1. **Access the Assistant**
Navigate to: `http://localhost:8000/ai_assistant/`

#### 2. **Ask Your First Question**
Try any of these natural language questions:

```
"Show me all contracts from 2024"
"How many overdue tasks are there?"
"What's the status of the system?"
"List active projects"
"Show pending approvals"
"Find sensitive files"
"Any contracts expiring soon?"
```

#### 3. **Quick Actions (Sidebar)**
Use the sidebar buttons for instant answers:
- **📊 System Status** - Overall system health and metrics
- **⚠️ Overdue Tasks** - Tasks past their due dates
- **📋 Active Projects** - All running projects
- **✅ Pending Approvals** - Items awaiting review

---

### Example Queries & What They Return

| Query | What Happens |
|-------|-------------|
| `"Show files from 2024"` | Searches File entity, filters by year 2024 |
| `"Contracts above $50000"` | Finds contracts with amount > $50,000 |
| `"Pending requisitions"` | Lists requisitions with "Pending" status |
| `"Overdue contracts"` | Shows contracts with milestone breaches |
| `"System status"` | Displays health score and key metrics |
| `"How many active projects?"` | Returns count of active projects |

---

### How It Works

#### **1. Intent Detection**
The AI recognizes what you're trying to do:
- **Search** - "Show me...", "Find...", "List..."
- **Analytics** - "How many...", "Count...", "Statistics..."
- **Summary** - "What is...", "Tell me about...", "Overview..."
- **Status** - "What's the status...", "Progress..."
- **Recommendation** - "Suggest...", "Should I..."

#### **2. Entity Recognition**
Automatically identifies what you're looking for:
- **File** - documents, records
- **Project** - initiatives, programs
- **Contract** - agreements, deals
- **Task** - actions, todos
- **User** - person, employee
- **Department** - team, division

#### **3. Filter Extraction**
Pulls out specific filters from your question:
- **Dates** - Years ("2024"), months ("January")
- **Amounts** - "above $X", "below $Y"
- **Status** - "pending", "approved", "completed", "active", "expired"
- **SLA Issues** - "overdue", "breach", "late"

#### **4. Intelligent Response**
Returns results with:
- Summary statement
- Relevant data items (up to 3 shown initially)
- Actionable insights
- Suggested follow-up questions

---

### Advanced Features

#### **Multi-Turn Conversation**
The assistant remembers recent context:
```
User: "Show me contracts"
[Assistant shows contracts]

User: "How many are expired?"
[Assistant filters the previous results to show expired ones]
```

#### **System Health Monitoring**
Get instant insights:
- Overall health score (0-100)
- Project completion rate
- Task completion rate
- Overdue task percentage
- User activity rate

#### **Real-Time Alerts**
The sidebar automatically shows:
- ⚠️ Overdue items needing attention
- ✅ Pending approvals
- 🔐 Highly sensitive files
- 📅 Contracts expiring soon

---

### Query Tips & Tricks

✅ **DO:**
- Use natural language: "Show me pending leave requests"
- Include specific values: "Contracts above $100k from 2024"
- Ask follow-up questions: "What about the expired ones?"
- Use timeframes: "Last month", "2024", "January"

❌ **DON'T:**
- Need special syntax - plain English works!
- Remember exact field names - describe what you want
- Worry about case - questions are case-insensitive
- Use complex boolean logic - just ask naturally

---

### Common Questions Answered

**Q: Can it show results across multiple entity types?**
A: Currently searches one entity at a time. Future version will support cross-entity queries.

**Q: How current is the data?**
A: Real-time - queries execute immediately against live database.

**Q: Can I export results?**
A: Not yet, but coming soon! For now, screenshot or note the results.

**Q: What if it doesn't understand my query?**
A: It provides a fallback text search. Rephrase with simpler words if needed.

**Q: Can it perform actions?**
A: Currently read-only. Cannot delete, approve, or modify records (coming in future versions).

---

### System Architecture

```
┌─────────────────────────────────────────┐
│      AI Assistant HTML Interface        │
│  (Modern ChatGPT-like conversation)     │
└──────────────┬──────────────────────────┘
               │ AJAX Query
               ▼
┌──────────────────────────────────────────┐
│    Enhanced AI Assistant Service         │
│  - Intent Detection                      │
│  - Entity Recognition                    │
│  - Filter Extraction                     │
│  - Intelligent Response Generation       │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌────────────────┐  ┌──────────────────────┐
│  System Health │  │  Database Queries    │
│  - Metrics     │  │  - Search Results    │
│  - Insights    │  │  - Filtered Data     │
└────────────────┘  └──────────────────────┘
```

---

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send query |
| `Tab` | Focus next quick button |
| Scroll | Browse message history |

---

### Troubleshooting

**Issue: Query returns no results**
- Try rephrasing your question
- Be more specific (add year, amount, status)
- Check that the entity exists in system

**Issue: Connection error**
- Refresh the page
- Check that Django server is running
- Clear browser cache

**Issue: Slow response**
- System may be indexing data
- Wait a few seconds and try again
- Use more specific filters to narrow results

---

### What's Coming Next?

🚀 **Future Enhancements:**
- **Semantic Search** - Understand meaning, not just keywords
- **Conversation History** - Save and resume conversations
- **Recommendations** - "Based on your searches, you might also want..."
- **Voice Input** - Speak your queries
- **Advanced Analytics** - Trends, patterns, forecasts
- **Integration** - Connect with external systems
- **Custom Reports** - Generate formatted reports

---

### Need Help?

- **Dashboard**: Navigate to main menu
- **System Admin**: Contact your IT department
- **Features Request**: Submit via feedback form
- **Bug Report**: Include query and expected vs. actual results

---

**Version**: RIFTS-X Intelligence v2.0 (Enhanced)  
**Last Updated**: June 2026  
**Status**: Production Ready ✅
