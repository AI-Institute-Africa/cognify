import re
import json
from django.db.models import Q, FloatField, Sum, Count, Avg
from django.db.models.functions import Cast
from django.db.models.fields.json import KeyTransform
from datetime import datetime, timedelta
from django.utils import timezone
from registry.models import (
    Contract, Requisition, Tender, LeaveRequest, File,
    ContractMilestone, ScannedDocument, Asset, KnowledgeEntry,
    Project, ProjectPhase, ProjectTask, Benefit, CostRecovery,
    Department, User, UserSecurity
)


class SystemKnowledgeBase:
    """Comprehensive knowledge base of the RIFTS-X system."""
    
    SYSTEM_OVERVIEW = {
        'name': 'RIFTS-X - Records Intelligence & File Tracking System',
        'core_modules': {
            'Records Management': ['File', 'Folio', 'FileVersion', 'CustodyLog', 'DigitalShare'],
            'Governance': ['Project', 'ProjectPhase', 'ProjectTask', 'Sprint', 'Benefit'],
            'Finance': ['Contract', 'Tender', 'Requisition', 'CostRecovery', 'Budget'],
            'HR & Admin': ['LeaveRequest', 'Asset', 'Department', 'User', 'Organization'],
            'Intelligence': ['ScannedDocument', 'KnowledgeEntry', 'ForensicAudit', 'CloudFile'],
        }
    }
    
    ENTITY_RELATIONSHIPS = {
        'File': {
            'relates_to': ['Department', 'User', 'CustodyLog', 'FileVersion', 'Folio', 'Project'],
            'key_fields': ['ref_num', 'title', 'sub_category', 'sensitivity_level', 'f_status'],
            'description': 'Official records and documents with complete chain-of-custody tracking'
        },
        'Project': {
            'relates_to': ['Department', 'User', 'ProjectPhase', 'Benefit', 'CostRecovery'],
            'key_fields': ['name', 'status', 'owner', 'progress_percentage', 'department'],
            'description': 'Strategic governance projects with phase gates and deliverables'
        },
        'Contract': {
            'relates_to': ['Tender', 'ContractMilestone', 'Vendor', 'Budget'],
            'key_fields': ['title', 'amount', 'status', 'start_date', 'end_date'],
            'description': 'Procurement contracts with milestone tracking and SLA monitoring'
        },
        'User': {
            'relates_to': ['UserSecurity', 'Department', 'Project', 'LeaveRequest'],
            'key_fields': ['username', 'role', 'department', 'platform', 'is_active'],
            'description': 'System users with role-based access and governance permissions'
        }
    }
    
    @staticmethod
    def get_system_stats():
        """Generate system-wide statistics and insights."""
        stats = {
            'total_files': File.objects.count(),
            'total_projects': Project.objects.filter(is_deleted=False).count(),
            'active_projects': Project.objects.filter(is_deleted=False, status='Active').count(),
            'total_contracts': Contract.objects.count(),
            'total_users': User.objects.count(),
            'total_departments': Department.objects.count(),
            'pending_approvals': ProjectPhase.objects.filter(status__icontains='Awaiting').count(),
            'overdue_tasks': ProjectTask.objects.filter(
                status__in=['Pending', 'In Progress', 'To Do'],
                due_date__lt=timezone.now().date()
            ).count(),
        }
        return stats
    
    @staticmethod
    def get_system_health():
        """Assess overall system health."""
        from django.db.models import Q
        
        total_tasks = ProjectTask.objects.filter(is_deleted=False).count()
        completed_tasks = ProjectTask.objects.filter(is_deleted=False, status='Completed').count()
        overdue_tasks = ProjectTask.objects.filter(
            is_deleted=False,
            status__in=['Pending', 'In Progress', 'To Do'],
            due_date__lt=timezone.now().date()
        ).count()
        
        health_score = 100
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            health_score = completion_rate
            if overdue_tasks > 0:
                health_score -= (overdue_tasks / total_tasks) * 20
        
        return {
            'score': max(0, int(health_score)),
            'status': 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'At Risk',
            'total_tasks': total_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks,
        }


