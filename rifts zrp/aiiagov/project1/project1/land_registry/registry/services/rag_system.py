"""
RAG (Retrieval-Augmented Generation) System for RIFTS-X
Comprehensive knowledge base with document and image analysis
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache

# Document processing imports
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from registry.models import (
    File, KnowledgeEntry, Project, Contract, User, Department,
    ProjectTask, LeaveRequest, ScannedDocument, Asset, Requisition
)


class SystemComponentsKnowledgeBase:
    """Index and store knowledge about all RIFTS-X system components."""
    
    @staticmethod
    def build_system_knowledge() -> Dict[str, Any]:
        """Build comprehensive knowledge base of system components."""
        knowledge = {
            'timestamp': timezone.now().isoformat(),
            'components': {},
            'relationships': {},
            'workflows': {},
        }
        
        # 1. Models Knowledge
        knowledge['components']['models'] = SystemComponentsKnowledgeBase._index_models()
        
        # 2. Views Knowledge  
        knowledge['components']['views'] = SystemComponentsKnowledgeBase._index_views()
        
        # 3. Services Knowledge
        knowledge['components']['services'] = SystemComponentsKnowledgeBase._index_services()
        
        # 4. Workflows
        knowledge['workflows'] = SystemComponentsKnowledgeBase._index_workflows()
        
        # Cache for 24 hours
        cache.set('system_knowledge_base', knowledge, 86400)
        return knowledge
    
    @staticmethod
    def _index_models() -> Dict[str, str]:
        """Index all database models and their purposes."""
        return {
            'File': 'Physical record tracking with custody chain and version history',
            'Folio': 'Collection of related files grouped by matter/subject',
            'FileVersion': 'Version control for digital files with change tracking',
            'CustodyLog': 'Complete audit trail of file movements and access',
            'Project': 'Strategic governance initiatives with phase gates',
            'ProjectPhase': 'Sequential phases with approval requirements and gates',
            'ProjectTask': 'Granular work items with dependencies and assignments',
            'Benefit': 'Business benefits linked to projects with metrics',
            'Contract': 'Procurement agreements with milestone and SLA tracking',
            'Tender': 'Procurement requests and vendor bidding',
            'Requisition': 'Purchase requests with approval workflow',
            'Vendor': 'External suppliers and service providers',
            'LeaveRequest': 'Employee time off with multi-tier approval',
            'Asset': 'Equipment and inventory tracking with depreciation',
            'Department': 'Organizational units with hierarchy',
            'User': 'System users with role-based permissions',
            'UserSecurity': 'Security profiles and access controls',
            'KnowledgeEntry': 'Institutional policies, procedures, and SOPs',
            'ScannedDocument': 'OCR-processed documents with metadata extraction',
            'CloudFile': 'Files stored in cloud vault with sync status',
            'CostRecovery': 'Project cost tracking and billing',
            'ForensicAudit': 'Complete audit trail of all system changes',
        }
    
    @staticmethod
    def _index_views() -> Dict[str, str]:
        """Index major views and their functions."""
        return {
            'Records Management': {
                'view_file': 'Display file details with complete custody history',
                'add_file': 'Create new physical record entry',
                'borrow_file': 'Initiate file movement with sign-out',
                'return_file': 'Complete file movement and update custody',
                'file_search': 'Advanced search with filters and full-text',
            },
            'Governance': {
                'create_project': 'Initiate strategic governance project',
                'view_project': 'Project dashboard with phase progress',
                'approve_phase': 'Multi-tier approval for project gates',
                'create_task': 'Add project work items',
                'track_benefits': 'Monitor project benefit realization',
            },
            'Finance': {
                'create_contract': 'Add procurement contract',
                'manage_contract': 'Track milestones and SLAs',
                'create_requisition': 'Submit purchase request',
                'manage_budget': 'Budget allocation and tracking',
                'cost_recovery': 'Project billing and cost allocation',
            },
            'HR & Admin': {
                'leave_request': 'Submit time off request',
                'manage_leave': 'Approve/reject leave with workflow',
                'asset_management': 'Track equipment and inventory',
                'user_management': 'Manage system users and roles',
                'department_config': 'Organizational hierarchy',
            },
            'AI & Intelligence': {
                'query_ai': 'Natural language system querying',
                'scan_documents': 'OCR and document analysis',
                'generate_insights': 'AI-powered system analytics',
            }
        }
    
    @staticmethod
    def _index_services() -> Dict[str, str]:
        """Index all services and capabilities."""
        return {
            'ai_assistant': 'Basic AI query processing and entity recognition',
            'ai_assistant_enhanced': 'ChatGPT-like AI with context awareness',
            'rag_system': 'Retrieval-Augmented Generation with knowledge indexing',
            'cloud_vault': 'Cloud storage integration and file sync',
            'custody': 'File movement and chain-of-custody tracking',
            'governance': 'Project workflow and approval orchestration',
            'permissions': 'Role-based access control and masking',
            'scanning': 'OCR and document ingestion',
            'security': 'Encryption, audit logging, forensic trails',
            'notifications': 'Real-time alerts and workflows',
        }
    
    @staticmethod
    def _index_workflows() -> Dict[str, Any]:
        """Index major system workflows."""
        return {
            'File Borrowing': {
                'steps': ['User requests file', 'Verify permissions', 'Sign out', 'Track location', 'Return', 'Sign in'],
                'participants': ['File user', 'Records keeper', 'Department head'],
            },
            'Project Approval': {
                'steps': ['Create project', 'Submit phase', 'Department review', 'Executive approval', 'Proceed'],
                'participants': ['Project manager', 'Department', 'Executives'],
            },
            'Procurement': {
                'steps': ['Create requisition', 'Manager approval', 'Finance review', 'Create PO', 'Vendor delivery', 'Invoice'],
                'participants': ['Requester', 'Manager', 'Finance', 'Vendor'],
            },
            'Leave Management': {
                'steps': ['Submit request', 'Manager approval', 'HR review', 'Final approval', 'Process'],
                'participants': ['Employee', 'Manager', 'HR', 'Executives'],
            },
        }


class DocumentAnalyzer:
    """Analyze and extract information from various document types."""
    
    @staticmethod
    def analyze_document(file_path: str) -> Dict[str, Any]:
        """
        Analyze any document type and extract structured information.
        Supports: PDF, DOCX, TXT, JPG, PNG, etc.
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found', 'file': file_path}
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        analysis = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'processed_at': timezone.now().isoformat(),
            'content': '',
            'metadata': {},
            'entities': [],
            'keywords': [],
        }
        
        try:
            if file_ext == '.pdf':
                analysis.update(DocumentAnalyzer._analyze_pdf(file_path))
            elif file_ext == '.docx':
                analysis.update(DocumentAnalyzer._analyze_docx(file_path))
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                analysis.update(DocumentAnalyzer._analyze_image(file_path))
            elif file_ext == '.txt':
                analysis.update(DocumentAnalyzer._analyze_text(file_path))
            else:
                analysis['error'] = f'Unsupported file type: {file_ext}'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        # Extract entities and keywords from content
        if analysis.get('content'):
            analysis['keywords'] = DocumentAnalyzer._extract_keywords(analysis['content'])
            analysis['entities'] = DocumentAnalyzer._extract_entities(analysis['content'])
        
        return analysis
    
    @staticmethod
    def _analyze_pdf(file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF."""
        if not HAS_PDF:
            return {'error': 'PyPDF2 not installed'}
        
        result = {'content': '', 'metadata': {}, 'pages': 0}
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                result['pages'] = len(pdf_reader.pages)
                result['metadata'] = dict(pdf_reader.metadata or {})
                
                for page in pdf_reader.pages:
                    result['content'] += page.extract_text() + '\n'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def _analyze_docx(file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from DOCX."""
        if not HAS_DOCX:
            return {'error': 'python-docx not installed'}
        
        result = {'content': '', 'metadata': {}}
        
        try:
            doc = DocxDocument(file_path)
            result['metadata']['paragraphs'] = len(doc.paragraphs)
            result['metadata']['tables'] = len(doc.tables)
            
            for para in doc.paragraphs:
                result['content'] += para.text + '\n'
            
            # Extract table data
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text for cell in row.cells)
                    result['content'] += row_text + '\n'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def _analyze_image(file_path: str) -> Dict[str, Any]:
        """Extract text from image using OCR."""
        if not HAS_OCR:
            return {'error': 'PIL/pytesseract not installed'}
        
        result = {'content': '', 'metadata': {}}
        
        try:
            img = Image.open(file_path)
            result['metadata']['size'] = img.size
            result['metadata']['format'] = img.format
            result['metadata']['mode'] = img.mode
            
            # Extract text using OCR
            result['content'] = pytesseract.image_to_string(img)
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def _analyze_text(file_path: str) -> Dict[str, Any]:
        """Extract text from plain text file."""
        result = {'content': ''}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                result['content'] = f.read()
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def _extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction based on word frequency
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'do',
                    'does', 'did', 'that', 'this', 'it', 'with', 'by', 'from', 'as', 'if'}
        
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Count occurrences and return top N
        from collections import Counter
        freq = Counter(keywords)
        return [word for word, _ in freq.most_common(top_n)]
    
    @staticmethod
    def _extract_entities(text: str) -> List[Dict[str, str]]:
        """Extract entities like email, phone, amounts, dates."""
        entities = []
        
        # Email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        entities.extend([{'type': 'EMAIL', 'value': e} for e in set(emails)])
        
        # Phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        entities.extend([{'type': 'PHONE', 'value': p} for p in set(phones)])
        
        # Amounts (currency)
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|usd)\b', text, re.IGNORECASE)
        entities.extend([{'type': 'AMOUNT', 'value': a} for a in set(amounts)])
        
        # Dates
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', text, re.IGNORECASE)
        entities.extend([{'type': 'DATE', 'value': d} for d in set(dates)])
        
        return entities


