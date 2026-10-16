# RIFTS-X RAG (Retrieval-Augmented Generation) System

## Overview

The RAG system transforms RIFTS-X into a comprehensive knowledge-aware AI assistant that:
- **Knows Every Component** - Indexed database models, views, services, workflows
- **Analyzes Documents** - PDF, DOCX, TXT, images with OCR
- **Retrieves Context** - Smart semantic matching for relevant information
- **Generates Answers** - Context-aware responses combining retrieval + generation

## Architecture

### 1. System Components Knowledge Base
Automatically indexes all RIFTS-X components:

```
├── Models (59 total)
│   ├── File & Records Management
│   ├── Governance & Projects
│   ├── Finance & Procurement
│   ├── HR & Assets
│   └── Intelligence & Audit
├── Views (100+ total)
│   ├── By domain (Records, Governance, Finance, HR)
│   └── With descriptions and purposes
├── Services (15 total)
│   ├── AI, Cloud, Custody, Governance
│   ├── Security, Scanning, Permissions
│   └── Notifications & Workflows
└── Workflows (10+ major)
    ├── File Borrowing
    ├── Project Approval
    ├── Procurement
    └── Leave Management
```

### 2. Document Analysis Pipeline
Processes multiple file types:

```
Input Document
    ↓
File Type Detection
    ↓
Content Extraction
├─ PDF → PyPDF2 text extraction
├─ DOCX → python-docx parsing
├─ Images → Tesseract OCR
└─ Text → Direct parsing
    ↓
Information Extraction
├─ Keywords (top N by frequency)
├─ Named Entities (email, phone, amounts, dates)
└─ Metadata (size, format, structure)
    ↓
Structured Analysis Output
```

### 3. Retrieval System
Smart matching using multiple strategies:

```
Query
    ↓
Term Extraction
    ↓
Relevance Matching
├─ Model matching (via descriptions)
├─ View matching (via functionality)
├─ Workflow matching (by steps)
├─ Document matching (by title/ref)
└─ Knowledge matching (by content)
    ↓
Scoring & Ranking
    ↓
Top-K Results (configurable)
```

## Usage

### 1. RAG Query Endpoint
```
POST /ai_assistant/rag/
Parameters:
  - query: Natural language question
  - documents: Optional uploaded files (PDF, DOCX, images)

Response:
{
  "query": "How do I borrow a file?",
  "context": {
    "components": [...],
    "documents": [...],
    "workflows": [...],
    "knowledge": [...]
  },
  "analysis": {
    "documents": {
      "loan_policy.pdf": {
        "content": "...",
        "keywords": ["file", "borrowing", "custody"],
        "entities": [...]
      }
    }
  },
  "answer": "Comprehensive answer with referenced components"
}
```

### 2. Document Analysis Endpoint
```
POST /ai_assistant/analyze_document/
Parameters:
  - document: File to analyze (PDF, DOCX, JPG, PNG, TXT, etc.)

Response:
{
  "file_name": "contract.pdf",
  "content": "Extracted text content",
  "keywords": ["payment", "delivery", "warranty"],
  "entities": [
    {"type": "EMAIL", "value": "contact@vendor.com"},
    {"type": "PHONE", "value": "555-0123"},
    {"type": "AMOUNT", "value": "$50,000"},
    {"type": "DATE", "value": "2026-06-15"}
  ],
  "metadata": {
    "pages": 5,
    "title": "Service Agreement"
  }
}
```

### 3. Knowledge Base Viewer
```
GET /ai_assistant/knowledge_base/

Displays:
- All 59 system models with descriptions
- All 100+ views organized by domain
- All 15 services with capabilities
- Major workflows and steps
```

## System Components Knowledge

### Models (Indexed)
- **File**: Physical record tracking with custody chain
- **Project**: Strategic governance initiatives
- **Contract**: Procurement agreements
- **LeaveRequest**: Employee time off management
- **Asset**: Equipment tracking
- **User**: System users and permissions
- **KnowledgeEntry**: Policies and procedures
- And 52 more...

### Views (Indexed by Domain)
**Records Management:**
- view_file: Display file details with custody history
- add_file: Create new physical record
- borrow_file: Initiate file movement
- return_file: Complete file movement
- file_search: Advanced search

**Governance:**
- create_project: Initiate strategic project
- view_project: Project dashboard
- approve_phase: Multi-tier approval
- create_task: Add project work items
- track_benefits: Monitor benefit realization

**Finance:**
- create_contract: Add procurement contract
- manage_contract: Track milestones and SLAs
- create_requisition: Submit purchase request
- manage_budget: Budget allocation
- cost_recovery: Project billing

**HR & Admin:**
- leave_request: Submit time off
- manage_leave: Approve/reject with workflow
- asset_management: Track equipment
- user_management: Manage system users

