from datetime import datetime
from random import random
from secrets import choice
from sys import prefix
from unicodedata import category
from django import forms
from django.db.models import Q
from registry import models

from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm, UserChangeForm
from django.contrib.auth.models import User
import datetime

class SaveUser(UserCreationForm):
    username = forms.CharField(max_length=250,help_text="The Username field is required.")
    email = forms.EmailField(max_length=250,help_text="The Email field is required.")
    first_name = forms.CharField(max_length=250,help_text="The First Name field is required.")
    last_name = forms.CharField(max_length=250,help_text="The Last Name field is required.")
    password1 = forms.CharField(max_length=250)
    password2 = forms.CharField(max_length=250)
    platform = forms.ChoiceField(choices=models.UserSecurity.PLATFORMS, help_text="Select your target platform.")
    requested_role = forms.ChoiceField(choices=models.UserSecurity.ROLES, help_text="Requested strategic role.")
    department = forms.ModelChoiceField(queryset=models.Department.objects.all(), required=True, help_text="Select your primary department.")
    job_title = forms.CharField(max_length=100, required=False, help_text="Job Title")
    position = forms.CharField(max_length=100, required=False, help_text="Position")

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'platform', 'requested_role', 'department', 'job_title', 'position')


class GovernanceRegistrationForm(SaveUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict roles to Governance roles
        self.fields['requested_role'].choices = [
            ('Board of Executives', 'Board of Executives'),
            ('HODs', 'Head of Departments'),
            ('Project Management Team', 'Project Management Team'),
            ('Project Leader', 'Project Leader'),
            ('Team Member', 'Project Team Member'),
        ]
        self.fields['platform'].initial = 'Governance'
        self.fields['platform'].required = False
        self.fields['platform'].widget = forms.HiddenInput()
        
        # Ensure departments are loaded
        self.fields['department'].queryset = models.Department.objects.all()

class UpdateProfile(UserChangeForm):
    username = forms.CharField(max_length=250,help_text="The Username field is required.")
    email = forms.EmailField(max_length=250,help_text="The Email field is required.")
    first_name = forms.CharField(max_length=250,help_text="The First Name field is required.")
    last_name = forms.CharField(max_length=250,help_text="The Last Name field is required.")
    current_password = forms.CharField(max_length=250)

    class Meta:
        model = User
        fields = ('email', 'username','first_name', 'last_name')

    def clean_current_password(self):
        if not self.instance.check_password(self.cleaned_data['current_password']):
            raise forms.ValidationError(f"Password is Incorrect")

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail is already exists/taken")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} mail is already exists/taken")

