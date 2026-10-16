# RIFTS-X RAG System - Quick Start Guide

## 🎯 What is RAG?

RAG (Retrieval-Augmented Generation) makes your AI system:
1. **Aware** - Knows all system components (models, views, services, workflows)
2. **Intelligent** - Retrieves relevant information for any query
3. **Context-Aware** - Analyzes documents and extracts structured information
4. **Helpful** - Generates informed answers combining all available knowledge

## 🚀 Getting Started

### Step 1: Install Optional Dependencies (Optional)
For full document support, install:
```bash
pip install PyPDF2 python-docx Pillow pytesseract
```

### Step 2: Access the System
All endpoints are authenticated (login required):
- Base URL: `http://localhost:8000`
- All endpoints require Django login

## 📚 Three Ways to Use RAG

### Method 1: Simple Query (No Documents)

**Web Interface:**
1. Open http://localhost:8000/ai_assistant/
2. Type your question in the chat box
3. Click "Send" or press Enter
4. System retrieves relevant components and returns answer

**Example Question:** "How do I track file movements?"

**Response includes:**
- ✓ Relevant models (File, CustodyLog)
- ✓ Relevant views (borrow_file, return_file)
- ✓ Relevant workflow (File Borrowing)
- ✓ Relevant documentation

### Method 2: Query with Documents

**Web Interface:**
1. Open http://localhost:8000/ai_assistant/
2. Click "Upload Documents" 
3. Select PDF, DOCX, or image file
4. Type your question
5. Click "Send with Analysis"

**Example:** Upload "loan_policy.pdf" + ask "What are the borrowing procedures?"

**Response includes:**
- ✓ System component recommendations
- ✓ Extracted content from document
- ✓ Keywords and entities from document
- ✓ Combined context answer

### Method 3: Document Analysis Only

**Web Interface:**
1. Open http://localhost:8000/ai_assistant/analyze_document/
2. Upload a document
3. Get instant analysis:
   - Full text extraction
   - Keywords
   - Entities (emails, phone numbers, amounts, dates)
   - Metadata

**Supported Formats:**
- ✓ PDF (text extraction)
- ✓ DOCX (text + tables)
- ✓ JPG/PNG/GIF (OCR with Tesseract)
- ✓ TXT (plain text)

## 🔌 API Examples

### Example 1: Query with Documents
```bash
curl -X POST http://localhost:8000/ai_assistant/rag/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -F "query=What is the procurement process?" \
  -F "documents=@vendor_guide.pdf"
```

### Example 2: Analyze Document Only
```bash
curl -X POST http://localhost:8000/ai_assistant/analyze_document/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -F "document=@contract.docx"
```

### Example 3: Query Only (No Upload)
```bash
curl -X POST http://localhost:8000/ai_assistant/rag/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d "query=Show me all project workflows"
```

### Example 4: Via Python (Django Shell)
```python
python manage.py shell

from registry.services.rag_system import RAGService, DocumentAnalyzer

# Query with context
result = RAGService.query_with_rag("How do I create a project?")
print(result['answer'])

# Analyze document
analysis = DocumentAnalyzer.analyze_document("policy.pdf")
print("Keywords:", analysis['keywords'])
print("Entities:", analysis['entities'])
```

## 📖 What the System Knows

### Models (59 Total)
- **Records:** File, Folio, FileVersion, CustodyLog, DigitalShare
- **Governance:** Project, ProjectPhase, ProjectTask, Sprint, Benefit
- **Finance:** Contract, Tender, Requisition, CostRecovery, Budget
- **HR:** LeaveRequest, Asset, Department, User, UserSecurity
- **Intelligence:** ScannedDocument, KnowledgeEntry, ForensicAudit, CloudFile
- And 34 more...

### Views (100+ Total)
Organized by domain:
- **Records Management:** view_file, add_file, borrow_file, return_file, search_files
- **Governance:** create_project, view_project, approve_phase, create_task
- **Finance:** create_contract, manage_requisition, create_budget, track_costs
- **HR & Admin:** leave_request, asset_management, user_management
- **AI & Intelligence:** query_ai, scan_documents, generate_insights

### Services (15 Total)
- ai_assistant (basic NLP)
- ai_assistant_enhanced (ChatGPT-like)
- rag_system (retrieval-augmented generation)
- cloud_vault, custody, governance, permissions
- scanning, security, notifications
- And more...

