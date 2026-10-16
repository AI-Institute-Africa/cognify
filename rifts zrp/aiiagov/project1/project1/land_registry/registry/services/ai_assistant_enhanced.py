"""
Enhanced RIFTS-X Intelligence Assistant
ChatGPT/Gemini-like capabilities with system knowledge, context awareness, and intelligent insights
"""

import re
import json
from django.db.models import Q, FloatField, Sum, Count, Avg
from django.db.models.functions import Cast
from django.db.models.fields.json import KeyTransform

# Import RAG system for comprehensive knowledge retrieval
try:
    from .rag_system import RAGService, RAGRetriever, DocumentAnalyzer, SystemComponentsKnowledgeBase
    HAS_RAG = True
except ImportError:
    HAS_RAG = False
from datetime import datetime, timedelta
from django.utils import timezone
from registry.models import (
    Contract, Requisition, Tender, LeaveRequest, File,
    ContractMilestone, ScannedDocument, Asset, KnowledgeEntry,
    Project, ProjectPhase, ProjectTask, Benefit, CostRecovery,
    Department, User, UserSecurity, Folio, FileVersion, CustodyLog
)


class SystemKnowledgeBase:
    """Comprehensive knowledge base of the RIFTS-X system."""
    
    SYSTEM_OVERVIEW = {
        'name': 'RIFTS-X - Records Intelligence & File Tracking System',
        'tagline': 'Enterprise Governance & Records Management Platform',
        'core_modules': {
            'Records Management': {
                'entities': ['File', 'Folio', 'FileVersion', 'CustodyLog', 'DigitalShare'],
                'capabilities': 'Full chain-of-custody tracking, version history, secure access control'
            },
            'Governance': {
                'entities': ['Project', 'ProjectPhase', 'ProjectTask', 'Sprint', 'Benefit'],
                'capabilities': 'Strategic initiatives, phase gates, milestone tracking, benefit realization'
            },
            'Finance': {
                'entities': ['Contract', 'Tender', 'Requisition', 'CostRecovery', 'Budget'],
                'capabilities': 'Procurement management, vendor management, cost tracking, SLA monitoring'
            },
            'HR & Admin': {
                'entities': ['LeaveRequest', 'Asset', 'Department', 'User', 'Organization'],
                'capabilities': 'Employee management, asset tracking, organizational hierarchy'
            },
            'Intelligence': {
                'entities': ['ScannedDocument', 'KnowledgeEntry', 'ForensicAudit', 'CloudFile'],
                'capabilities': 'OCR processing, knowledge management, forensic audit trails'
            },
        }
    }
    
    @staticmethod
    def get_system_stats():
        """Generate system-wide statistics and insights."""
        try:
            stats = {
                'total_files': File.objects.count(),
                'active_files': File.objects.filter(f_status='1').count(),
                'total_projects': Project.objects.filter(is_deleted=False).count(),
                'active_projects': Project.objects.filter(is_deleted=False, status='Active').count(),
                'completed_projects': Project.objects.filter(is_deleted=False, status='Completed').count(),
                'total_contracts': Contract.objects.count(),
                'active_contracts': Contract.objects.filter(status='Active').count(),
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'total_departments': Department.objects.count(),
            }
            return stats
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_system_health():
        """Assess overall system health and identify issues."""
        try:
            from django.db.models import Q, F, FloatField
            from django.db.models.functions import Cast
            
            health_metrics = {}
            
            # Project health
            total_projects = Project.objects.filter(is_deleted=False).count()
            if total_projects > 0:
                completed_projects = Project.objects.filter(is_deleted=False, status='Completed').count()
                health_metrics['project_completion_rate'] = (completed_projects / total_projects) * 100
            
            # Task health
            total_tasks = ProjectTask.objects.filter(is_deleted=False).count()
            if total_tasks > 0:
                completed_tasks = ProjectTask.objects.filter(is_deleted=False, status='Completed').count()
                overdue_tasks = ProjectTask.objects.filter(
                    is_deleted=False,
                    status__in=['Pending', 'In Progress', 'To Do'],
                    due_date__lt=timezone.now().date()
                ).count()
                health_metrics['task_completion_rate'] = (completed_tasks / total_tasks) * 100
                health_metrics['overdue_tasks'] = overdue_tasks
                health_metrics['task_overdue_percentage'] = (overdue_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            # Contract health
            total_contracts = Contract.objects.count()
            if total_contracts > 0:
                breached_milestones = ContractMilestone.objects.filter(status='Overdue').count()
                health_metrics['contract_breach_count'] = breached_milestones
            
            # User activity
            active_users = User.objects.filter(is_active=True).count()
            total_users = User.objects.count()
            if total_users > 0:
                health_metrics['user_activity_rate'] = (active_users / total_users) * 100
            
            # Overall score
            components = []
            if 'project_completion_rate' in health_metrics:
                components.append(health_metrics['project_completion_rate'])
            if 'task_completion_rate' in health_metrics:
                components.append(health_metrics['task_completion_rate'])
            
            overall_score = sum(components) / len(components) if components else 50
            
            # Adjust for problems
            if health_metrics.get('overdue_tasks', 0) > 0:
                overall_score -= health_metrics.get('task_overdue_percentage', 0) * 0.5
            
            overall_score = max(0, min(100, overall_score))
            
            status = 'Excellent' if overall_score >= 80 else 'Good' if overall_score >= 60 else 'Fair' if overall_score >= 40 else 'At Risk'
            
            return {
                'overall_score': int(overall_score),
                'status': status,
                'metrics': health_metrics,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_key_insights():
        """Generate actionable insights from system data."""
        insights = []
        
        try:
            # Find overdue items
            overdue_tasks = ProjectTask.objects.filter(
                is_deleted=False,
                status__in=['Pending', 'In Progress'],
                due_date__lt=timezone.now().date()
            ).count()
            if overdue_tasks > 0:
                insights.append({
                    'type': 'warning',
                    'title': f'{overdue_tasks} Overdue Tasks',
                    'description': 'Multiple tasks are past their due dates. Immediate attention required.'
                })
            
            # Find pending approvals
            pending_phases = ProjectPhase.objects.filter(
                status__icontains='Awaiting'
            ).count()
            if pending_phases > 0:
                insights.append({
                    'type': 'info',
                    'title': f'{pending_phases} Pending Phase Approvals',
                    'description': 'Several project phases are awaiting approval or review.'
                })
            
            # Find contracts nearing expiry
            near_expiry = Contract.objects.filter(
                end_date__lt=timezone.now().date() + timedelta(days=30),
                end_date__gte=timezone.now().date(),
                status='Active'
            ).count()
            if near_expiry > 0:
                insights.append({
                    'type': 'warning',
                    'title': f'{near_expiry} Contracts Expiring Soon',
                    'description': 'Contracts set to expire within 30 days. Plan renewal or extension.'
                })
            
            # Find high-risk files
            sensitive_files = File.objects.filter(sensitivity_level__in=['3', '4']).count()
            if sensitive_files > 0:
                insights.append({
                    'type': 'security',
                    'title': f'{sensitive_files} Highly Sensitive Files',
                    'description': 'Files with high sensitivity levels require enhanced access controls.'
                })
            
        except Exception as e:
            insights.append({
                'type': 'error',
                'title': 'Insight Generation Error',
                'description': f'Could not generate insights: {str(e)}'
            })
        
        return insights


class ConversationMemory:
    """Manage multi-turn conversation context for ChatGPT-like interactions."""
    
    def __init__(self):
        self.messages = []
        self.context = {}
        self.entity_focus = None
        self.search_history = []
    
    def add_message(self, role, content, metadata=None):
        """Add a message to conversation history."""
        self.messages.append({
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'timestamp': timezone.now().isoformat()
        })
        # Keep last 20 messages
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def get_context(self):
        """Get recent context for understanding follow-up questions."""
        return {
            'recent_messages': self.messages[-5:] if len(self.messages) > 5 else self.messages,
            'entity_focus': self.entity_focus,
            'context_data': self.context,
            'search_history': self.search_history[-3:]  # Last 3 searches
        }
    
    def set_focus(self, entity_type, entity_id=None, details=None):
        """Set the current entity being discussed."""
        self.entity_focus = {
            'type': entity_type,
            'id': entity_id,
            'details': details or {}
        }
    
    def add_search(self, query, results_count):
        """Track search history."""
        self.search_history.append({
            'query': query,
            'results': results_count,
            'timestamp': timezone.now().isoformat()
        })
    
    def to_dict(self):
        """Convert conversation to dictionary for storage."""
        return {
            'messages': self.messages,
            'entity_focus': self.entity_focus,
            'search_history': self.search_history
        }


class QueryIntentAnalyzer:
    """Advanced analysis of user query intent."""
    
    INTENT_PATTERNS = {
        'summary': ['summary', 'overview', 'brief', 'what is', 'tell me about', 'explain'],
        'search': ['find', 'show', 'list', 'get', 'retrieve', 'search', 'where is', 'which'],
        'analytics': ['how many', 'count', 'statistics', 'analytics', 'trend', 'analysis', 'report'],
        'comparison': ['compare', 'difference', 'vs', 'versus', 'better', 'worse'],
        'status': ['status', 'progress', 'state', 'condition', 'how is'],
        'recommendation': ['suggest', 'recommend', 'should', 'what should', 'best'],
        'alert': ['alert', 'warning', 'issue', 'problem', 'risk', 'danger'],
    }
    
    @staticmethod
    def detect_intent(query_text):
        """Detect the primary intent of a query."""
        query_lower = query_text.lower()
        intents = []
        
        for intent, keywords in QueryIntentAnalyzer.INTENT_PATTERNS.items():
            if any(kw in query_lower for kw in keywords):
                intents.append(intent)
        
        return intents if intents else ['search']
    
    @staticmethod
    def extract_entities(query_text):
        """Extract entity types and specific IDs from query."""
        entities = {
            'file': r'\b(file|document|record)\b',
            'project': r'\b(project|initiative|program)\b',
            'contract': r'\b(contract|agreement|deal)\b',
            'task': r'\b(task|todo|action item)\b',
            'user': r'\b(user|person|employee|member)\b',
            'department': r'\b(department|team|division)\b',
        }
        
        found = {}
        for entity_type, pattern in entities.items():
            if re.search(pattern, query_text, re.IGNORECASE):
                found[entity_type] = True
        
        return found


class EnhancedAIAssistantService:
    """
    Enhanced AI Assistant Service with ChatGPT/Gemini-like capabilities
    - Natural language understanding
    - Multi-turn conversation support
    - System insights and analytics
    - Intelligent recommendations
    """
    
    STATUS_MAP = {
        'pending': ['pending', 'awaiting', 'unprocessed', 'waiting'],
        'approved': ['approved', 'cleared', 'authorised', 'authorized', 'ok'],
        'rejected': ['rejected', 'denied', 'declined', 'no'],
        'active': ['active', 'live', 'current', 'ongoing', 'running'],
        'expired': ['expired', 'lapsed', 'overdue', 'overrun', 'past'],
        'completed': ['completed', 'done', 'finished', 'closed', 'final'],
    }
    
    @staticmethod
    def process_intelligent_query(query_text, conversation_memory=None):
        """
        Process query with intelligent multi-step analysis.
        Returns conversational response with insights.
        """
        
        if conversation_memory is None:
            conversation_memory = ConversationMemory()
        
        # 1. Detect intent
        intents = QueryIntentAnalyzer.detect_intent(query_text)
        
        # 2. Extract entities
        entities = QueryIntentAnalyzer.extract_entities(query_text)
        
        # 3. Perform contextual search
        results = EnhancedAIAssistantService.parse_query(query_text)
        
        # 4. Generate intelligent response
        response = EnhancedAIAssistantService.generate_response(
            query_text, 
            intents, 
            entities, 
            results,
            conversation_memory
        )
        
        # 5. Add insights if appropriate
        if 'analytics' in intents or 'summary' in intents:
            insights = SystemKnowledgeBase.get_key_insights()
            response['insights'] = insights
        
        # 6. Store in memory
        conversation_memory.add_message('user', query_text, {'intents': intents, 'entities': entities})
        conversation_memory.add_message('assistant', response['summary'])
        
        return response
    
    @staticmethod
    def generate_response(query_text, intents, entities, search_results, memory):
        """Generate conversational response with context."""
        
        response = {
            'summary': '',
            'details': [],
            'recommendations': [],
            'follow_up_questions': [],
            'data': search_results.get('data', [])
        }
        
        # Generate summary based on intent
        if 'summary' in intents or 'alert' in intents:
            health = SystemKnowledgeBase.get_system_health()
            response['summary'] = f"System Status: {health.get('status', 'Unknown')} " \
                                f"(Score: {health.get('overall_score', 'N/A')}/100)"
            
            insights = SystemKnowledgeBase.get_key_insights()
            if insights:
                response['summary'] += f"\n\nKey Issues: {len(insights)} item(s) need attention"
                response['details'] = [f"• {i['title']}: {i['description']}" for i in insights[:3]]
        
        elif 'analytics' in intents:
            stats = SystemKnowledgeBase.get_system_stats()
            response['summary'] = f"System Analytics: {stats.get('active_projects', 0)} active projects, " \
                                f"{stats.get('active_files', 0)} active files, " \
                                f"{stats.get('active_users', 0)}/{stats.get('total_users', 0)} users online"
        
        else:
            # Default search response
            data_count = len(search_results.get('data', []))
            if data_count > 0:
                response['summary'] = f"Found {data_count} result(s) matching your query"
                # Show snippets
                for item in search_results.get('data', [])[:3]:
                    response['details'].append(f"• {item['title']}: {item['description']}")
            else:
                response['summary'] = "No exact matches found. Try refining your search or ask about system status."
        
        # Add recommendations
        if 'recommendation' in intents:
            health = SystemKnowledgeBase.get_system_health()
            if health.get('overall_score', 100) < 60:
                response['recommendations'].append("Focus on completing overdue tasks to improve system health")
            response['recommendations'].append("Review security settings for sensitive files regularly")
        
        # Add follow-up questions
        response['follow_up_questions'] = [
            "Would you like to drill down into a specific result?",
            "Need help with related information?",
            "Can I help you with anything else about the system?"
        ]
        
        return response
    
    @staticmethod
    def parse_query(query_text: str) -> dict:
        """Parse natural language query into structured search parameters."""
        results = {
            'raw_query': query_text,
            'entity': None,
            'filters': {},
            'data': []
        }
        
        query_lower = query_text.lower()
        
        # 1. Entity Detection
        entity_patterns = {
            'Contract': r'\b(contract|contracts|agreement|agreements|deal|deals|procurement)\b',
            'Requisition': r'\b(requisition|requisitions|request|order|purchase)\b',
            'User': r'\b(user|users|staff|employee|personnel|account|accounts)\b',
            'File': r'\b(file|files|document|documents|record|records)\b',
            'LeaveRequest': r'\b(leave|vacation|timeoff|time off|absence)\b',
            'Asset': r'\b(asset|assets|equipment|inventory)\b',
            'Knowledge': r'\b(knowledge|info|information|guide|tutorial|howto)\b',
            'ScannedDocument': r'\b(scanned|scan|document|pdf|image|archive)\b',
            'Project': r'\b(project|projects|initiative|program|strategic)\b',
        }
        
        for entity, pattern in entity_patterns.items():
            if re.search(pattern, query_lower):
                results['entity'] = entity
                break
        
        if not results['entity']:
            results['entity'] = 'File'  # Default
        
        # 2. Year/Date extraction
        year_match = re.search(r'\b(20\d{2})\b', query_text)
        if year_match:
            results['filters']['year'] = int(year_match.group(1))
        
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december']
        for i, month in enumerate(months, 1):
            if month in query_lower:
                results['filters']['month'] = i
                break
        
        # 3. Amount extraction
        amount_patterns = [
            (r'above\s*\$?([\d,]+)', 'amount_gt'),
            (r'below\s*\$?([\d,]+)', 'amount_lt'),
            (r'more than\s*\$?([\d,]+)', 'amount_gt'),
            (r'less than\s*\$?([\d,]+)', 'amount_lt'),
        ]
        
        for pattern, filter_name in amount_patterns:
            match = re.search(pattern, query_lower)
            if match:
                amount = int(match.group(1).replace(',', ''))
                results['filters'][filter_name] = amount
        
        # 4. SLA/Breach detection
        if any(w in query_lower for w in ['breach', 'sla', 'overdue', 'late', 'delayed', 'overrun']):
            results['filters']['sla_breach'] = True
        
        # 5. Status filter
        detected_status = EnhancedAIAssistantService._detect_status(query_text)
        if detected_status:
            results['filters']['status'] = detected_status
        
        # 6. Execute search
        EnhancedAIAssistantService._execute_search(results)
        
        # 7. Generate summary
        data_count = len(results.get('data', []))
        if data_count > 0:
            entity_name = results.get('entity', 'Item')
            results['summary'] = f"Found {data_count} {entity_name.lower()}(s) matching your query"
        else:
            results['summary'] = f"No results found for '{query_text}'. Try refining your search."
        
        return results
    
    @staticmethod
    def _detect_status(text: str):
        """Map natural language status to canonical values."""
        text_lower = text.lower()
        for canonical, keywords in EnhancedAIAssistantService.STATUS_MAP.items():
            if any(kw in text_lower for kw in keywords):
                return canonical
        return None
    
    @staticmethod
    def _execute_search(results):
        """Execute database queries based on parsed parameters."""
        entity = results['entity']
        filters = results['filters']
        
        if entity == 'Contract':
            qs = Contract.objects.all()
            if 'year' in filters:
                qs = qs.filter(date_created__year=filters['year'])
            if 'status' in filters:
                status_map = {'active': 'Active', 'expired': 'Expired', 'completed': 'Completed'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)
            
            results['data'] = [{
                'title': f"Contract: {obj.title} ({obj.contract_ref})",
                'description': f"Amount: ${obj.amount:,.2f} | Status: {obj.status}",
                'link': f"/procurement/contract/view/{obj.pk}/",
                'type': 'Contract',
                'badge': obj.status,
            } for obj in qs[:10]]
        
        elif entity == 'Project':
            qs = Project.objects.filter(is_deleted=False)
            if 'year' in filters:
                qs = qs.filter(date_created__year=filters['year'])
            if 'status' in filters:
                status_map = {'active': 'Active', 'completed': 'Completed', 'pending': 'Pending'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)
            
            results['data'] = [{
                'title': f"Project: {obj.name}",
                'description': f"Owner: {obj.owner.username if obj.owner else 'N/A'} | "
                               f"Progress: {obj.progress_percentage}% | Status: {obj.status}",
                'link': f"/view_project/{obj.pk}/",
                'type': 'Project',
                'badge': obj.status,
            } for obj in qs[:10]]
        
        elif entity == 'File':
            qs = File.objects.all()
            
            # Search by query keywords in title or description
            raw_query = results.get('raw_query', '').lower()
            if raw_query and not any(x in raw_query for x in ['file', 'document', 'record', 'list all']):
                # If query is not just asking for "files", search for the term in title
                query_terms = raw_query.split()
                query_filter = Q()
                for term in query_terms:
                    if len(term) > 2:  # Only search terms longer than 2 chars
                        query_filter |= Q(title__icontains=term) | Q(ref_num__icontains=term)
                if query_filter:
                    qs = qs.filter(query_filter)
            
            if 'year' in filters:
                qs = qs.filter(date_added__year=filters['year'])
            if 'status' in filters:
                status_map = {'active': '1', 'pending': '2', 'completed': '3'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(f_status=model_status)
            
            results['data'] = [{
                'title': f"File: {obj.title} ({obj.ref_num})",
                'description': f"Category: {obj.sub_category.name if obj.sub_category else 'N/A'} | Sensitivity: {obj.sensitivity_level}",
                'link': f"/view_file_doc/{obj.pk}",
                'type': 'File',
                'badge': obj.f_status,
            } for obj in qs[:10]]
        
        elif entity == 'User':
            qs = User.objects.filter(is_active=True)
            if 'status' in filters:
                if filters['status'] == 'inactive':
                    qs = User.objects.filter(is_active=False)
                else:
                    qs = User.objects.filter(is_active=True)
            
            results['data'] = [{
                'title': f"User: {obj.username}",
                'description': f"Email: {obj.email} | Active: {'Yes' if obj.is_active else 'No'}",
                'link': f"/user_profile/{obj.pk}/",
                'type': 'User',
                'badge': 'Active' if obj.is_active else 'Inactive',
            } for obj in qs[:10]]
        
        elif entity == 'LeaveRequest':
            qs = LeaveRequest.objects.all()
            if 'year' in filters:
                qs = qs.filter(start_date__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(start_date__month=filters['month'])
            if 'status' in filters:
                status_map = {'pending': 'Pending', 'approved': 'Approved', 'rejected': 'Rejected'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)
            
            results['data'] = [{
                'title': f"Leave: {obj.user.username} – {obj.leave_type}",
                'description': f"From {obj.start_date} to {obj.end_date} | Status: {obj.status}",
                'link': f"/leave_applications",
                'type': 'Leave',
                'badge': obj.status,
            } for obj in qs[:10]]
        
        elif entity == 'Requisition':
            qs = Requisition.objects.all()
            if 'year' in filters:
                qs = qs.filter(date_requested__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(date_requested__month=filters['month'])
            if 'status' in filters:
                status_map = {'pending': 'Pending', 'approved': 'Approved', 'rejected': 'Rejected', 'completed': 'Issued'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)
            
            results['data'] = [{
                'title': f"Requisition: {obj.item_name}",
                'description': f"Total: ${obj.total_amount:,.2f} | Status: {obj.status}",
                'link': f"/all_requisitions",
                'type': 'Requisition',
                'badge': obj.status,
            } for obj in qs[:10]]
        
        elif entity == 'Asset':
            qs = Asset.objects.all()
            if 'year' in filters:
                qs = qs.filter(acquisition_date__year=filters['year'])
            if 'status' in filters:
                status_map = {'active': 'Active', 'expired': 'Disposed', 'pending': 'Maintenance'}
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)
            
            results['data'] = [{
                'title': f"Asset: {obj.asset_code} – {obj.name}",
                'description': f"Category: {obj.category} | Cost: ${obj.acquisition_cost:,.2f} | Status: {obj.status}",
                'link': f"/assets/",
                'type': 'Asset',
                'badge': obj.status,
            } for obj in qs[:10]]
        
        # Add more entity types as needed...
    
    @staticmethod
    def query_with_rag(query_text: str, document_files: list = None) -> dict:
        """
        Enhanced query with RAG (Retrieval-Augmented Generation).
        Retrieves relevant system components, documents, and knowledge.
        """
        if not HAS_RAG:
            # Fallback to basic parse_query if RAG not available
            return EnhancedAIAssistantService.parse_query(query_text)
        
        # Use RAG service to get comprehensive results
        rag_result = RAGService.query_with_rag(query_text, document_files)
        
        # Convert RAG result to compatible format
        return {
            'raw_query': query_text,
            'entity': 'RAG',
            'filters': {},
            'data': EnhancedAIAssistantService._format_rag_results(rag_result),
            'summary': rag_result['answer'],
            'rag_context': rag_result['context'],
            'rag_analysis': rag_result.get('analysis', {}),
        }
    
    @staticmethod
    def _format_rag_results(rag_result: dict) -> list:
        """Format RAG results into data items."""
        items = []
        context = rag_result.get('context', {})
        
        # Add components
        for comp in context.get('components', [])[:3]:
            items.append({
                'title': f"Component: {comp.get('type')} - {comp.get('name', 'N/A')}",
                'description': comp.get('description', 'N/A')[:100],
                'type': 'Component',
                'badge': comp.get('type'),
            })
        
        # Add documents
        for doc in context.get('documents', [])[:3]:
            items.append({
                'title': f"File: {doc['title']}",
                'description': f"Category: {doc['category']} | Relevance: {doc['relevance_score']:.0%}",
                'type': 'File',
                'badge': doc['ref_num'],
                'link': doc.get('link'),
            })
        
        # Add knowledge
        for k in context.get('knowledge', [])[:3]:
            items.append({
                'title': f"Knowledge: {k['title']}",
                'description': f"Type: {k['entry_type']} | Category: {k['category']}",
                'type': 'Knowledge',
                'badge': k['entry_type'],
                'link': k.get('link'),
            })
        
        return items