class UpdateUser(UserChangeForm):
    username = forms.CharField(max_length=250,help_text="The Username field is required.")
    email = forms.EmailField(max_length=250,help_text="The Email field is required.")
    first_name = forms.CharField(max_length=250,help_text="The First Name field is required.")
    last_name = forms.CharField(max_length=250,help_text="The Last Name field is required.")

    class Meta:
        model = User
        fields = ('email', 'username','first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(email = email)
        except Exception as e:
            return email
        raise forms.ValidationError(f"The {user.email} mail is already exists/taken")

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.exclude(id=self.cleaned_data['id']).get(username = username)
        except Exception as e:
            return username
        raise forms.ValidationError(f"The {user.username} mail is already exists/taken")

class UpdatePasswords(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Old Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Confirm New Password")
    class Meta:
        model = User
        fields = ('old_password','new_password1', 'new_password2')

class SaveCategory(forms.ModelForm):
    name = forms.CharField(max_length=250)
    description = forms.Textarea()
    status = forms.CharField(max_length=2)

    class Meta:
        model = models.Category
        fields = ('name', 'description', 'status', )

    def clean_name(self):
        id = self.data['id'] if (self.data['id']).isnumeric() else 0
        name = self.cleaned_data['name']
        try:
            if id > 0:
                name = models.Category.objects.exclude(id = id).get(name = name, delete_flag = 0)
            else:
                name = models.Category.objects.get(name = name, delete_flag = 0)
        except:
            return name
        raise forms.ValidationError("Category Name already exists.")

class SaveSubCategory(forms.ModelForm):
    category = forms.CharField(max_length=250)
    name = forms.CharField(max_length=250)
    description = forms.Textarea()
    status = forms.CharField(max_length=2)

    class Meta:
        model = models.SubCategory
        fields = ('category', 'name', 'description', 'status', )

    def clean_category(self):
        cid = int(self.data.get('category')) if str(self.data.get('category', '')).isnumeric() else 0
        try:
            category = models.Category.objects.get(id = cid)
            return category
        except:
            raise forms.ValidationError("Invalid Category.")

    def clean_name(self):
        id = int(self.data.get('id')) if str(self.data.get('id', '')).isnumeric() else 0
        cid = int(self.data.get('category')) if str(self.data.get('category', '')).isnumeric() else 0
        name = self.cleaned_data.get('name')
        try:
            category = models.Category.objects.get(id = cid)
            if id > 0:
                cid = models.SubCategory.objects.exclude(id = id).get(name = name, delete_flag = 0, category = category)
            else:
                cid = models.SubCategory.objects.get(name = name, delete_flag = 0, category = category)
        except:
            return name
        raise forms.ValidationError("Sub-Category Name already exists on the selected Category.")
     
class SaveFile(forms.ModelForm):
    sub_category = forms.CharField(max_length=250)
    ref_num = forms.CharField(max_length=250)
    title = forms.CharField(max_length=250)
    description = forms.Textarea()
    status = forms.CharField(max_length=2)

    class Meta:
        model = models.File
        fields = ('ref_num', 'sub_category', 'title', 'description', 'status', 'file_attachment', )

    def clean_sub_category(self):
        scid = int(self.data.get('sub_category')) if str(self.data.get('sub_category', '')).isnumeric() else 0
        try:
            sub_category = models.SubCategory.objects.get(id = scid)
            return sub_category
        except:
            raise forms.ValidationError("Invalid Sub Category.")

    def clean_ref_num(self):
        id = int(self.data.get('id')) if str(self.data.get('id', '')).isnumeric() else 0
        ref_num = self.cleaned_data.get('ref_num')
        try:
            if id > 0:
                ref_num = models.File.objects.exclude(id = id).get(ref_num = ref_num, delete_flag = 0)
            else:
                ref_num = models.File.objects.get(ref_num = ref_num, delete_flag = 0)
        except:
            return ref_num
        raise forms.ValidationError("Ref Num already exists on the Database.")
  
class SaveBorrower(forms.ModelForm):
    code = forms.CharField(max_length=250)
    first_name = forms.CharField(max_length=250)
    middle_name = forms.CharField(max_length=250, required= False)
    last_name = forms.CharField(max_length=250)
    gender = forms.CharField(max_length=250)
    department = forms.CharField(max_length=250)
    email = forms.EmailField(max_length=250, required=False)
    status = forms.CharField(max_length=2)

    class Meta:
        model = models.Borrower
        fields = ('code', 'first_name', 'middle_name', 'last_name', 'gender', 'department', 'email', 'status',)

    def clean_department(self):
        dept_id = self.data.get('department')
        if str(dept_id).isnumeric():
            try:
                return models.Department.objects.get(id=dept_id)
            except models.Department.DoesNotExist:
                raise forms.ValidationError("Invalid Department selected.")
        return None

    def clean_code(self):
        id = int(self.data.get('id')) if str(self.data.get('id', '')).isnumeric() else 0
        code = self.cleaned_data.get('code')
        try:
            if id > 0:
                code = models.Borrower.objects.exclude(id = id).get(code = code, delete_flag = 0)
            else:
                code = models.Borrower.objects.get(code = code, delete_flag = 0)
        except:
            return code
        raise forms.ValidationError("Borrower Id already exists on the Database.")
    
class SaveBorrow(forms.ModelForm):
    borrower = forms.CharField(max_length=250)
    file_doc = forms.CharField(max_length=250)
    borrowing_date = forms.DateField()
    return_date = forms.DateField()
    folio_ref = forms.CharField(max_length=250)
    status = forms.ChoiceField(choices=models.Borrow.STATUS_CHOICES, required=False)

    class Meta:
        model = models.Borrow
        fields = ('borrower', 'file_doc', 'borrowing_date', 'return_date', 'status','folio_ref', )

    def clean_borrower(self):
        borrower = int(self.data.get('borrower')) if str(self.data.get('borrower', '')).isnumeric() else 0
        try:
            borrower = models.Borrower.objects.get(id = borrower)
            return borrower
        except:
            raise forms.ValidationError("Invalid borrower.")
            
    def clean_file_doc(self):
        file_doc_id = int(self.data.get('file_doc')) if str(self.data.get('file_doc', '')).isnumeric() else 0
        try:
            file_doc = models.File.objects.get(id = file_doc_id)
            # Physical Integrity Check: File must have folios to be borrowed/issued
            if models.Folio.objects.filter(filee=file_doc, delete_flag=0).count() == 0:
                raise forms.ValidationError("Physical Integrity Error: File has no Folios/Components. Please add folios before issuing.")
            return file_doc
        except models.File.DoesNotExist:
            raise forms.ValidationError("Invalid File.")
        

class SaveFolio(forms.ModelForm):
    filee = forms.CharField(max_length=250)
    title = forms.CharField(max_length=250)
    description = forms.Textarea()
    #status = forms.CharField(max_length=2)

    class Meta:
        model = models.Folio
        fields = ('filee', 'title', 'description', )

    def clean_filee(self):
        cid = int(self.data['filee']) if (self.data['filee']).isnumeric() else 0
        try:
            filee = models.File.objects.get(id = cid)
            return filee
        except:
            raise forms.ValidationError("Invalid File.")

    def clean_title(self):
        id = int(self.data['id']) if (self.data['id']).isnumeric() else 0
        fid = int(self.data['filee']) if (self.data['filee']).isnumeric() else 0
        title = self.cleaned_data['title']
        try:
            filee = models.File.objects.get(id = fid)
            if id > 0:
                fid = models.Folio.objects.exclude(id = id).get(title = title, delete_flag = 0, filee = filee)
            else:
                fid = models.Folio.objects.get(title = title, delete_flag = 0, filee = filee)
        except:
            return title
        raise forms.ValidationError("Folio Name already exists on the selected File.")

class LeaveRequestForm(forms.ModelForm):
    approvers = forms.ModelMultipleChoiceField(
        queryset=models.User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'lf-approvers-hidden', 'style': 'display:none;'})
    )

    class Meta:
        model = models.LeaveRequest
        fields = ('leave_type', 'start_date', 'end_date', 'reason', 'supporting_document', 'approvers')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'lf-textarea', 'placeholder': 'Provide a clear reason for your leave request…'}),
            'leave_type': forms.Select(attrs={'class': 'lf-select'}),
            'supporting_document': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.jpg,.png,.jpeg'}),
        }