### Workflows (10+ Total)
- **File Borrowing:** Request → Verify → Sign-out → Track → Return → Sign-in
- **Project Approval:** Create → Submit → Review → Approve → Proceed
- **Procurement:** Requisition → Manager → Finance → PO → Delivery
- **Leave Management:** Submit → Manager → HR → Final → Process
- And more...

## 💡 Common Questions & How to Ask

**Question Type:** System Information
- "What models does RIFTS-X have?"
- "Show me all governance views"
- "Explain the file borrowing workflow"

**Question Type:** Procedures
- "How do I create a project?"
- "What's the requisition process?"
- "How do I request time off?"

**Question Type:** Integration
- "How do file movements work?"
- "What services handle security?"
- "How is custody tracked?"

**Question Type:** With Documents
- "Analyze this contract and tell me the payment terms"
- "What are the key policies in this document?"
- "Extract all dates and amounts from this PDF"

## 🔍 Example Responses

### Query: "How do I borrow a file?"
```
Found 3 relevant system components:
• Model: File - Physical record tracking with custody chain and version history
• Model: CustodyLog - Complete audit trail of file movements and access  
• View: borrow_file - Initiate file movement with sign-out

Found relevant workflow:
• File Borrowing: User requests file → Verify permissions → Sign out 
  → Track location → Return → Sign in

Answer: To borrow a file, use the borrow_file view. The system will:
1. Verify your permissions in the File model
2. Create a CustodyLog entry for audit trail
3. Track the file location
4. Provide sign-out mechanism
5. Complete the borrowing workflow
```

### Query: "What's the procurement process?" (with vendor_guide.pdf)
```
Found 3 relevant components:
• View: create_requisition - Submit purchase request
• Service: governance - Project workflow and approval orchestration
• Workflow: Procurement - Requisition → Manager → Finance → PO → Delivery

Document Analysis:
Keywords: procurement, approval, budget, vendor, contract
Entities: 
  EMAIL: procurement@company.com
  PHONE: (555) 123-4567
  AMOUNT: $50,000
  DATE: 2026-07-01

Combined Answer: Based on system workflows and document analysis...
```

## ⚙️ Configuration

### Increase Result Limits
Edit `registry/services/rag_system.py`:
```python
# Change from top_k=5 to top_k=10
results = RAGRetriever.retrieve_for_query(query, top_k=10)
```

### Enable More Document Types
```python
# Install additional parsers
pip install openpyxl xlrd  # Excel files
pip install pptx            # PowerPoint
```

### Adjust Cache TTL
Edit `registry/services/rag_system.py`:
```python
# Change from 86400 (24 hours) to 3600 (1 hour)
cache.set('system_knowledge_base', knowledge, 3600)
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No results returned | Try simpler keywords; check Django cache |
| "RAG not available" | Ensure rag_system.py exists in registry/services/ |
| PDF analysis fails | Install PyPDF2: `pip install PyPDF2` |
| OCR not working | Install pytesseract and tesseract-ocr system package |
| Document upload fails | Check file size limits and permissions |

## 📊 View Knowledge Base

**Web Interface:**
- Open: http://localhost:8000/ai_assistant/knowledge_base/
- Browse all indexed components
- See models, views, services, workflows
- Search within knowledge base

## 🎓 Next Steps

1. **Try Simple Queries** - "How do I...?" questions
2. **Upload Documents** - Test with PDF or DOCX files
3. **Use API** - Integrate with other systems
4. **Customize** - Extend with domain-specific knowledge
5. **Monitor** - Check cache performance

## 📞 Support

For issues, check:
1. Django logs: Check for ImportError or AttributeError
2. Browser console: Check JavaScript errors  
3. Network tab: Verify POST requests are being sent
4. Documentation: RAG_SYSTEM_GUIDE.md for detailed info

## ✅ You're Ready!

Your RIFTS-X system now has:
- ✓ Knowledge of every component (59 models, 100+ views, 15 services)
- ✓ Document analysis capability (PDF, DOCX, images, text)
- ✓ Smart retrieval (semantic matching and ranking)
- ✓ Context-aware responses (combining all sources)

**Happy querying! 🚀**
