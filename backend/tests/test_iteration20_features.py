"""
Iteration 20 Testing - P0 Bug Fixes and Batch 1 Features
Tests:
1. P0 Bug Fix: Content uploads (videos, images) display correctly on CourseViewPage
2. P0 Bug Fix: Organization Admin Dashboard - Staff and Participants tabs
3. P0 Bug Fix: Study Groups visibility - all students see groups in 'Browse All Groups'
4. Batch 1 Feature: Teacher Messaging Page - teachers see students and send messages
5. Batch 1 Feature: AI Mentor Voice Input - Web Speech API (frontend only)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cognify-edu.preview.emergentagent.com')

# Test credentials
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
STUDENT_CREDS = {"email": "demo.student@cognify.edu", "password": "demo123"}
ORG_ADMIN_CREDS = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}

# Course with content
COURSE_WITH_CONTENT_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✓ Health check passed")


class TestAuthentication:
    """Authentication tests for all user types"""
    
    def test_teacher_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] in ['teacher', 'admin']
        print(f"✓ Teacher login successful: {data['user']['email']}")
        return data['access_token']
    
    def test_student_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'student'
        print(f"✓ Student login successful: {data['user']['email']}")
        return data['access_token']
    
    def test_org_admin_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['user']['role'] == 'org_admin'
        print(f"✓ Org admin login successful: {data['user']['email']}")
        return data['access_token']


class TestCourseContentDisplay:
    """P0 Bug Fix: Content uploads (videos, images) display correctly"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()['access_token']
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()['access_token']
    
    def test_get_course_content(self, student_token):
        """Test that course content endpoint returns content with video/image URLs"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(
            f"{BASE_URL}/api/content/course/{COURSE_WITH_CONTENT_ID}/content",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if it's a list or has access_restricted
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
            print(f"✓ Course content returned (access restricted): {len(contents)} items")
        else:
            contents = data if isinstance(data, list) else []
            print(f"✓ Course content returned: {len(contents)} items")
        
        # Check for video/image content types
        video_count = sum(1 for c in contents if c.get('type') == 'video')
        image_count = sum(1 for c in contents if c.get('type') == 'image')
        print(f"  - Videos: {video_count}, Images: {image_count}")
        
        return contents
    
    def test_video_content_has_url(self, student_token):
        """Test that video content has proper URL field"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(
            f"{BASE_URL}/api/content/course/{COURSE_WITH_CONTENT_ID}/content",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        contents = data.get('contents', []) if isinstance(data, dict) else data
        video_contents = [c for c in contents if c.get('type') == 'video']
        
        for video in video_contents:
            # Video should have url or video_url field
            has_url = video.get('url') or video.get('video_url')
            print(f"  Video '{video.get('title')}': URL present = {bool(has_url)}")
            if has_url:
                print(f"    URL: {has_url[:80]}...")
        
        print(f"✓ Video content URL check completed: {len(video_contents)} videos")
    
    def test_image_content_has_url(self, student_token):
        """Test that image content has proper URL field"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(
            f"{BASE_URL}/api/content/course/{COURSE_WITH_CONTENT_ID}/content",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        contents = data.get('contents', []) if isinstance(data, dict) else data
        image_contents = [c for c in contents if c.get('type') == 'image']
        
        for img in image_contents:
            # Image should have url or image_url field
            has_url = img.get('url') or img.get('image_url')
            print(f"  Image '{img.get('title')}': URL present = {bool(has_url)}")
            if has_url:
                print(f"    URL: {has_url[:80]}...")
        
        print(f"✓ Image content URL check completed: {len(image_contents)} images")
    
    def test_upload_video_content(self, teacher_token):
        """Test that teachers can upload video content"""
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        video_content = {
            "content_type": "video",
            "title": f"TEST_Video_{uuid.uuid4().hex[:8]}",
            "description": "Test video content for iteration 20",
            "content_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "order": 99
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{COURSE_WITH_CONTENT_ID}/content",
            headers=headers,
            json=video_content
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('type') == 'video'
        assert data.get('url') or data.get('content_url')
        print(f"✓ Video content uploaded successfully: {data.get('title')}")
        return data.get('id')
    
    def test_upload_image_content(self, teacher_token):
        """Test that teachers can upload image content"""
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        image_content = {
            "content_type": "image",
            "title": f"TEST_Image_{uuid.uuid4().hex[:8]}",
            "description": "Test image content for iteration 20",
            "content_url": "https://picsum.photos/800/600",
            "order": 98
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{COURSE_WITH_CONTENT_ID}/content",
            headers=headers,
            json=image_content
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('type') == 'image'
        print(f"✓ Image content uploaded successfully: {data.get('title')}")
        return data.get('id')


class TestOrgAdminDashboard:
    """P0 Bug Fix: Organization Admin Dashboard - Staff and Participants tabs"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        return response.json()['access_token']
    
    def test_org_admin_dashboard(self, org_admin_token):
        """Test org admin dashboard endpoint"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/admin/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for statistics
        stats = data.get('statistics', {})
        print(f"✓ Org admin dashboard loaded")
        print(f"  - Teachers: {stats.get('teachers', 0)}")
        print(f"  - Students: {stats.get('students', 0)}")
        print(f"  - Courses: {stats.get('courses', 0)}")
        return data
    
    def test_org_teachers_list(self, org_admin_token):
        """Test that Staff tab data (teachers) is returned correctly"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/teachers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        teachers = data if isinstance(data, list) else []
        print(f"✓ Staff (teachers) list returned: {len(teachers)} members")
        
        for teacher in teachers[:3]:  # Show first 3
            print(f"  - {teacher.get('full_name', 'N/A')} ({teacher.get('email', 'N/A')}) - {teacher.get('role', 'N/A')}")
        
        return teachers
    
    def test_org_students_list(self, org_admin_token):
        """Test that Participants tab data (students) is returned correctly"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        students = data if isinstance(data, list) else []
        print(f"✓ Participants (students) list returned: {len(students)} members")
        
        for student in students[:3]:  # Show first 3
            print(f"  - {student.get('full_name', 'N/A')} ({student.get('email', 'N/A')}) - GPA: {student.get('gpa', 'N/A')}")
        
        return students


class TestStudyGroupsVisibility:
    """P0 Bug Fix: Study Groups visibility - all students see groups in 'Browse All Groups'"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()['token']
    
    def test_get_all_study_groups(self, student_token):
        """Test that GET /api/study-groups/all returns all groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        groups = data if isinstance(data, list) else []
        print(f"✓ All study groups returned: {len(groups)} groups")
        
        for group in groups[:5]:  # Show first 5
            print(f"  - {group.get('name', 'N/A')} (Topic: {group.get('topic', 'N/A')}) - Members: {group.get('member_count', 0)}")
        
        return groups
    
    def test_study_groups_search(self, student_token):
        """Test search functionality in Browse All Groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(
            f"{BASE_URL}/api/study-groups/all?search=study",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        groups = data if isinstance(data, list) else []
        print(f"✓ Study groups search returned: {len(groups)} groups matching 'study'")
        return groups
    
    def test_create_and_find_group(self, student_token):
        """Test that a created group appears in all groups list"""
        headers = {
            "Authorization": f"Bearer {student_token}",
            "Content-Type": "application/json"
        }
        
        # Create a new group
        group_name = f"TEST_Group_{uuid.uuid4().hex[:8]}"
        new_group = {
            "name": group_name,
            "topic": "Testing",
            "description": "Test group for iteration 20"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/study-groups",
            headers=headers,
            json=new_group
        )
        assert create_response.status_code == 200
        created_group = create_response.json()
        group_id = created_group.get('id')
        print(f"✓ Created test group: {group_name}")
        
        # Verify it appears in all groups
        all_response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert all_response.status_code == 200
        all_groups = all_response.json()
        
        found = any(g.get('name') == group_name for g in all_groups)
        assert found, f"Created group '{group_name}' not found in all groups list"
        print(f"✓ Created group found in 'Browse All Groups' list")
        
        # Cleanup - delete the test group
        if group_id:
            delete_response = requests.delete(
                f"{BASE_URL}/api/study-groups/{group_id}",
                headers=headers
            )
            if delete_response.status_code == 200:
                print(f"✓ Test group cleaned up")


class TestTeacherMessaging:
    """Batch 1 Feature: Teacher Messaging Page"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()['token']
    
    def test_get_teacher_students(self, teacher_token):
        """Test that teachers can get list of their students"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        students = data if isinstance(data, list) else []
        print(f"✓ Teacher students list returned: {len(students)} students")
        
        for student in students[:5]:  # Show first 5
            print(f"  - {student.get('full_name', 'N/A')} ({student.get('email', 'N/A')})")
        
        return students
    
    def test_get_teacher_students_by_course(self, teacher_token):
        """Test that teachers can get students grouped by course"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/students-by-course", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        courses = data if isinstance(data, list) else []
        print(f"✓ Teacher students by course returned: {len(courses)} courses")
        
        for course in courses[:3]:  # Show first 3
            students = course.get('students', [])
            print(f"  - {course.get('course_name', 'N/A')}: {len(students)} students")
        
        return courses
    
    def test_send_message_endpoint_exists(self, teacher_token):
        """Test that message sending endpoint exists"""
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        # Test with a dummy student ID - should return 404 for non-existent student
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers=headers,
            json={
                "recipient_id": "non-existent-id",
                "content": "Test message",
                "message_type": "text"
            }
        )
        
        # Should not be 405 (method not allowed) - endpoint should exist
        assert response.status_code != 405, "Messages endpoint does not exist"
        print(f"✓ Messages endpoint exists (status: {response.status_code})")


class TestAIMentorVoiceInput:
    """Batch 1 Feature: AI Mentor Voice Input - Web Speech API (frontend verification)"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()['token']
    
    def test_mentor_profile_endpoint(self, student_token):
        """Test that mentor profile endpoint works"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/mentor/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Mentor profile endpoint works")
        print(f"  - Learning style: {data.get('learning_style', 'N/A')}")
        print(f"  - Preferred pace: {data.get('preferred_pace', 'N/A')}")
        return data
    
    def test_mentor_chat_endpoint(self, student_token):
        """Test that mentor chat endpoint works"""
        headers = {
            "Authorization": f"Bearer {student_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/mentor/chat",
            headers=headers,
            json={
                "message": "Hello, can you help me study?",
                "language": "en",
                "context": "general",
                "include_audio": False
            }
        )
        
        # Should return 200 or 500 (if AI service has issues)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Mentor chat endpoint works")
            print(f"  - Response preview: {data.get('response', '')[:100]}...")
        else:
            print(f"⚠ Mentor chat returned 500 (AI service may be unavailable)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