class RequisitionForm(forms.ModelForm):
    class Meta:
        model = models.Requisition
        fields = ('item_name', 'quantity', 'estimated_unit_cost', 'total_amount', 'budget_line', 'financial_document', 'purpose', )
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'quantity': forms.NumberInput(attrs={'id': 'id_quantity', 'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'estimated_unit_cost': forms.NumberInput(attrs={'id': 'id_unit_cost', 'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'total_amount': forms.NumberInput(attrs={'id': 'id_total_amount', 'class': 'form-control border-0 shadow-sm rounded-pill px-3', 'readonly': 'readonly'}),
            'budget_line': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'financial_document': forms.FileInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control border-0 shadow-sm rounded-3 px-3 py-2'}),
        }

class BudgetForm(forms.ModelForm):
    class Meta:
        model = models.Budget
        fields = ('department', 'fiscal_year', 'total_allocation', )
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'fiscal_year': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3', 'placeholder': 'e.g. 2026'}),
            'total_allocation': forms.NumberInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
        }

class ExpenditureForm(forms.ModelForm):
    class Meta:
        model = models.Expenditure
        fields = ('requisition', 'amount', 'reference_no', 'payment_voucher', )
        widgets = {
            'requisition': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'payment_voucher': forms.FileInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
        }

class MeetingForm(forms.ModelForm):
    class Meta:
        model = models.Meeting
        fields = ('title', 'meeting_date', 'meeting_type', 'location', 'agenda', 'minutes')
        widgets = {
            'meeting_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'title': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'meeting_type': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'location': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'agenda': forms.FileInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'minutes': forms.FileInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
        }

class ResolutionForm(forms.ModelForm):
    class Meta:
        model = models.Resolution
        fields = ('resolution_number', 'description', 'status', 'files', 'assigned_to', 'deadline')
        widgets = {
            'resolution_number': forms.TextInput(attrs={'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control border-0 shadow-sm rounded-3 px-3 py-2'}),
            'status': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'files': forms.SelectMultiple(attrs={'class': 'form-select border-0 shadow-sm rounded-3 select2'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select border-0 shadow-sm rounded-pill'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control border-0 shadow-sm rounded-pill px-3'}),
        }