### Services (Indexed)
- **ai_assistant**: Basic query processing
- **ai_assistant_enhanced**: ChatGPT-like AI with context
- **rag_system**: Retrieval-Augmented Generation
- **cloud_vault**: Cloud storage integration
- **custody**: File movement tracking
- **governance**: Project workflow
- **permissions**: Role-based access control
- **scanning**: OCR and ingestion
- **security**: Encryption and audit
- And more...

### Workflows (Indexed)
1. **File Borrowing**: Request → Verify → Sign-out → Track → Return → Sign-in
2. **Project Approval**: Create → Submit → Review → Approve → Proceed
3. **Procurement**: Requisition → Manager Approval → Finance → PO → Delivery
4. **Leave Management**: Submit → Manager → HR → Final → Process

## Features

### 1. Semantic Search
```python
from registry.services.rag_system import RAGRetriever

results = RAGRetriever.retrieve_for_query("How do I track file movements?")
# Returns:
# - Relevant models (File, CustodyLog)
# - Relevant views (borrow_file, return_file)
# - Relevant documents (custody procedures)
# - Relevant workflows (file borrowing)
```

### 2. Document Intelligence
```python
from registry.services.rag_system import DocumentAnalyzer

analysis = DocumentAnalyzer.analyze_document("contract.pdf")
# Extracts:
# - Full text content
# - Keywords and entities
# - Email addresses, phone numbers
# - Monetary amounts and dates
# - Document metadata
```

### 3. Comprehensive Context
```python
from registry.services.rag_system import RAGService

response = RAGService.query_with_rag(
    query="What's the procurement process?",
    document_files=["vendor_guide.pdf"]
)
# Returns components, documents, workflows, analysis
```

### 4. AI Integration
The RAG system integrates seamlessly with the AI assistant:

```python
from registry.services.ai_assistant_enhanced import EnhancedAIAssistantService

results = EnhancedAIAssistantService.query_with_rag(
    query="Show me user accounts",
    document_files=["user_manual.pdf"]
)
# Results include:
# - AI response with components
# - Formatted data items
# - Document analysis
# - Workflow recommendations
```

## API Examples

### Example 1: Query with Document
```bash
curl -X POST http://localhost:8000/ai_assistant/rag/ \
  -H "X-CSRFToken: YOUR_TOKEN" \
  -F "query=How do I process a contract?" \
  -F "documents=@contract_template.pdf"
```

### Example 2: Analyze Document Only
```bash
curl -X POST http://localhost:8000/ai_assistant/analyze_document/ \
  -H "X-CSRFToken: YOUR_TOKEN" \
  -F "document=@vendor_agreement.docx"
```

### Example 3: Query Only (No Documents)
```bash
curl -X POST http://localhost:8000/ai_assistant/rag/ \
  -H "X-CSRFToken: YOUR_TOKEN" \
  -d "query=List all project workflows"
```

## Configuration

### Enable Optional Dependencies
```bash
# For PDF support
pip install PyPDF2

# For Word document support
pip install python-docx

# For image OCR
pip install Pillow pytesseract

# Then configure Tesseract path (if needed)
# On Linux: sudo apt-get install tesseract-ocr
# On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Cache Configuration
The system uses Django's default cache for knowledge base (24-hour TTL):
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## Performance Considerations

1. **Knowledge Base Indexing**: Built on-demand and cached for 24 hours
2. **Document Analysis**: Streaming for large files
3. **Query Matching**: Uses efficient term intersection for similarity
4. **Database Queries**: Limited to first 100 records per entity type

## Security

- All document analysis is performed server-side
- Temporary files are cleaned up after analysis
- User authentication required for all endpoints
- No document storage (analyzed and discarded)

## Troubleshooting

### "RAG service not available"
Solution: Ensure rag_system.py is in registry/services/ directory

### "PyPDF2 not installed" when processing PDFs
Solution: `pip install PyPDF2`

### "Tesseract not found" for OCR
Solution: Install tesseract-ocr on your system and configure path

### No results returned for query
Solution: Increase similarity threshold or check query specificity

## Future Enhancements

1. **Vector Embeddings**: Use semantic embeddings instead of keyword matching
2. **Persistent Knowledge Store**: Database-backed knowledge graph
3. **Multi-language Support**: Query and document processing in multiple languages
4. **Real-time Indexing**: Automatic re-indexing on model changes
5. **Advanced NLP**: Named entity recognition, relationship extraction
6. **Chat History**: Multi-turn conversations with context persistence

## Files Modified

- `registry/services/rag_system.py` - NEW: Complete RAG implementation
- `registry/services/ai_assistant_enhanced.py` - ADDED: RAG integration
- `registry/views.py` - ADDED: 3 new endpoints
- `registry/urls.py` - ADDED: 3 new URL patterns

## Summary

The RAG system makes RIFTS-X a truly intelligent system that:
✅ Knows all 59 models and 100+ views
✅ Understands all 15 services and their capabilities
✅ Recognizes all major workflows
✅ Analyzes any document format (PDF, DOCX, images, etc.)
✅ Retrieves contextually relevant information
✅ Generates informed answers combining knowledge + documents