class RAGRetriever:
    """Retrieve relevant information from system knowledge base."""
    
    @staticmethod
    def retrieve_for_query(query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant system components and knowledge for a query.
        Uses semantic similarity and keyword matching.
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w+\b', query_lower))
        
        retrieval_result = {
            'query': query,
            'components': [],
            'documents': [],
            'knowledge': [],
            'workflows': [],
        }
        
        # 1. Retrieve relevant system components
        system_kb = cache.get('system_knowledge_base')
        if not system_kb:
            system_kb = SystemComponentsKnowledgeBase.build_system_knowledge()
        
        # Match models
        for model_name, model_desc in system_kb['components']['models'].items():
            if RAGRetriever._similarity_score(query_terms, model_desc) > 0.3:
                retrieval_result['components'].append({
                    'type': 'Model',
                    'name': model_name,
                    'description': model_desc,
                })
        
        # Match views
        for view_category, views in system_kb['components']['views'].items():
            if isinstance(views, dict):
                for view_name, view_desc in views.items():
                    if RAGRetriever._similarity_score(query_terms, view_desc) > 0.3:
                        retrieval_result['components'].append({
                            'type': 'View',
                            'category': view_category,
                            'name': view_name,
                            'description': view_desc,
                        })
        
        # Match workflows
        for workflow_name, workflow_data in system_kb['workflows'].items():
            if RAGRetriever._similarity_score(query_terms, workflow_name) > 0.4:
                retrieval_result['workflows'].append({
                    'name': workflow_name,
                    'steps': workflow_data.get('steps', []),
                    'participants': workflow_data.get('participants', []),
                })
        
        # 2. Retrieve relevant documents from system
        retrieval_result['documents'] = RAGRetriever._retrieve_documents(query_terms, top_k)
        
        # 3. Retrieve knowledge entries
        retrieval_result['knowledge'] = RAGRetriever._retrieve_knowledge(query_terms, top_k)
        
        return retrieval_result
    
    @staticmethod
    def _similarity_score(query_terms: set, text: str) -> float:
        """Calculate similarity between query terms and text."""
        text_terms = set(re.findall(r'\b\w+\b', text.lower()))
        if not text_terms:
            return 0.0
        
        common_terms = query_terms.intersection(text_terms)
        return len(common_terms) / len(query_terms) if query_terms else 0.0
    
    @staticmethod
    def _retrieve_documents(query_terms: set, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve relevant files/documents."""
        documents = []
        
        try:
            files = File.objects.all()[:100]  # Limit for performance
            
            for f in files:
                title_terms = set(re.findall(r'\b\w+\b', f.title.lower()))
                score = len(query_terms.intersection(title_terms)) / len(query_terms) if query_terms else 0.0
                
                if score > 0.3:
                    documents.append({
                        'type': 'File',
                        'title': f.title,
                        'ref_num': f.ref_num,
                        'category': f.sub_category.name if f.sub_category else 'N/A',
                        'relevance_score': score,
                        'link': f'/view_file_doc/{f.pk}/',
                    })
            
            # Sort by relevance
            documents = sorted(documents, key=lambda x: x['relevance_score'], reverse=True)[:top_k]
        
        except Exception as e:
            pass
        
        return documents
    
    @staticmethod
    def _retrieve_knowledge(query_terms: set, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge entries."""
        knowledge = []
        
        try:
            entries = KnowledgeEntry.objects.all()[:100]
            
            for entry in entries:
                title_terms = set(re.findall(r'\b\w+\b', entry.title.lower()))
                content_terms = set(re.findall(r'\b\w+\b', entry.content.lower()))
                
                combined_terms = title_terms.union(content_terms)
                score = len(query_terms.intersection(combined_terms)) / len(query_terms) if query_terms else 0.0
                
                if score > 0.3:
                    knowledge.append({
                        'type': 'Knowledge',
                        'title': entry.title,
                        'category': entry.category.name if entry.category else 'N/A',
                        'entry_type': entry.entry_type,
                        'relevance_score': score,
                        'link': f'/knowledge/view/{entry.slug}/',
                    })
            
            knowledge = sorted(knowledge, key=lambda x: x['relevance_score'], reverse=True)[:top_k]
        
        except Exception as e:
            pass
        
        return knowledge


class RAGService:
    """Main RAG service combining retrieval and generation."""
    
    @staticmethod
    def query_with_rag(query: str, document_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query system with RAG capability.
        Can include optional documents for context.
        """
        response = {
            'query': query,
            'timestamp': timezone.now().isoformat(),
            'context': {},
            'analysis': {},
        }
        
        # 1. Retrieve relevant information
        response['context'] = RAGRetriever.retrieve_for_query(query, top_k=5)
        
        # 2. Analyze provided documents
        if document_files:
            response['analysis']['documents'] = {}
            for doc_file in document_files:
                if os.path.exists(doc_file):
                    analysis = DocumentAnalyzer.analyze_document(doc_file)
                    response['analysis']['documents'][os.path.basename(doc_file)] = analysis
        
        # 3. Generate comprehensive response
        response['answer'] = RAGService._generate_answer(query, response['context'], response['analysis'])
        
        return response
    
    @staticmethod
    def _generate_answer(query: str, context: Dict, analysis: Dict) -> str:
        """Generate comprehensive answer based on RAG context."""
        answer_parts = []
        
        # Add information about found components
        if context.get('components'):
            answer_parts.append(f"🔧 Found {len(context['components'])} relevant system components:")
            for comp in context['components'][:3]:
                answer_parts.append(f"  • {comp['type']}: {comp.get('name', 'N/A')} - {comp.get('description', 'N/A')[:100]}")
        
        # Add information about found documents
        if context.get('documents'):
            answer_parts.append(f"\n📄 Found {len(context['documents'])} relevant documents:")
            for doc in context['documents'][:3]:
                answer_parts.append(f"  • {doc['title']} ({doc['ref_num']}) - Relevance: {doc['relevance_score']:.0%}")
        
        # Add workflow information
        if context.get('workflows'):
            answer_parts.append(f"\n🔄 Relevant workflows:")
            for wf in context['workflows']:
                answer_parts.append(f"  • {wf['name']}: {' → '.join(wf['steps'][:3])}...")
        
        # Add knowledge
        if context.get('knowledge'):
            answer_parts.append(f"\n💡 Related knowledge:")
            for k in context['knowledge'][:2]:
                answer_parts.append(f"  • {k['title']} ({k['entry_type']})")
        
        # Add document analysis
        if analysis.get('documents'):
            answer_parts.append(f"\n📊 Document Analysis:")
            for doc_name, analysis_data in analysis['documents'].items():
                if 'keywords' in analysis_data:
                    keywords = ', '.join(analysis_data['keywords'][:5])
                    answer_parts.append(f"  • {doc_name}: Keywords: {keywords}")
        
        return '\n'.join(answer_parts) if answer_parts else "No relevant information found in system."