# --- Procurement & Contract Lifecycle Forms ---

class TenderForm(forms.ModelForm):
    class Meta:
        model = models.Tender
        fields = ('title', 'ref_num', 'description', 'tender_type', 'budget', 'closing_date', 'status', 'department', 'requisition')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'ref_num': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control rounded-3 px-3'}),
            'tender_type': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'closing_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'requisition': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }

class BidForm(forms.ModelForm):
    # ... (existing BidForm fields)
    class Meta:
        model = models.Bid
        fields = ('bidder_name', 'bidder_email', 'amount', 'proposal_doc')
        widgets = {
            'bidder_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'bidder_email': forms.EmailInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'proposal_doc': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

class ContractForm(forms.ModelForm):
    class Meta:
        model = models.Contract
        fields = ('title', 'contract_ref', 'physical_file', 'start_date', 'end_date', 'amount', 'status', 'contract_document')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'contract_ref': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'physical_file': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'contract_document': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

class ContractMilestoneForm(forms.ModelForm):
    class Meta:
        model = models.ContractMilestone
        fields = ('title', 'description', 'due_date', 'completed_date', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'completed_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }

class PerformanceEvaluationForm(forms.ModelForm):
    class Meta:
        model = models.PerformanceEvaluation
        fields = ('score', 'comments')
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1, 'max': 10}),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control rounded-3 px-3'}),
        }

# --- Asset Management Forms ---

class AssetForm(forms.ModelForm):
    class Meta:
        model = models.Asset
        fields = (
            'name', 'category', 'item_type', 'technician_name', 'goods_received_entry', 'contract', 'department', 
            'acquisition_date', 'unit_cost', 'acquisition_cost', 'useful_life', 'status', 'description',
            'quantity_expected', 'quantity_delivered',
            'supplier_name', 'delivery_note_number', 'delivery_note_doc',
            'invoice_number', 'invoice_doc',
            'pmu_source_doc_ref', 'pmu_source_doc'
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Dell Latitude Core i7 Laptops'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'item_type': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_item_type'}),
            'technician_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_technician_name', 'placeholder': 'e.g. SGT KADIKI / INSP NYATHI'}),
            'goods_received_entry': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_goods_received_entry'}),
            'contract': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'acquisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_unit_cost', 'step': '0.01'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_acquisition_cost', 'step': '0.01'}),
            'useful_life': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
            'quantity_expected': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_quantity_expected', 'min': 1, 'placeholder': 'e.g. 25 (per PO)'}),
            'quantity_delivered': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_quantity_delivered', 'min': 1, 'placeholder': 'e.g. 20 (delivered)'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Apex Hardware / TelOne Supplies'}),
            'delivery_note_number': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. DN-2026-8941'}),
            'delivery_note_doc': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. INV-90421'}),
            'invoice_doc': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'pmu_source_doc_ref': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. PMU-PO-4421 / TDR-88'}),
            'pmu_source_doc': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Explicitly make contract link optional
        self.fields['contract'].required = False
        self.fields['contract'].empty_label = "-- None / No Linked Contract (Optional) --"
        if 'technician_name' in self.fields:
            self.fields['technician_name'].required = False
            self.fields['technician_name'].label = "Inspector / Testing Officer"
        if 'goods_received_entry' in self.fields:
            self.fields['goods_received_entry'].required = False
            self.fields['goods_received_entry'].empty_label = "-- Select from Goods Received Ledger (Optional) --"
        if 'quantity_expected' in self.fields:
            self.fields['quantity_expected'].required = False
        if 'quantity_delivered' in self.fields:
            self.fields['quantity_delivered'].required = False

