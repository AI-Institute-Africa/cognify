from django.contrib import admin
from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    #path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    #path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 
    
    path('',views.home, name="home-page"),
    path('login',views.login_page,name='login-page'),
    path('register',views.userregister,name='register-page'),
    path('governance/register', views.governance_register, name='governance-register'),
    path('save_register',views.save_register,name='register-user'),
    path('save_governance_register', views.save_governance_register, name='save-governance-register'),
    path('user_login',views.login_user,name='login-user'),
    path('verify_mfa',views.verify_mfa,name='verify-mfa'),
    path('verify_login_otp', views.verify_mfa, name='verify-login-otp'),
    path('verify-email/<str:token>', views.verify_email, name='verify-email'),
    path('resend-verification', views.resend_verification, name='resend-verification'),
    path('governance/pm/members/', views.pm_manage_members, name='pm-manage-members'),
    path('governance/pm/members/action/', views.pm_member_action, name='pm-member-action'),
    path('home',views.home,name='home-page'),
    path('dashboard/md', views.dashboard_md, name='dashboard-md'),
    path('dashboard/hod', views.dashboard_hod, name='dashboard-hod'),
    path('dashboard/pm', views.dashboard_pm, name='dashboard-pm'),
    path('dashboard/member', views.dashboard_member, name='dashboard-member'),
    path('governance/users/', views.manage_users, name='manage-users'),
    path('governance/users/action/', views.user_role_action, name='user-role-action'),
    

    path('logout',views.logout_user,name='logout'),
    path('profile',views.profile,name='profile-page'),
    path('update_password',views.update_password,name='update-password'),
    path('update_profile',views.update_profile,name='update-profile'),
    path('users',views.users,name='user-page'),
    path('manage_user',views.manage_user,name='manage-user'),
    path('manage_user/<int:pk>',views.manage_user,name='manage-user-pk'),
    path('save_user',views.save_user,name='save-user'),
    path('delete_user/<int:pk>',views.delete_user,name='delete-user'),
    path('category',views.category,name='category-page'),
    path('manage_category',views.manage_category,name='manage-category'),
    path('manage_category/<int:pk>',views.manage_category,name='manage-category-pk'),
    path('view_category/<int:pk>',views.view_category,name='view-category-pk'),
    path('save_category',views.save_category,name='save-category'),
    path('delete_category/<int:pk>',views.delete_category,name='delete-category'),
    path('sub_category',views.sub_category,name='sub_category-page'),
    path('manage_sub_category',views.manage_sub_category,name='manage-sub_category'),
    path('manage_sub_category/<int:pk>',views.manage_sub_category,name='manage-sub_category-pk'),
    path('view_sub_category/<int:pk>',views.view_sub_category,name='view-sub_category-pk'),
    path('save_sub_category',views.save_sub_category,name='save-sub_category'),
    path('delete_sub_category/<int:pk>',views.delete_sub_category,name='delete-sub_category'),
    path('files/',views.files,name='file_doc-page'),
    path('manage_file_doc',views.manage_file_doc,name='manage-file_doc'),
    path('manage_file_doc/<int:pk>',views.manage_file_doc,name='manage-file_doc-pk'),
    path('view_file_doc/<int:pk>',views.view_file_doc,name='view-file_doc-pk'),
    path('save_file_doc',views.save_file_doc,name='save-file_doc'),
    path('delete_file_doc/<int:pk>',views.delete_file_doc,name='delete-file_doc'),
    path('download_version/<int:pk>',views.download_version,name='secure-download'),
    path('borrower',views.borrower,name='borrower-page'),
    path('manage_borrower',views.manage_borrower,name='manage-borrower'),
    path('manage_borrower/<int:pk>',views.manage_borrower,name='manage-borrower-pk'),
    path('view_borrower/<int:pk>',views.view_borrower,name='view-borrower-pk'),
    path('save_borrower',views.save_borrower,name='save-borrower'),
    path('delete_borrower/<int:pk>',views.delete_borrower,name='delete-borrower'),
    path('borrows',views.borrows,name='borrow-page'),
    
    
    path('manage_borrow',views.manage_borrow,name='manage-borrow'),
    path('manage_borrow/<int:pk>',views.manage_borrow,name='manage-borrow-pk'),
    path('view_borrow/<int:pk>',views.view_borrow,name='view-borrow-pk'),
    path('save_borrow',views.save_borrow,name='save-borrow'),
    path('delete_borrow/<int:pk>',views.delete_borrow,name='delete-borrow'),
    path('folio',views.folio,name='folio-page'),
    path('manage_folio',views.manage_folio,name='manage-folio'),
    path('manage_folio/<int:pk>',views.manage_folio,name='manage-folio-pk'),
    path('view_folio/<int:pk>',views.view_folio,name='view-folio-pk'),
    path('save_folio',views.save_folio,name='save-folio'),
    path('delete_folio/<int:pk>',views.delete_folio,name='delete-folio'),
    path('departments',views.departments,name='department-page'),
    path('manage_department',views.manage_department,name='manage-department'),
    path('manage_department/<int:pk>',views.manage_department,name='manage-department-pk'),
    path('save_department',views.save_department,name='save-department'),
    path('delete_department/<int:pk>',views.delete_department,name='delete-department'),
    
    # RIFTS-X Antigravity Module 12
    path('secure_link/generate/<int:pk>', views.generate_secure_link, name='generate-secure-link'),
    path('secure_link/verify/<str:token>', views.verify_secure_link, name='verify-secure-link'),
    path('overdue_count', views.get_overdue_count, name='overdue-count'),
    
    # Digital Sharing and Tracking
    path('share_file_digital/<int:pk>', views.share_file_digital, name='share-file-digital'),
    path('verify_digital_share/<str:token>', views.verify_digital_share, name='verify-digital-share'),
    path('return_digital_share/<str:token>', views.return_digital_share, name='return-digital-share'),
    path('file_timeline/<int:pk>/', views.file_timeline, name='file-timeline'),
    path('handover_file/', views.handover_file, name='handover-file'),
    path('transfer_file/', views.transfer_file, name='transfer-file'),
    path('handover_modal/', views.handover_modal, name='handover-modal'),
    path('transfer_modal/', views.transfer_modal, name='transfer-modal'),
    path('executive_dashboard/', views.executive_dashboard, name='executive-dashboard'),
    path('forensic_audit/<int:pk>/', views.forensic_audit_export, name='forensic-audit'),
    path('audit_highlights/<int:pk>', views.get_audit_highlights, name='audit-highlights'),
    path('download_bundle/<str:token>', views.download_file_bundle, name='download-file-bundle'),
    
    # Recipient Dashboard
    path('my_dashboard', views.recipient_dashboard, name='recipient-dashboard'),
    path('submit_modification', views.submit_modification, name='submit-modification'),
    path('access/<str:token>', views.access_with_token, name='access-with-token'),
    path('borrow_folder/<int:pk>/', views.borrow_folder_view, name='borrow-folder-view'),
    path('edit_issued_file/<int:borrow_id>/<int:file_id>/', views.edit_issued_file, name='edit-issued-file'),
    path('save_issued_file_edit/', views.save_issued_file_edit, name='save-issued-file-edit'),
    path('onlyoffice/config/<int:borrow_id>/<int:file_id>/', views.get_onlyoffice_document_config, name='get-onlyoffice-config'),
    path('onlyoffice/file/<int:borrow_id>/<int:file_id>/', views.get_onlyoffice_file, name='get-onlyoffice-file'),
    path('onlyoffice/callback/<int:borrow_id>/<int:file_id>/', views.onlyoffice_callback, name='onlyoffice-callback'),
    path('confirm_borrow_return/<int:borrow_id>/', views.confirm_borrow_return, name='confirm-borrow-return'),
    path('download_issued_folder/<int:pk>/', views.download_issued_folder_zip, name='download-issued-folder'),
    path('acknowledge_transfer/<int:pk>', views.acknowledge_transfer, name='acknowledge-transfer'),
    
    # Staff Leave & Requisitions
    path('leaves', views.leave_list, name='leave-list'),
    path('manage_leave', views.manage_leave, name='manage-leave'),
    path('save_leave', views.save_leave, name='save-leave'),
    path('leave_applications', views.leave_applications, name='leave-applications'),
    path('approve_leave', views.approve_leave, name='approve-leave'),
    path('leave/<int:pk>/sign-visual/', views.leave_sign_visual, name='leave-sign-visual'),
    path('leave/<int:pk>/view/', views.leave_view, name='leave-view'),
    path('approvers/directory/', views.approver_directory, name='approver-directory'),
    path('profile/signature/', views.manage_signature, name='manage-signature'),
    path('leave/verify/<str:token>/', views.verify_leave_approval, name='verify-leave-approval'),
    
    path('requisitions', views.requisition_list, name='requisition-list'),
    path('manage_requisition', views.manage_requisition, name='manage-requisition'),
    path('save_requisition', views.save_requisition, name='save-requisition'),
    path('all_requisitions', views.all_requisitions, name='all-requisitions'),
    path('approve_requisition', views.approve_requisition, name='approve-requisition'),

    # Enhanced Supply Requisitions
    path('supply_requisitions/', views.supply_requisition_list, name='supply-requisition-list'),
    path('supply_requisition/create/', views.manage_supply_requisition, name='supply-requisition-create'),
    path('supply_requisition/<int:pk>/', views.view_supply_requisition, name='supply-requisition-view'),
    path('supply_requisition/save/', views.save_supply_requisition, name='supply-requisition-save'),
    path('supply_requisition/<int:pk>/sign/<str:stage>/', views.sign_supply_requisition, name='supply-requisition-sign'),
    path('supply_requisition/<int:pk>/signatories/', views.supply_requisition_signatories, name='supply-requisition-signatories'),
    path('supply_requisition/<int:pk>/pdf/', views.download_supply_requisition_pdf, name='supply-requisition-pdf'),
    # Plural-form aliases (in case email links or manual navigation uses plural)
    path('supply_requisitions/<int:pk>/', views.view_supply_requisition, name='supply-requisition-view-alt'),
    path('supply_requisitions/<int:pk>/sign/<str:stage>/', views.sign_supply_requisition, name='supply-requisition-sign-alt'),
    path('supply_requisitions/<int:pk>/signatories/', views.supply_requisition_signatories, name='supply-requisition-signatories-alt'),

    # Role-based Dashboards
    path('dashboard/dept_manager/', views.dashboard_dept_manager, name='dashboard-dept-manager'),
    path('dashboard/ceo/', views.dashboard_ceo, name='dashboard-ceo'),
    path('dashboard/purchasing_officer/', views.dashboard_purchasing_officer, name='dashboard-purchasing-officer'),
    path('dashboard/finance_officer/', views.dashboard_finance_officer, name='dashboard-finance-officer'),



    # Meeting & Resolution Tracking
    path('meetings', views.meeting_list, name='meeting-list'),
    path('manage_meeting', views.manage_meeting, name='manage-meeting'),
    path('manage_meeting/<int:id>', views.manage_meeting, name='manage-meeting-id'),
    path('save_meeting', views.save_meeting, name='save-meeting'),
    path('view_meeting/<int:id>', views.view_meeting, name='view-meeting'),
    path('manage_resolution/<int:meeting_id>', views.manage_resolution, name='manage-resolution'),
    path('manage_resolution/<int:meeting_id>/<int:id>', views.manage_resolution, name='manage-resolution-id'),
    path('save_resolution', views.save_resolution, name='save-resolution'),
    path('update_resolution_status', views.update_resolution_status, name='update-resolution-status'),

    # Meeting Minutes Recorder
    path('record_minutes/<int:meeting_id>', views.record_minutes, name='record-minutes'),
    path('save_minutes_text/<int:meeting_id>', views.save_minutes_text, name='save-minutes-text'),
    path('download_minutes_pdf/<int:meeting_id>', views.download_minutes_pdf, name='download-minutes-pdf'),

    # Procurement & Contracts
    path('procurement/', views.tender_list, name='procurement-hub'),
    path('procurement', views.tender_list),
    path('procurement/tenders/', views.tender_list, name='tender-list'),
    path('procurement/tender/manage/', views.manage_tender, name='manage-tender'),
    path('procurement/tender/manage/<int:pk>/', views.manage_tender, name='manage-tender-pk'),
    path('procurement/tender/save/', views.save_tender, name='save-tender'),
    path('procurement/tender/view/<int:pk>/', views.view_tender, name='view-tender-pk'),
    path('procurement/tender/<int:tender_id>/bids/', views.bid_list, name='bid_list'),
    path('procurement/bid/manage/<int:tender_pk>/', views.manage_bid, name='manage-bid-tender'),
    path('procurement/bid/manage/<int:tender_pk>/<int:pk>/', views.manage_bid, name='manage-bid-pk'),
    path('procurement/bid/save/', views.save_bid, name='save-bid'),
    path('procurement/bid/award/<int:pk>/', views.award_bid, name='award-bid'),
    # ── e-GP Portal Direct Communication ──────────────────────────────────
    path('procurement/tender/<int:pk>/egp-sync/', views.egp_tender_sync, name='egp-tender-sync'),
    path('procurement/egp/test-connection/', views.egp_test_connection, name='egp-test-connection'),
    path('procurement/contracts/', views.contract_list, name='contract-list'),
    path('procurement/contract/view/<int:pk>/', views.view_contract, name='view-contract-pk'),
    path('procurement/contract/milestone/save/', views.save_milestone, name='save-milestone'),
    path('procurement/contract/performance/save/', views.save_performance, name='save-performance'),

    # Asset & Inventory
    path('assets/', views.asset_list, name='asset-list'),
    path('assets/manage/', views.manage_asset, name='manage-asset'),
    path('assets/manage/<int:pk>/', views.manage_asset, name='manage-asset-pk'),
    path('assets/save/', views.save_asset, name='save-asset'),
    path('assets/view/<int:pk>/', views.view_asset, name='view-asset-pk'),
    path('assets/maintenance/save/', views.save_asset_maintenance, name='save-asset-maintenance'),
    path('assets/custody/save/', views.save_asset_custody, name='save-asset-custody'),
    path('assets/reports/depreciation/', views.asset_depreciation_report, name='asset-depreciation-report'),
    path('assets/<int:pk>/inspect/', views.technician_inspect_asset, name='asset-inspect'),
    path('assets/<int:pk>/upload-document/', views.upload_asset_document, name='asset-upload-document'),
    path('assets/<int:pk>/print-dossier/', views.print_asset_dossier, name='print-asset-dossier'),
    path('assets/<int:pk>/serials/save/', views.save_asset_serial, name='save-asset-serial'),
    path('assets/<int:pk>/serials/delete/<int:serial_id>/', views.delete_asset_serial, name='delete-asset-serial'),

    # Statutory Form 60260-6: Board of Survey (BOS)
    path('assets/board-of-survey/', views.board_of_survey_list, name='board-of-survey-list'),
    path('assets/board-of-survey/manage/', views.manage_board_of_survey, name='manage-board-of-survey'),
    path('assets/board-of-survey/manage/<int:pk>/', views.manage_board_of_survey, name='manage-board-of-survey-pk'),
    path('assets/board-of-survey/save/', views.save_board_of_survey, name='save-board-of-survey'),
    path('assets/board-of-survey/view/<int:pk>/', views.view_board_of_survey, name='view-board-of-survey'),
    path('assets/board-of-survey/<int:pk>/items/save/', views.save_board_of_survey_item, name='save-board-of-survey-item'),
    path('assets/board-of-survey/<int:pk>/items/delete/<int:item_id>/', views.delete_board_of_survey_item, name='delete-board-of-survey-item'),
    path('assets/board-of-survey/<int:pk>/approve/', views.approve_board_of_survey, name='approve-board-of-survey'),
    path('assets/board-of-survey/<int:pk>/certify-disposal/', views.certify_disposal_board_of_survey, name='certify-disposal-board-of-survey'),
    path('assets/board-of-survey/<int:pk>/print/', views.print_board_of_survey, name='print-board-of-survey'),

    # Statutory Z.R.P. FORM 27: Requisition/Issue Voucher
    path('assets/form27/', views.form27_list, name='form27-list'),
    path('assets/form27/manage/', views.manage_form27, name='manage-form27'),
    path('assets/form27/manage/<int:pk>/', views.manage_form27, name='manage-form27-pk'),
    path('assets/form27/save/', views.save_form27, name='save-form27'),
    path('assets/form27/view/<int:pk>/', views.view_form27, name='view-form27'),
    path('assets/form27/<int:pk>/item/save/', views.save_form27_item, name='save-form27-item'),
    path('assets/form27/<int:pk>/item/delete/<int:item_id>/', views.delete_form27_item, name='delete-form27-item'),
    path('assets/form27/<int:pk>/receive/', views.receive_form27, name='receive-form27'),
    path('assets/form27/<int:pk>/sign-electronic/', views.sign_form27_electronic, name='sign-form27-electronic'),
    path('assets/form27/<int:pk>/print/', views.print_form27, name='print-form27'),

    # Statutory Z.R.P. FORM 216: Stock Card / Ledger
    path('assets/form216/', views.form216_list, name='form216-list'),
    path('assets/form216/manage/', views.manage_form216, name='manage-form216'),
    path('assets/form216/manage/<int:pk>/', views.manage_form216, name='manage-form216-pk'),
    path('assets/form216/save/', views.save_form216, name='save-form216'),
    path('assets/form216/view/<int:pk>/', views.view_form216, name='view-form216'),
    path('assets/form216/<int:pk>/entry/save/', views.save_form216_entry, name='save-form216-entry'),
    path('assets/form216/<int:pk>/entry/delete/<int:entry_id>/', views.delete_form216_entry, name='delete-form216-entry'),
    path('assets/form216/<int:pk>/print/', views.print_form216, name='print-form216'),

    # Statutory GOODS RECEIVED Ledger / Register
    path('assets/goods-received/', views.goods_received_list, name='goods-received-list'),
    path('assets/goods-received/manage/', views.manage_goods_received, name='manage-goods-received'),
    path('assets/goods-received/manage/<int:pk>/', views.manage_goods_received, name='manage-goods-received-pk'),
    path('assets/goods-received/save/', views.save_goods_received, name='save-goods-received'),
    path('assets/goods-received/delete/<int:pk>/', views.delete_goods_received, name='delete-goods-received'),
    path('assets/goods-received/print/', views.print_goods_received_ledger, name='print-goods-received'),

    # Statutory ISSUES REGISTER
    path('assets/issues-register/', views.issues_register_list, name='issues-register-list'),
    path('assets/issues-register/manage/', views.manage_issues_register, name='manage-issues-register'),
    path('assets/issues-register/manage/<int:pk>/', views.manage_issues_register, name='manage-issues-register-pk'),
    path('assets/issues-register/save/', views.save_issues_register, name='save-issues-register'),
    path('assets/issues-register/delete/<int:pk>/', views.delete_issues_register, name='delete-issues-register'),
    path('assets/issues-register/print/', views.print_issues_register, name='print-issues-register'),

    # Statutory TENDER PROCEDURES
    path('assets/tender-procedures/', views.tender_procedures_list, name='tender-procedures-list'),
    path('assets/tender-procedures/manage/', views.manage_tender_procedure, name='manage-tender-procedure'),
    path('assets/tender-procedures/manage/<int:pk>/', views.manage_tender_procedure, name='manage-tender-procedure-pk'),
    path('assets/tender-procedures/save/', views.save_tender_procedure, name='save-tender-procedure'),
    path('assets/tender-procedures/delete/<int:pk>/', views.delete_tender_procedure, name='delete-tender-procedure'),
    path('assets/tender-procedures/print/', views.print_tender_procedures, name='print-tender-procedures'),

    # Knowledge Vault
    path('knowledge/', views.knowledge_vault, name='knowledge-vault'),
    path('manage_knowledge/', views.manage_knowledge, name='manage-knowledge'),
    path('manage_knowledge/<int:pk>/', views.manage_knowledge, name='manage-knowledge-pk'),
    path('save_knowledge/', views.save_knowledge, name='save-knowledge'),
    path('view_knowledge/<int:pk>/', views.view_knowledge, name='view-knowledge'),
    path('save_knowledge_relation/', views.save_knowledge_relation, name='save-knowledge-relation'),

    # Financial Governance
    path('budgets/', views.budget_list, name='budget-list'),
    path('budget/manage/', views.manage_budget, name='manage-budget'),
    path('budget/manage/<int:pk>/', views.manage_budget, name='manage-budget-pk'),
    path('budget/save/', views.save_budget, name='save-budget'),
    path('financial/dashboard/', views.expenditure_dashboard, name='expenditure-dashboard'),
    path('financial/expenditure/manage/', views.manage_expenditure, name='manage-expenditure'),
    path('financial/expenditure/save/', views.save_expenditure, name='save-expenditure'),
    
    # AI Assistant
    path('ai_assistant/', views.ai_assistant, name='ai-assistant'),
    path('ai_assistant/process/', views.process_ai_query, name='process-ai-query'),
    path('ai_assistant/rag/', views.query_with_rag, name='query-with-rag'),
    path('ai_assistant/analyze_document/', views.analyze_document, name='analyze-document'),
    path('ai_assistant/knowledge_base/', views.rag_knowledge_base, name='rag-knowledge-base'),

    # Service Tickets
    path('tickets/', views.service_tickets, name='service-tickets'),
    path('ticket/manage/', views.manage_ticket, name='manage-ticket'),
    path('ticket/manage/<int:pk>/', views.manage_ticket, name='manage-ticket-pk'),
    path('ticket/save/', views.save_service_ticket, name='save-service-ticket'),
    path('ticket/view/<int:pk>/', views.view_ticket, name='view-ticket'),
    path('ticket/update/<int:pk>/', views.save_ticket_update, name='save-ticket-update'),
    path('ticket/delete/<int:pk>/', views.delete_ticket, name='delete-ticket'),

    # Digital Certificates
    path('certificates/', views.certificates, name='certificates'),
    path('certificate/manage/', views.manage_certificate, name='manage-certificate'),
    path('certificate/manage/<int:pk>/', views.manage_certificate, name='manage-certificate-pk'),
    path('certificate/save/', views.save_certificate, name='save-certificate'),
    path('certificate/view/<int:pk>/', views.view_certificate, name='view-certificate'),
    path('certificate/verify/', views.verify_certificate_public, name='verify-certificate'),

    # Notice Board
    path('notices/', views.notice_board, name='notice-board'),
    path('notice/manage/', views.manage_announcement, name='manage-announcement'),
    path('notice/manage/<int:pk>/', views.manage_announcement, name='manage-announcement-pk'),
    path('notice/save/', views.save_announcement, name='save-announcement'),

    # Organizational Digital Twin
    path('digital_twin/', views.digital_twin, name='digital-twin'),
    path('api/digital_twin/updates/', views.get_digital_twin_updates, name='digital-twin-updates'),

    # Federation Mode
    path('organizations', views.organizations, name='organization-page'),
    path('manage_organization', views.manage_organization, name='manage-organization'),
    path('manage_organization/<int:pk>', views.manage_organization, name='manage-organization-pk'),
    path('save_organization', views.save_organization, name='save-organization'),
    path('federation_links', views.federation_links, name='federation-link-page'),
    path('federated_transfer_file/', views.federated_transfer_file, name='federated-transfer-file'),
    path('federated_transfer_modal/', views.federated_transfer_modal, name='federated-transfer-modal'),

    # Smart Scanner Integration
    path('api/scanner/upload/', views.scanner_upload_api, name='scanner-upload-api'),
    path('scanner/scans/', views.scanned_docs_list, name='scanned-docs-list'),
    path('scanner/search/', views.smart_search_docs, name='smart-search-docs'),
    path('scanner/process/<int:pk>/', views.process_scan, name='process-scan'),
    path('scanner/devices/', views.scanner_devices, name='scanner-devices'),
    path('scanner/save_device/', views.save_scanner_device, name='save-scanner-device'),
    path('scanner/delete_device/<int:pk>/', views.delete_scanner_device, name='delete-scanner-device'),

    # RIFTS Document Cloud
    path('cloud/', views.cloud_dashboard, name='cloud-dashboard'),
    path('cloud/file/<int:pk>/', views.cloud_file_view, name='cloud-file-view'),
    path('cloud/upload/', views.cloud_upload_version, name='cloud-upload'),
    path('cloud/upload/<int:pk>/', views.cloud_upload_version, name='cloud-upload-version'),
    path('cloud/create-folder/', views.cloud_create_folder, name='cloud-create-folder'),
    path('cloud/create-document/', views.cloud_create_doc, name='cloud-create-doc'),
    path('cloud/delete-folder/<int:pk>/', views.cloud_delete_folder, name='cloud-delete-folder'),
    path('cloud/download-folder/<int:pk>/', views.cloud_download_folder, name='cloud-download-folder'),
    path('cloud/restore-folder/<int:pk>/', views.cloud_restore_folder, name='cloud-restore-folder'),
    path('cloud/file/delete/<int:pk>/', views.cloud_delete_file, name='cloud-delete-file'),
    path('cloud/file/restore/<int:pk>/', views.cloud_restore_file, name='cloud-restore-file'),
    path('cloud/file/<int:pk>/generate-share/', views.cloud_generate_share, name='cloud-generate-share'),
    path('cloud/s/<str:token>/', views.cloud_share_access, name='cloud-share-access'),

    # Individual File Digital Twin
    path('file-digital-twin/<int:pk>/', views.file_digital_twin, name='file-digital-twin'),
    path('sync-digital-twin/<int:pk>/', views.sync_digital_twin, name='sync-digital-twin'),
    path('mark-file-lost/<int:pk>/', views.mark_file_lost, name='mark-file-lost'),
    # Offline & Mobile Capture
    path('mobile-capture/', views.mobile_capture, name='mobile-capture'),
    path('api/sync/upload/', views.upload_sync_record, name='upload-sync-record'),
    path('api/sync/trigger/', views.trigger_sync, name='trigger-sync'),
    # Project Governance
    path('projects/', views.project_governance_list, name='project-list'),
    path('projects/portfolio/', views.project_portfolio, name='project-portfolio'),
    path('projects/create/', views.create_project, name='create-project'),
    path('projects/<int:pk>/', views.project_detail, name='project-detail'),
    path('projects/approve-phase/<int:pk>/<str:status>/', views.approve_phase, name='approve-phase'),
    path('projects/pl-consolidate/<int:pk>/', views.pm_consolidate_phase, name='pm-consolidate-phase'),
    path('projects/pl-consolidate-auto/<int:pk>/', views.pm_auto_consolidate_phase, name='pm-auto-consolidate-auto'),
    path('projects/pmt-verify/<int:pk>/', views.pmt_verify_phase, name='pmt-verify-phase'),
    path('projects/hods-verify/<int:pk>/', views.hods_verify_phase, name='hods-verify-phase'),
    path('projects/return-phase/<int:pk>/', views.return_phase, name='return-phase'),
    path('projects/phase/edit-meta/<int:pk>/', views.edit_phase_meta, name='edit-phase-meta'),
    path('projects/advance-phase/<int:pk>/', views.advance_phase_view, name='advance-phase'),
    path('projects/update-task-status/<int:pk>/', views.update_task_status, name='update-task-status'),
    path('projects/membership/request/<int:project_pk>/', views.request_project_membership, name='request-project-membership'),
    path('projects/membership/approve/<int:membership_pk>/<str:action>/', views.approve_project_member, name='approve-project-member'),
    path('projects/executive-governance/', views.executive_governance, name='executive-governance'),
    # Sprint URLs (Layer 4)
    path('projects/phase/<int:phase_pk>/sprint/create/', views.manage_sprint, name='create-sprint'),
    path('projects/phase/<int:phase_pk>/sprint/<int:sprint_pk>/edit/', views.manage_sprint, name='edit-sprint'),
    path('projects/sprint/<int:pk>/', views.sprint_detail, name='sprint-detail'),
    path('projects/sprint/<int:pk>/status/', views.update_sprint_status, name='sprint-status'),
    # Task URLs (Layer 5)
    path('projects/phase/<int:phase_pk>/task/create/', views.manage_task, name='create-task'),
    path('projects/phase/<int:phase_pk>/task/<int:task_pk>/edit/', views.manage_task, name='edit-task'),
    path('projects/task/<int:pk>/', views.task_detail, name='task-detail'),
    path('projects/update-task/<int:pk>/', views.update_task, name='update-task'),

    
    # Visualization & Kanban AJAX
    path('projects/api/viz/<int:pk>/', views.project_visualization_data, name='project-viz-data'),
    path('projects/api/kanban/update/', views.update_task_kanban, name='update-task-kanban'),
    path('projects/phase/<int:pk>/attach-document/', views.attach_phase_document, name='attach-phase-document'),

    path('approve_action/<int:pk>/<str:status>/', views.handle_approval, name='handle-approval'),
    path('approvals/', views.approvals_list, name='approvals-list'),
    
    # Benefit Tracking
    path('governance/benefits/', views.benefit_list, name='benefit-list'),
    path('governance/benefits/create/', views.manage_benefit, name='create-benefit'),
    path('governance/benefits/manage/<int:pk>/', views.manage_benefit, name='manage-benefit'),
    path('governance/benefits/delete/<int:pk>/', views.delete_benefit, name='delete-benefit'),

    # Deliverables Release
    path('projects/phase/<int:pk>/download-deliverables/', views.download_phase_deliverables, name='download-phase-deliverables'),
    
    # Collaboration & Comments
    path('collaboration/comment/add/', views.add_comment, name='add-comment'),
    path('collaboration/action-item/resolve/<int:pk>/', views.resolve_action_item, name='resolve-action-item'),
    path('projects/intelligence-hub/', views.intelligence_hub, name='intelligence-hub'),

    # HOD Cost Recovery Financial Dashboard
    path('hod/financial-dashboard/', views.hod_financial_dashboard, name='hod-financial-dashboard'),
    path('hod/cost-recovery/save/', views.save_cost_recovery, name='save-cost-recovery'),
    path('hod/cost-recovery/chart-data/', views.cost_recovery_chart_data, name='cost-recovery-chart-data'),
    
    path('projects/<int:pk>/delete/', views.delete_project, name='delete-project'),
    path('projects/<int:pk>/restore/', views.restore_project, name='restore-project'),
    path('projects/recycle-bin/', views.recycle_bin, name='recycle-bin'),
    path('projects/<int:pk>/governance-levels/', views.edit_governance_levels, name='edit-governance-levels'),
    
    # Collaborative Mentions & Notifications
    # RIFTS-X Governance Extension
    path('collaboration/mentions/users/', views.get_mention_users, name='get-mention-users'),
    path('collaboration/notifications/', views.get_user_notifications, name='get-user-notifications'),
    path('notifications/subscribe/', views.save_push_subscription, name='save-push-subscription'),
    path('notifications/test-push/', views.test_push_notification, name='test-push-notification'),

    # BRD E-Signature Workflow
    path('brd/', views.brd_list, name='brd-list'),
    path('brd/initiate/', views.initiate_brd, name='initiate-brd'),
    path('brd/<int:pk>/', views.brd_detail, name='brd-detail'),
    path('brd/<int:pk>/sign/', views.sign_brd, name='sign-brd'),
    path('brd/<int:pk>/sign-visual/', views.brd_sign_visual, name='brd-sign-visual'),
    path('brd/<int:pk>/reject/', views.reject_brd, name='reject-brd'),
    path('brd/<int:pk>/download/', views.download_brd, name='download-brd'),
    path('brd/<int:pk>/forward-pl/', views.brd_forward_to_pl, name='brd-forward-to-pl'),
    path('brd/<int:pk>/edit/', views.edit_brd, name='edit-brd'),
    path('brd/<int:pk>/delete/', views.delete_brd, name='delete-brd'),
    path('brd/<int:pk>/ai-analyze/', views.brd_ai_analyze, name='brd-ai-analyze'),
    path('brd/<int:pk>/ai-chat/', views.brd_ai_chat, name='brd-ai-chat'),
]

