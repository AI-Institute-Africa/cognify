from django.test import TestCase
from django.utils import timezone
from .models import Category, SubCategory, File, Borrower, Borrow
import datetime

class RegistryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.sub_category = SubCategory.objects.create(category=self.category, name="Test Sub")
        self.file = File.objects.create(sub_category=self.sub_category, ref_num="REF001", title="Test File")
        self.borrower = Borrower.objects.create(code="B001", first_name="John", last_name="Doe")

    def test_file_creation(self):
        self.assertEqual(str(self.file), "REF001 - Test File")
        self.assertEqual(self.file.f_status, "available")

    def test_borrowing_status_codes(self):
        # Default status should be '0' (Issued)
        borrow = Borrow.objects.create(
            borrower=self.borrower,
            file_doc=self.file,
            borrowing_date=timezone.now().date(),
            return_date=timezone.now().date() + datetime.timedelta(days=7),
            folio_ref="F001"
        )
        self.assertEqual(borrow.status, '0')
        
        # Test updating to Returned
        borrow.status = '1'
        borrow.save()
        self.assertEqual(borrow.status, '1')

    def test_tender_egp_publishing_and_bids(self):
        from registry.models import Tender, Bid, Department
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.create_user(username='tender_user', password='password')
        dept = Department.objects.create(name='Procurement Dept')
        
        # 1. Initiate Tender as Draft
        tender = Tender.objects.create(
            title="Office Supply Tender",
            ref_num="TNDR-0099",
            description="Procuring office stationery",
            tender_type="Open",
            budget=25000.00,
            closing_date=timezone.now() + datetime.timedelta(days=14),
            status="Draft",
            department=dept,
            created_by=user
        )
        
        # Verify it has no bids in Draft state
        self.assertEqual(tender.bids.count(), 0)
        
        # 2. Simulate saving it as Published (calls the logic inside save_tender or views)
        # We can test our save_tender view by POSTing, or we can just mock/call it.
        # Let's call the POST view using the Django test client
        from django.urls import reverse
        self.client.force_login(user)
        response = self.client.post(reverse('save-tender'), {
            'id': tender.id,
            'title': tender.title,
            'ref_num': tender.ref_num,
            'description': tender.description,
            'tender_type': tender.tender_type,
            'budget': tender.budget,
            'closing_date': (tender.closing_date).strftime('%Y-%m-%dT%H:%M'),
            'department': dept.id,
            'status': 'Published'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh tender from DB
        tender.refresh_from_db()
        self.assertEqual(tender.status, 'Published')
        
        # Verify that 4 bids were automatically populated from e-GP simulation
        self.assertEqual(tender.bids.count(), 4)
        
        # Verify properties of the generated bids
        bids = tender.bids.all()
        for bid in bids:
            self.assertEqual(bid.status, 'Pending')
            self.assertGreater(bid.amount, 0)
            self.assertGreater(bid.evaluation_score, 0)