class AssetInspectionForm(forms.ModelForm):
    class Meta:
        model = models.Asset
        fields = (
            'technician_name', 'inspection_status', 'inspection_date', 'inspection_notes',
            'quality_test_passed',
            'approval_doc_1', 'approval_doc_2', 'approval_doc_3'
        )
        widgets = {
            'technician_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'id': 'id_inspection_technician_name', 'placeholder': 'e.g. SGT KADIKI / INSP NYATHI'}),
            'inspection_status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'inspection_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Record all quality, operational, and safety tests conducted before approval...'}),
            'quality_test_passed': forms.CheckboxInput(attrs={'class': 'form-check-input ms-2'}),
            'approval_doc_1': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'approval_doc_2': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'approval_doc_3': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'technician_name' in self.fields:
            self.fields['technician_name'].required = False
            self.fields['technician_name'].label = "Inspector / Testing Officer"
        if 'approval_doc_1' in self.fields:
            self.fields['approval_doc_1'].required = False
        if 'approval_doc_2' in self.fields:
            self.fields['approval_doc_2'].required = False
        if 'approval_doc_3' in self.fields:
            self.fields['approval_doc_3'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tech_name = cleaned_data.get('technician_name')
        if not tech_name:
            # Fallback to instance technician or POST technician ID if passed by API
            if self.instance and self.instance.technician:
                cleaned_data['technician_name'] = self.instance.technician.get_full_name() or self.instance.technician.username
            elif self.data.get('technician'):
                from django.contrib.auth.models import User
                try:
                    u = User.objects.get(pk=int(self.data['technician']))
                    cleaned_data['technician_name'] = u.get_full_name() or u.username
                except (User.DoesNotExist, ValueError):
                    pass
            elif not cleaned_data.get('technician_name'):
                self.add_error('technician_name', 'Inspector / Testing Officer name is required.')
        return cleaned_data

class AssetDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = models.AssetDocument
        fields = ('doc_type', 'title', 'document_file', 'notes')
        widgets = {
            'doc_type': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Document title or scan label'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Any scanner or reference notes...'}),
        }

class AssetMaintenanceForm(forms.ModelForm):
    class Meta:
        model = models.AssetMaintenance
        fields = ('description', 'scheduled_date', 'performed_date', 'cost', 'status', 'performed_by')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'performed_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'performed_by': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

class AssetCustodyForm(forms.ModelForm):
    class Meta:
        model = models.AssetCustody
        fields = ('user', 'issue_date', 'return_date', 'notes')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
        }

# --- Statutory Form 60260-6: Board of Survey Forms ---

class BoardOfSurveyForm(forms.ModelForm):
    class Meta:
        model = models.BoardOfSurvey
        fields = (
            'report_ref', 'held_at', 'proceedings_date', 'department',
            'member_1_name', 'member_1_rank',
            'member_2_name', 'member_2_rank',
            'member_3_name', 'member_3_rank',
            'member_4_name', 'member_4_rank',
            'status'
        )
        widgets = {
            'report_ref': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. BOS-2026-001'}),
            'held_at': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. ZRP ICT Central Stores'}),
            'proceedings_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'member_1_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Presiding Officer / Chairman Name'}),
            'member_1_rank': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank / Designation'}),
            'member_2_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Member 2 Name'}),
            'member_2_rank': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank'}),
            'member_3_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Member 3 Name (Optional)'}),
            'member_3_rank': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank'}),
            'member_4_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Member 4 Name (Optional)'}),
            'member_4_rank': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }

class BoardOfSurveyItemForm(forms.ModelForm):
    class Meta:
        model = models.BoardOfSurveyItem
        fields = (
            'asset', 'description', 'serial_numbers_list', 'quantity', 'value',
            'reason_for_condemning', 'disposal_recommendation', 'disposal_remarks'
        )
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'description': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Description of article'}),
            'serial_numbers_list': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Serial numbers of condemned items (comma separated or per line)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1}),
            'value': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'step': '0.01'}),
            'reason_for_condemning': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Reason for condemning (e.g. Unserviceable, beyond economic repair, obsolete)...'}),
            'disposal_recommendation': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'disposal_remarks': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Additional disposal instructions / remarks'}),
        }


# --- Statutory Z.R.P. FORM 27 Forms ---

