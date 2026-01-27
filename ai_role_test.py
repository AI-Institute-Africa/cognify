import requests
import time
import json

def test_ai_with_timeout():
    """Test AI features with longer timeout"""
    base_url = "https://school-hub-128.preview.emergentagent.com/api"
    
    # First register and login as student
    student_data = {
        "email": f"ai_test_student_{int(time.time())}@test.edu",
        "password": "TestPass123!",
        "full_name": "AI Test Student",
        "role": "student"
    }
    
    print("🔐 Registering student for AI test...")
    response = requests.post(f"{base_url}/auth/register", json=student_data, timeout=30)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("✅ Student registered and logged in")
    
    # Test AI Career Chat with longer timeout
    print("\n🤖 Testing AI Career Chat (30s timeout)...")
    chat_data = {
        "message": "What are good career paths in technology?",
        "context": "Testing AI integration"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/ai/career-chat", json=chat_data, headers=headers, timeout=30)
        end_time = time.time()
        
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI Career Chat successful")
            print(f"📝 Response length: {len(result.get('response', ''))} characters")
            if result.get('response'):
                print(f"📄 Sample response: {result['response'][:200]}...")
            return True
        else:
            print(f"❌ AI Career Chat failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ AI Career Chat timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ AI Career Chat error: {str(e)}")
        return False

def test_role_based_access():
    """Test role-based access control"""
    base_url = "https://school-hub-128.preview.emergentagent.com/api"
    
    print("\n👥 Testing Role-Based Access Control...")
    
    # Test with teacher role
    teacher_data = {
        "email": f"role_test_teacher_{int(time.time())}@test.edu",
        "password": "TestPass123!",
        "full_name": "Role Test Teacher",
        "role": "teacher"
    }
    
    print("🔐 Registering teacher...")
    response = requests.post(f"{base_url}/auth/register", json=teacher_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Teacher registration failed: {response.status_code}")
        return False
    
    teacher_token = response.json()['access_token']
    teacher_headers = {'Authorization': f'Bearer {teacher_token}', 'Content-Type': 'application/json'}
    
    # Test course creation with teacher role
    course_data = {
        "code": f"ROLE{int(time.time())}",
        "name": "Role Test Course",
        "description": "Testing role-based course creation",
        "grade_level": "Grade 10",
        "credits": 3,
        "max_students": 30
    }
    
    print("📚 Testing course creation with teacher role...")
    response = requests.post(f"{base_url}/courses", json=course_data, headers=teacher_headers, timeout=10)
    
    if response.status_code == 201:
        print("✅ Teacher can create courses")
        course_id = response.json()['id']
        
        # Test student management access
        print("👥 Testing student management access...")
        response = requests.get(f"{base_url}/students", headers=teacher_headers, timeout=10)
        if response.status_code == 200:
            print("✅ Teacher can access student management")
        else:
            print(f"❌ Teacher cannot access students: {response.status_code}")
        
        return True
    else:
        print(f"❌ Teacher cannot create courses: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("🧪 EduOS AI and Role Testing")
    print("=" * 40)
    
    ai_success = test_ai_with_timeout()
    role_success = test_role_based_access()
    
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    print(f"AI Features: {'✅ Working' if ai_success else '❌ Failed'}")
    print(f"Role Access: {'✅ Working' if role_success else '❌ Failed'}")