class ConversationMemory:
    """Manage multi-turn conversation context."""
    
    def __init__(self):
        self.messages = []
        self.context = {}
        self.entity_focus = None  # Current entity being discussed
    
    def add_message(self, role, content):
        """Add a message to conversation history."""
        self.messages.append({
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': timezone.now().isoformat()
        })
    
    def get_context(self):
        """Get recent context for understanding follow-up questions."""
        return {
            'last_messages': self.messages[-3:] if len(self.messages) > 3 else self.messages,
            'entity_focus': self.entity_focus,
            'context_data': self.context
        }
    
    def set_focus(self, entity_type, entity_id=None):
        """Set the current entity being discussed."""
        self.entity_focus = {'type': entity_type, 'id': entity_id}


class AIAssistantService:

    # ── Status / keyword maps ────────────────────────────────────────────────
    STATUS_MAP = {
        'pending':   ['pending', 'awaiting', 'unprocessed'],
        'approved':  ['approved', 'cleared', 'authorised', 'authorized'],
        'rejected':  ['rejected', 'denied', 'declined'],
        'active':    ['active', 'live', 'current', 'ongoing'],
        'expired':   ['expired', 'lapsed', 'overdue', 'overrun'],
        'completed': ['completed', 'done', 'finished', 'closed'],
    }

    @classmethod
    def _detect_status(cls, text: str):
        """Return canonical status string that matches query words, or None."""
        for canonical, keywords in cls.STATUS_MAP.items():
            if any(kw in text for kw in keywords):
                return canonical
        return None

    @staticmethod
    def parse_query(query_text: str) -> dict:
        query_text = query_text.lower()
        results = {
            'entity': None,
            'filters': {},
            'raw_query': query_text,
            'data': []
        }

        # 1. Identify Entity ─────────────────────────────────────────────────
        if any(w in query_text for w in ['contract', 'procurement', 'tender', 'vendor']):
            results['entity'] = 'Contract'
        elif any(w in query_text for w in ['leave', 'absence', 'sick', 'vacation', 'annual']):
            results['entity'] = 'LeaveRequest'
        elif any(w in query_text for w in ['requisition', 'purchase request', 'purchase order']):
            results['entity'] = 'Requisition'
        elif any(w in query_text for w in ['asset', 'equipment', 'vehicle', 'furniture', 'inventory']):
            results['entity'] = 'Asset'
        elif any(w in query_text for w in ['knowledge', 'policy', 'procedure', 'sop', 'manual', 'guide']):
            results['entity'] = 'Knowledge'
        elif any(w in query_text for w in ['scan', 'ingest', 'incoming', 'ocr']):
            results['entity'] = 'ScannedDocument'
        elif any(w in query_text for w in ['user', 'staff', 'employee', 'personnel', 'account']):
            results['entity'] = 'User'
        elif any(w in query_text for w in ['file', 'document', 'record', 'folio', 'title deed']):
            results['entity'] = 'File'
        else:
            # Broad scan fallback
            results['entity'] = 'ScannedDocument'

        # 2. Extract Year ────────────────────────────────────────────────────
        year_match = re.search(r'\b(20\d{2})\b', query_text)
        if year_match:
            results['filters']['year'] = int(year_match.group(1))

        # 3. Extract Month name  ─────────────────────────────────────────────
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
        }
        for mname, mnum in month_names.items():
            if mname in query_text:
                results['filters']['month'] = mnum
                break

        # 4. Extract Amount ──────────────────────────────────────────────────
        amount_match = re.search(
            r'(above|over|greater than|exceed|>\s*)\$?\s*(\d[\d,]*k?|\d+)', query_text
        )
        if amount_match:
            val_str = amount_match.group(2).replace(',', '')
            if 'k' in val_str:
                amount = float(val_str.replace('k', '')) * 1000
            else:
                amount = float(val_str)
            results['filters']['amount_gt'] = amount

        # Amount below  ──────────────────────────────────────────────────────
        amount_lt_match = re.search(
            r'(below|under|less than|<\s*)\$?\s*(\d[\d,]*k?|\d+)', query_text
        )
        if amount_lt_match:
            val_str = amount_lt_match.group(2).replace(',', '')
            if 'k' in val_str:
                amount = float(val_str.replace('k', '')) * 1000
            else:
                amount = float(val_str)
            results['filters']['amount_lt'] = amount

        # 5. SLA Breach ──────────────────────────────────────────────────────
        if any(w in query_text for w in ['breach', 'sla', 'overdue', 'late', 'delayed', 'overrun']):
            results['filters']['sla_breach'] = True

        # 6. Status filter ───────────────────────────────────────────────────
        detected_status = AIAssistantService._detect_status(query_text)
        if detected_status:
            results['filters']['status'] = detected_status

        # 7. Execute ─────────────────────────────────────────────────────────
        AIAssistantService._execute_search(results)
        
        # 8. Generate summary
        data_count = len(results.get('data', []))
        if data_count > 0:
            entity_name = results.get('entity', 'Item')
            results['summary'] = f"Found {data_count} {entity_name.lower()}(s) matching your query"
        else:
            results['summary'] = f"No results found for '{query_text}'. Try refining your search."
        
        return results

    @staticmethod
    def _execute_search(results):
        entity = results['entity']
        filters = results['filters']

        if entity == 'Contract':
            qs = Contract.objects.all()
            if 'year' in filters:
                qs = qs.filter(date_created__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(date_created__month=filters['month'])
            if 'amount_gt' in filters:
                qs = qs.filter(amount__gt=filters['amount_gt'])
            if 'amount_lt' in filters:
                qs = qs.filter(amount__lt=filters['amount_lt'])
            if filters.get('sla_breach'):
                qs = qs.filter(milestones__status='Overdue').distinct()
            if 'status' in filters:
                # Map canonical → model values
                status_map = {
                    'active': 'Active', 'expired': 'Expired',
                    'completed': 'Completed', 'pending': 'Pending',
                }
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)

            results['data'] = [{
                'title': f"Contract: {obj.title} ({obj.contract_ref})",
                'description': f"Amount: ${obj.amount:,.2f} | Status: {obj.status} | End: {obj.end_date}",
                'link': f"/procurement/contract/view/{obj.pk}/",
                'type': 'Contract',
                'badge': obj.status,
            } for obj in qs[:10]]

        elif entity == 'Requisition':
            qs = Requisition.objects.all()
            if 'year' in filters:
                qs = qs.filter(date_requested__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(date_requested__month=filters['month'])
            if 'amount_gt' in filters:
                qs = qs.filter(total_amount__gt=filters['amount_gt'])
            if 'amount_lt' in filters:
                qs = qs.filter(total_amount__lt=filters['amount_lt'])
            if 'status' in filters:
                status_map = {
                    'pending': 'Pending', 'approved': 'Approved',
                    'rejected': 'Rejected', 'completed': 'Issued',
                }
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)

            results['data'] = [{
                'title': f"Requisition: {obj.item_name} by {obj.requestor.username}",
                'description': f"Total: ${obj.total_amount:,.2f} | Status: {obj.status}",
                'link': f"/all_requisitions",
                'type': 'Requisition',
                'badge': obj.status,
            } for obj in qs[:10]]

        elif entity == 'File':
            qs = File.objects.all()
            
            # Search by query keywords in title or description
            raw_query = results.get('raw_query', '').lower()
            if raw_query and not any(x in raw_query for x in ['file', 'document', 'record']):
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
            if 'month' in filters:
                qs = qs.filter(date_added__month=filters['month'])
            if 'status' in filters:
                status_map = {
                    'active': '1', 'pending': '2', 'completed': '3',
                }
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(f_status=model_status)

            results['data'] = [{
                'title': f"File: {obj.title} ({obj.ref_num})",
                'description': f"Category: {obj.sub_category.name} | Status: {obj.f_status}",
                'link': f"/view_file_doc/{obj.pk}",
                'type': 'File',
                'badge': obj.f_status,
            } for obj in qs[:10]]

        elif entity == 'LeaveRequest':
            qs = LeaveRequest.objects.all()
            if 'year' in filters:
                qs = qs.filter(start_date__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(start_date__month=filters['month'])
            if 'status' in filters:
                status_map = {
                    'pending': 'Pending', 'approved': 'Approved', 'rejected': 'Rejected',
                }
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

        elif entity == 'Asset':
            qs = Asset.objects.all()
            if 'year' in filters:
                qs = qs.filter(acquisition_date__year=filters['year'])
            if 'amount_gt' in filters:
                qs = qs.filter(acquisition_cost__gt=filters['amount_gt'])
            if 'status' in filters:
                status_map = {
                    'active': 'Active', 'expired': 'Disposed',
                    'pending': 'Maintenance',
                }
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

        elif entity == 'Knowledge':
            qs = KnowledgeEntry.objects.all()
            if 'year' in filters:
                qs = qs.filter(date_created__year=filters['year'])
            term = results['raw_query']
            qs = qs.filter(Q(title__icontains=term) | Q(content__icontains=term) | Q(tags__name__icontains=term)).distinct()

            results['data'] = [{
                'title': f"Knowledge: {obj.title}",
                'description': f"Type: {obj.entry_type} | Category: {obj.category.name if obj.category else 'N/A'}",
                'link': f"/knowledge/view/{obj.slug}/",
                'type': 'Knowledge',
                'badge': obj.entry_type,
            } for obj in qs[:10]]

        elif entity == 'ScannedDocument':
            base_qs = ScannedDocument.objects.all()
            qs = base_qs

            if 'year' in filters:
                qs = qs.filter(created_at__year=filters['year'])
            if 'month' in filters:
                qs = qs.filter(created_at__month=filters['month'])

            if 'amount_gt' in filters:
                q_numeric = Q(metadata__extracted_amount__gt=filters['amount_gt'])
                if not qs.filter(q_numeric).exists():
                    try:
                        qs = qs.annotate(
                            amt_val=Cast(KeyTransform('extracted_amount', 'metadata'), FloatField())
                        ).filter(amt_val__gt=filters['amount_gt'])
                    except Exception:
                        qs = qs.filter(q_numeric)
                else:
                    qs = qs.filter(q_numeric)

            if 'status' in filters:
                status_map = {
                    'pending': 'Pending', 'completed': 'Completed',
                    'active': 'Completed', 'rejected': 'Failed',
                }
                model_status = status_map.get(filters['status'])
                if model_status:
                    qs = qs.filter(status=model_status)

            # Final text fallback
            if not qs.exists() or not filters:
                term = results['raw_query']
                qs = base_qs.filter(
                    Q(extracted_text__icontains=term) | Q(classification__icontains=term)
                )
                if not qs.exists() and len(term.split()) > 1:
                    for word in term.split():
                        if len(word) > 4:
                            qs = qs | base_qs.filter(extracted_text__icontains=word)

            results['data'] = [{
                'title': f"Scan #{obj.id}: {obj.classification or 'Document'}",
                'description': (
                    f"Name: {obj.metadata.get('extracted_name', 'N/A')} | "
                    f"Amount: ${obj.metadata.get('extracted_amount', '0')} | "
                    f"Status: {obj.status}"
                ),
                'link': f"/scanner/scans/?id={obj.id}",
                'type': 'Scan',
                'badge': obj.status,
            } for obj in qs.distinct()[:10]]

        elif entity == 'User':
            qs = User.objects.filter(is_active=True)
            if 'status' in filters:
                if filters['status'] == 'inactive':
                    qs = User.objects.filter(is_active=False)
                else:
                    qs = User.objects.filter(is_active=True)

            results['data'] = [{
                'title': f"User: {obj.username}",
                'description': f"Email: {obj.email} | Is Active: {'Yes' if obj.is_active else 'No'}",
                'link': f"/user_profile/{obj.pk}/",
                'type': 'User',
                'badge': 'Active' if obj.is_active else 'Inactive',
            } for obj in qs[:10]]