class ZrpForm27VoucherForm(forms.ModelForm):
    class Meta:
        model = models.ZrpForm27Voucher
        fields = (
            'voucher_no', 'date', 'issued_by',
            'station', 'station_date', 'requisition_no',
            'how_dispatched', 'checker', 'checker_user', 'checker_date',
            'received_by_user', 'received_by_name', 'received_by_force_no', 'received_date',
            'status',
            # Reverse-side certifications
            'cert_essential_communication', 'cert_member_name', 'cert_member_date',
            'demand_reasons', 'picto_name', 'picto_date_stamp',
            'director_approved', 'director_remarks', 'director_name', 'director_date_stamp',
            'receipt_ledger_certified', 'receiving_ict_officer', 'receiving_date_stamp',
        )
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. 85/26'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'issued_by': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. O.I.C CENTRAL RADIO STORES   (I.C.T)'}),
            'station': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Harare Central Station / Signals Section'}),
            'station_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'requisition_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Station Requisition Reference No.'}),
            'how_dispatched': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Police Vehicle ZRP-1144 / Dispatch Bag'}),
            'checker': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. CST KADIKI (or leave blank if selecting from users)'}),
            'checker_user': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'checker_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'received_by_user': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'received_by_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Full Name of Receiving Officer'}),
            'received_by_force_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank & Force Number'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            # Block (1)
            'cert_essential_communication': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cert_member_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Officer / Member-in-Charge Name & Force No.'}),
            'cert_member_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            # Block (2)
            'demand_reasons': forms.Textarea(attrs={'rows': 3, 'class': 'form-control rounded-3 px-3', 'placeholder': 'State reasons why tools/equipment are demanded...'}),
            'picto_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'PICTO Name & Designation'}),
            'picto_date_stamp': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            # Block (3)
            'director_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'director_remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Director ICT remarks on issue approval...'}),
            'director_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Director ICT Name & Designation'}),
            'director_date_stamp': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            # Block (4)
            'receipt_ledger_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receiving_ict_officer': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Provincial/District ICT Officer Name & Force No.'}),
            'receiving_date_stamp': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
        }


class ZrpForm27ItemForm(forms.ModelForm):
    class Meta:
        model = models.ZrpForm27Item
        fields = ('asset', 'serial_number', 'description', 'stores_use_only', 'quantity', 'remarks')
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'serial_number': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'description': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. HM785 VHF MOBILE RADIO S/N'}),
            'stores_use_only': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Stores reference or Serial number e.g. 26'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1}),
            'remarks': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Remarks / Destination details'}),
        }

class ZrpForm27ReceiveForm(forms.ModelForm):
    class Meta:
        model = models.ZrpForm27Voucher
        fields = ('received_by_user', 'received_by_name', 'received_by_force_no', 'received_date', 'signed_voucher_scan')
        widgets = {
            'received_by_user': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_received_by_user'}),
            'received_by_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Full Name of Receiving Officer'}),
            'received_by_force_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Rank & Force Number (e.g. SGT 044122E)'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'signed_voucher_scan': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'received_by_user' in self.fields:
            self.fields['received_by_user'].required = False
            self.fields['received_by_user'].empty_label = "-- Select Receiving Officer from System Users --"
        if 'received_by_name' in self.fields:
            self.fields['received_by_name'].required = False


# --- Statutory Z.R.P. FORM 216 Forms (Stock / Ledger Card) ---

class ZrpForm216CardForm(forms.ModelForm):
    class Meta:
        model = models.ZrpForm216Card
        fields = (
            'code_no', 'article', 'unit', 'folio_no',
            'department', 'location_bin',
        )
        widgets = {
            'code_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. RAD-VHF-001 or Asset Code'}),
            'article': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. HM785 VHF MOBILE RADIO'}),
            'unit': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Each, No., Set, Box'}),
            'folio_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. FOL-2026/01 or Page No.'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'location_bin': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Central Radio Stores - Shelf B-2'}),
        }


class ZrpForm216EntryForm(forms.ModelForm):
    class Meta:
        model = models.ZrpForm216Entry
        fields = ('date', 'voucher_no', 'from_to', 'receipts', 'issues', 'remarks')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'voucher_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. 85/26 (Form 27), DN-402, GRV-102'}),
            'from_to': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. From Supplier / To Harare Central'}),
            'receipts': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 0, 'value': 0}),
            'issues': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 0, 'value': 0}),
            'remarks': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'Optional transaction notes'}),
        }


