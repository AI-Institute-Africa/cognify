import requests
import sys
import json
from datetime import datetime

class EduOSAPITester:
    def __init__(self, base_url="https://school-hub-128.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append({"test": name, "error": details})

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Expected {expected_status}, got {response.status_code}"
            if not success and response.text:
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', response.text[:100])}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details if not success else "")
            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_register_student(self):
        """Test student registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        student_data = {
            "email": f"student_{timestamp}@test.edu",
            "password": "TestPass123!",
            "full_name": f"Test Student {timestamp}",
            "role": "student"
        }
        
        success, response = self.run_test("Register Student", "POST", "auth/register", 200, student_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True
        return False

    def test_register_teacher(self):
        """Test teacher registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        teacher_data = {
            "email": f"teacher_{timestamp}@test.edu",
            "password": "TestPass123!",
            "full_name": f"Test Teacher {timestamp}",
            "role": "teacher"
        }
        
        success, response = self.run_test("Register Teacher", "POST", "auth/register", 200, teacher_data)
        return success

    def test_register_parent(self):
        """Test parent registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        parent_data = {
            "email": f"parent_{timestamp}@test.edu",
            "password": "TestPass123!",
            "full_name": f"Test Parent {timestamp}",
            "role": "parent"
        }
        
        success, response = self.run_test("Register Parent", "POST", "auth/register", 200, parent_data)
        return success

    def test_login(self):
        """Test login with registered user"""
        if not self.user_data:
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("Login", "POST", "auth/login", 200, login_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_get_me(self):
        """Test get current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)[0]

    def test_dashboard_stats(self):
        """Test dashboard stats"""
        return self.run_test("Dashboard Stats", "GET", "dashboard/stats", 200)[0]

    def test_get_courses(self):
        """Test get courses"""
        return self.run_test("Get Courses", "GET", "courses", 200)[0]

    def test_create_course(self):
        """Test create course (requires teacher/admin role)"""
        course_data = {
            "code": f"TEST{datetime.now().strftime('%H%M%S')}",
            "name": "Test Course",
            "description": "A test course for API testing",
            "grade_level": "Grade 10",
            "credits": 3,
            "max_students": 30
        }
        
        # This might fail if user is student (expected behavior)
        success, response = self.run_test("Create Course", "POST", "courses", 201, course_data)
        return success, response.get('id') if success else None

    def test_enroll_course(self, course_id):
        """Test course enrollment"""
        if not course_id:
            return False
        return self.run_test("Enroll Course", "POST", f"courses/{course_id}/enroll", 200)[0]

    def test_get_attendance(self):
        """Test get attendance"""
        return self.run_test("Get Attendance", "GET", "attendance", 200)[0]

    def test_get_grades(self):
        """Test get grades"""
        return self.run_test("Get Grades", "GET", "grades", 200)[0]

    def test_get_fees(self):
        """Test get fees"""
        return self.run_test("Get Fees", "GET", "fees", 200)[0]

    def test_get_achievements(self):
        """Test get achievements"""
        return self.run_test("Get Achievements", "GET", "achievements", 200)[0]

    def test_get_notifications(self):
        """Test get notifications"""
        return self.run_test("Get Notifications", "GET", "notifications", 200)[0]

    def test_ai_career_chat(self):
        """Test AI career guidance"""
        chat_data = {
            "message": "What career paths are good for someone interested in technology?",
            "context": "Testing AI integration"
        }
        
        success, response = self.run_test("AI Career Chat", "POST", "ai/career-chat", 200, chat_data)
        if success and 'response' in response:
            print(f"   AI Response received: {len(response['response'])} characters")
        return success

    def test_ai_lesson_planner(self):
        """Test AI lesson planner (requires teacher role)"""
        lesson_data = {
            "message": "Create a lesson plan for introduction to programming"
        }
        
        success, response = self.run_test("AI Lesson Planner", "POST", "ai/lesson-planner", 200, lesson_data)
        if success and 'response' in response:
            print(f"   AI Response received: {len(response['response'])} characters")
        return success

    def test_get_students(self):
        """Test get students (admin/teacher only)"""
        return self.run_test("Get Students", "GET", "students", 200)[0]

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting EduOS API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)

        # Health check
        self.test_health_check()

        # Authentication tests
        print("\n📝 Testing Authentication...")
        if not self.test_register_student():
            print("❌ Student registration failed - stopping tests")
            return self.get_results()

        self.test_register_teacher()
        self.test_register_parent()
        
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return self.get_results()

        self.test_get_me()

        # Core functionality tests
        print("\n📊 Testing Core Features...")
        self.test_dashboard_stats()
        self.test_get_courses()
        
        # Try to create course (might fail for student role)
        course_success, course_id = self.test_create_course()
        if course_id:
            self.test_enroll_course(course_id)

        self.test_get_attendance()
        self.test_get_grades()
        self.test_get_fees()
        self.test_get_achievements()
        self.test_get_notifications()

        # AI features
        print("\n🤖 Testing AI Features...")
        self.test_ai_career_chat()
        self.test_ai_lesson_planner()  # Might fail for student role

        # Admin features
        print("\n👥 Testing Management Features...")
        self.test_get_students()  # Might fail for student role

        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test['test']}: {test['error']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n✨ Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failed_tests),
            "success_rate": success_rate,
            "failures": self.failed_tests
        }

def main():
    tester = EduOSAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())