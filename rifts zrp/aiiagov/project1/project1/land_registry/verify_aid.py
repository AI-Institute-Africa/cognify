import os, sys, django, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'land_registry.settings'
django.setup()

from registry.services.ai_assistant import AIAssistantService
from registry.services.federation import FederationService

print("=== AI QUERY PARSING TESTS ===")

tests = [
    'contracts signed in March 2024 above 100k pending approval',
    'approved leave requests in 2023',
    'rejected requisitions below 50k',
    'active assets ICT equipment',
    'knowledge policy SOP manual',
]

for q in tests:
    r = AIAssistantService.parse_query(q)
    print(f"  Query : {q}")
    print(f"  Entity: {r['entity']} | Filters: {r['filters']}")
    print()

print("=== HMAC FEDERATION TESTS ===")

class MockLink:
    shared_secret = 'super_secret_key_for_testing_only'
    link_status = 'Active'

link = MockLink()
payload = {'file_id': 42, 'target': 'MINISTRY_OF_FINANCE'}
token = FederationService.generate_access_token(link, payload)
valid = FederationService.verify_access_token(link, payload, token)
tampered_valid = FederationService.verify_access_token(link, {'file_id': 99}, token)

print(f"  Token generated : {token[:32]}...")
print(f"  Valid (correct) : {valid}")
print(f"  Valid (tampered): {tampered_valid}")
print()

if valid and not tampered_valid:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