class GoodsReceivedEntryForm(forms.ModelForm):
    class Meta:
        model = models.GoodsReceivedEntry
        fields = (
            'entry_no', 'date', 'goods_received', 'company', 'qty', 'bal',
            'po_no', 'bin_no', 'receiver_user', 'checker_user', 'receiver', 'checker', 'remarks',
            'department', 'delivery_note_scan'
        )
        widgets = {
            'entry_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. GR-01/26'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'goods_received': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Desktop Computers & Monitors'}),
            'company': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. C&T COMPUTERS'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1}),
            'bal': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'po_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. ZRP01/23'}),
            'bin_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Rack A-02 / Shelf 3'}),
            'receiver_user': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_gr_receiver_user'}),
            'checker_user': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_gr_checker_user'}),
            'receiver': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. MUMBANYIWA'}),
            'checker': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. MUMBANYIWA'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Condition, serials, or receipt notes...'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'delivery_note_scan': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'entry_no' in self.fields:
            self.fields['entry_no'].required = False
        if 'receiver_user' in self.fields:
            self.fields['receiver_user'].required = False
            self.fields['receiver_user'].empty_label = "-- Select Receiver from System Users (Optional) --"
        if 'checker_user' in self.fields:
            self.fields['checker_user'].required = False
            self.fields['checker_user'].empty_label = "-- Select Checker from System Users (Optional) --"
        if 'receiver' in self.fields:
            self.fields['receiver'].required = True
            self.fields['receiver'].label = "Receiver"
        if 'checker' in self.fields:
            self.fields['checker'].required = True
            self.fields['checker'].label = "Checker"


class IssuesRegisterEntryForm(forms.ModelForm):
    class Meta:
        model = models.IssuesRegisterEntry
        fields = (
            'entry_no', 'date', 'urgency', 'target_date', 'item_description', 'qty', 'requesting_station',
            'station_ref', 'date_requested', 'item_class', 'issuer', 'receiver_user', 'checker_user', 'receiver_details',
            'receiver_signature_image', 'voucher_scan', 'remarks',
            'department', 'linked_asset', 'linked_stock_card', 'linked_form27_voucher'
        )
        widgets = {
            'entry_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 fw-bold font-monospace bg-light', 'placeholder': 'Auto-generated e.g. 01/2026'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'urgency': forms.Select(attrs={'class': 'form-select rounded-pill px-3', 'id': 'id_urgency'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3 bg-light', 'id': 'id_target_date'}),
            'item_description': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Lenovo ThinkPad Core i7 Laptop'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1, 'id': 'id_qty'}),
            'requesting_station': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Harare Central Station / Signals Section'}),
            'station_ref': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. HC/REQ/25/08'}),
            'date_requested': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'item_class': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Class I, Consumable, Radio, ICT'}),
            'issuer': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. CST KADIKI / Storeman Name'}),
            'receiver_user': forms.Select(attrs={'class': 'form-select rounded-pill px-3', 'id': 'id_receiver_user'}),
            'checker_user': forms.Select(attrs={'class': 'form-select rounded-pill px-3', 'id': 'id_checker_user'}),
            'receiver_details': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'No, Rank, Name & Signature of Receiver (e.g. 044122E SGT MUKAMBA T.)'}),
            'receiver_signature_image': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'voucher_scan': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Serial numbers or dispatch remarks...'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'linked_asset': forms.Select(attrs={'class': 'form-select rounded-pill', 'id': 'id_linked_asset'}),
            'linked_stock_card': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'linked_form27_voucher': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entry_no'].required = False
        self.fields['target_date'].required = False
        self.fields['item_description'].required = False
        if 'receiver_user' in self.fields:
            self.fields['receiver_user'].required = False
            self.fields['receiver_user'].empty_label = "-- Select Receiver from System Users (Optional) --"
        if 'checker_user' in self.fields:
            self.fields['checker_user'].required = False
            self.fields['checker_user'].empty_label = "-- Select Checker from System Users (Optional) --"
        if 'receiver_details' in self.fields:
            self.fields['receiver_details'].required = False
            self.fields['receiver_details'].label = "Receiver (No, Rank, Name & Signature)"
        self.fields['qty'].required = False
        self.fields['linked_asset'].required = False
        self.fields['linked_stock_card'].required = False
        self.fields['linked_form27_voucher'].required = False
        self.fields['department'].required = False

    def clean(self):
        cleaned_data = super().clean()
        rec_details = cleaned_data.get('receiver_details')
        rec_user = cleaned_data.get('receiver_user')
        if not rec_details and rec_user:
            cleaned_data['receiver_details'] = f"{rec_user.get_full_name() or rec_user.username} (Received in Good Order)"
        elif not rec_details and not rec_user:
            self.add_error('receiver_details', 'Receiver (No, Rank, Name & Signature) is required.')
        return cleaned_data
        
        # Filter available assets: exclude already issued items and items with 0 stock
        available_assets = models.Asset.objects.exclude(status='Issued').filter(
            Q(quantity_delivered__gt=0) | Q(quantity_delivered__isnull=True)
        ).order_by('category', 'name')
        
        self.fields['linked_asset'].queryset = available_assets
        self.fields['linked_asset'].empty_label = "-- Select from Asset / Inventory Register --"
        self.fields['linked_asset'].label_from_instance = lambda obj: (
            f"{obj.name} ({obj.asset_code}) — Avail: {obj.quantity_delivered or 1} [{obj.get_category_display()}]"
        )


class TenderProcedureEntryForm(forms.ModelForm):
    class Meta:
        model = models.TenderProcedureEntry
        fields = (
            'entry_no', 'date', 'item_description', 'requesting_station',
            'qty', 'total_price', 'ict_ref', 'purchase_order_no', 'remarks',
            'department', 'linked_asset', 'tender_doc_scan'
        )
        widgets = {
            'entry_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. TND-01/26'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded-pill px-3'}),
            'item_description': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Supply & Installation of Solar Backup Systems'}),
            'requesting_station': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. Beitbridge Border Post / Signals Headquarters'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'min': 1}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3', 'step': '0.01', 'placeholder': '0.00'}),
            'ict_ref': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. ICT/TND/2026/08'}),
            'purchase_order_no': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g. PO-ZRP-9921'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Supplier awarded, PRAZ reference, tender notes...'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'linked_asset': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'tender_doc_scan': forms.FileInput(attrs={'class': 'form-control rounded-pill px-3'}),
        }