# --- RIFTS-X REST API Routing ---
from django.urls import include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views
from registry import api_views

router = DefaultRouter()
router.register('users', api_views.UserViewSet, basename='api-users')
router.register('organizations', api_views.OrganizationViewSet, basename='api-organizations')
router.register('departments', api_views.DepartmentViewSet, basename='api-departments')
router.register('files', api_views.FileViewSet, basename='api-files')
router.register('borrows', api_views.BorrowViewSet, basename='api-borrows')
router.register('cloud-folders', api_views.CloudFolderViewSet, basename='api-cloud-folders')
router.register('cloud-files', api_views.CloudFileViewSet, basename='api-cloud-files')
router.register('projects', api_views.ProjectViewSet, basename='api-projects')
router.register('project-tasks', api_views.ProjectTaskViewSet, basename='api-project-tasks')
router.register('brds', api_views.BRDViewSet, basename='api-brds')
router.register('requisitions', api_views.SupplyRequisitionViewSet, basename='api-requisitions')

urlpatterns += [
    path('api/token-auth/', auth_views.obtain_auth_token, name='api-token-auth'),
    path('api/', include(router.urls)),
    # API Portal & Developer Documentation
    path('api-docs/', views.api_docs, name='api-docs'),
    path('api-docs/download/', views.download_api_docs, name='download-api-docs'),
    # ZRP Document Governance Routes
    path('files/<int:file_id>/move/', views.move_document_view, name='move-document'),
    path('files/<int:file_id>/rename/', views.rename_document_view, name='rename-document'),
    path('files/<int:file_id>/archive/', views.archive_document_view, name='archive-document'),
    path('files/<int:file_id>/restore/', views.restore_document_view, name='restore-document'),
    path('files/<int:file_id>/workflow/', views.transition_document_workflow, name='transition-document-workflow'),
    # ZRP Minuting & Meeting Action Tracking Routes
    path('meetings/', views.minuting_dashboard_view, name='meetings-dashboard'),
    path('meetings/create/', views.create_meeting_view, name='create-meeting'),
    path('meetings/<int:meeting_id>/minute-taking/', views.digital_minute_taking_view, name='digital-minute-taking'),
    path('meetings/transcribe/', views.transcribe_audio_view, name='transcribe-audio'),
    path('meetings/<int:meeting_id>/workflow/', views.approve_minutes_workflow_view, name='approve-minutes-workflow'),
    path('action-tracking/', views.action_tracking_view, name='action-tracking'),
    path('action-tracking/<int:action_id>/comment/', views.post_action_comment_view, name='post-action-comment'),
    # ZRP Interview & Selection Governance Routes
    path('interviews/', views.interview_dashboard_view, name='interview-dashboard'),
    path('interviews/create/', views.create_interview_exercise_view, name='create-interview-exercise'),
    path('interviews/candidate/<int:candidate_id>/scorecard/', views.conduct_interview_scoring_view, name='conduct-interview-scoring'),
    path('interviews/<int:exercise_id>/workflow/', views.advance_interview_workflow_view, name='advance-interview-workflow'),
    path('interviews/<int:exercise_id>/reports/', views.interview_reports_view, name='interview-reports'),
    # ZRP HR & Leave Governance Routes
    path('hr/self-service/', views.employee_self_service_view, name='employee-self-service'),
    path('leaves/out-of-office/', views.out_of_office_dashboard_view, name='out-of-office-dashboard'),
    path('leaves/<int:leave_id>/workflow/', views.advance_leave_workflow_view, name='advance-leave-workflow'),
    # ZRP Procurement & Movement Tracking Routes
    path('procurement/<int:pk>/movement/', views.track_requisition_movement_view, name='track-requisition-movement'),
    path('procurement/<int:pk>/issue-po/', views.issue_purchase_order_view, name='issue-purchase-order'),
    path('procurement/<int:pk>/update-delivery/', views.update_delivery_status_view, name='update-delivery-status'),
    # ZRP Training, Travel & Subsistence Allowance (TSA) Routes
    path('travel-tsa/', views.travel_tsa_dashboard_view, name='travel-tsa-dashboard'),
    path('travel-tsa/create/', views.create_travel_request_view, name='create-travel-request'),
    path('travel-tsa/<int:pk>/workflow/', views.advance_travel_workflow_view, name='advance-travel-workflow'),
    path('travel-tsa/<int:pk>/acquittal/', views.submit_travel_acquittal_view, name='submit-travel-acquittal'),
    # ZRP Universal Electronic Approval & Signature Routes
    path('approvals/center/', views.electronic_approval_center_view, name='electronic-approval-center'),
    path('approvals/trail/<str:entity_type>/<int:entity_id>/', views.verify_approval_trail_view, name='verify-approval-trail'),
    path('approvals/sign-action/', views.sign_electronic_approval_action_view, name='sign-electronic-approval-action'),
    # ZRP Daily Attendance & Time Management Routes
    path('attendance/', views.attendance_dashboard_view, name='attendance-dashboard'),
    path('attendance/clock-action/', views.clock_in_out_action_view, name='clock-in-out-action'),
    path('attendance/monthly-report/', views.monthly_attendance_report_view, name='monthly-attendance-report'),
    # ZRP Analytics, Executive & Admin Dashboard Routes
    path('analytics/executive/', views.executive_analytics_dashboard_view, name='executive-analytics-dashboard'),
    path('admin-operations/', views.admin_operations_dashboard_view, name='admin-operations-dashboard'),
    path('admin/', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin', RedirectView.as_view(url='/admin/', permanent=False)),
    path('reports/export/<str:report_type>/', views.export_reports_view, name='export-reports'),
    # ZRP Departmental Analytics Dashboards
    path('analytics/hr/', views.hr_analytics_dashboard_view, name='hr-analytics-dashboard'),
    path('analytics/procurement/', views.procurement_analytics_dashboard_view, name='procurement-analytics-dashboard'),
    path('analytics/travel-training/', views.travel_analytics_dashboard_view, name='travel-analytics-dashboard'),
    # ZRP Security, Access Control & Audit Governance Routes
    path('security/center/', views.security_audit_center_view, name='security-audit-center'),
    path('security/toggle-mfa/', views.toggle_mfa_action_view, name='toggle-mfa-action'),
    path('security/backup-db/', views.backup_and_recovery_action_view, name='backup-and-recovery-action'),
    # ZRP Notification & Alert Hub Routes
    path('notifications/', views.notifications_center_view, name='notifications-center'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark-notification-read'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='mark-all-notifications-read'),
    # ZRP Requirement 13: Unified Platform Command Portal
    path('platform/architecture/', views.zrp_unified_platform_view, name='ZRP-unified-platform'),
    # ZRP Requirement 14: Institutional Documentation & Templates Routes
    path('institutional/library/', views.zrp_institutional_library_view, name='ZRP-institutional-library'),
    path('institutional/template/create/', views.manage_document_template, name='template-create'),
    path('institutional/template/edit/<int:pk>/', views.manage_document_template, name='template-edit'),
    path('institutional/template/delete/<int:pk>/', views.delete_document_template, name='template-delete'),
    path('institutional/template/preview/<int:pk>/', views.preview_document_template, name='template-preview'),
]
#+ static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