# --- Institutional Knowledge Vault Forms ---

class KnowledgeEntryForm(forms.ModelForm):
    class Meta:
        model = models.KnowledgeEntry
        fields = ('title', 'entry_type', 'category', 'department', 'physical_file', 'meeting', 'content', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'entry_type': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'physical_file': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'meeting': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control rounded-3 px-3', 'placeholder': 'Enter policy or decision content...'}),
            'status': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }

class KnowledgeCategoryForm(forms.ModelForm):
    class Meta:
        model = models.KnowledgeCategory
        fields = ('name', 'description', 'icon')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
            'icon': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3', 'placeholder': 'e.g., fas fa-book'}),
        }

class KnowledgeRelationForm(forms.ModelForm):
    class Meta:
        model = models.KnowledgeRelation
        fields = ('target', 'relation_type', 'comments')
        widgets = {
            'target': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'relation_type': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'comments': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3'}),
        }

class SaveServiceTicket(forms.ModelForm):
    class Meta:
        model = models.ServiceTicket
        fields = ('department', 'category', 'priority', 'subject', 'description')
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'priority': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'subject': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm', 'placeholder': 'Brief summary of the issue'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control rounded-3 px-3 shadow-sm', 'placeholder': 'Full details of your request...'}),
        }

class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = models.TicketUpdate
        fields = ('comment', 'new_status')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 2, 'class': 'form-control rounded-3 px-3 shadow-sm', 'placeholder': 'Add a comment or resolution details...'}),
            'new_status': forms.Select(choices=models.ServiceTicket.STATUS_CHOICES, attrs={'class': 'form-select rounded-pill shadow-sm'}),
        }

class SaveDigitalCertificate(forms.ModelForm):
    class Meta:
        model = models.DigitalCertificate
        fields = ('certificate_type', 'subject', 'recipient_name', 'content')
        widgets = {
            'certificate_type': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'subject': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control rounded-3 px-3 shadow-sm', 'placeholder': 'Official document content...'}),
        }

class SaveAnnouncement(forms.ModelForm):
    class Meta:
        model = models.Announcement
        fields = ('title', 'content', 'priority', 'department', 'expiry_date')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control rounded-3 px-3 shadow-sm'}),
            'priority': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control rounded-pill px-3 shadow-sm'}),
        }

class BenefitForm(forms.ModelForm):
    class Meta:
        model = models.Benefit
        fields = ('revenue_line', 'monthly_savings', 'projected_year_end', 'annual_projection', 'department')
        widgets = {
            'revenue_line': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'monthly_savings': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'projected_year_end': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'annual_projection': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-3 shadow-sm'}),
            'department': forms.Select(attrs={'class': 'form-select rounded-pill shadow-sm'}),
        }
     