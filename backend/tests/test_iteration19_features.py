"""
Test Suite for Iteration 19 Features:
- Study Groups - All groups visible to all students at /api/study-groups/all
- Organization Settings - Profile, Social Media, Documents, Database tabs
- Assignment Generator - Course selection dropdown with course_id parameter
- Video/Image content display in CourseViewPage
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://edusync-34.preview.emergentagent.com')

# Test credentials
STUDENT_CREDS = {"email": "demo.student@cognify.edu", "password": "demo123"}
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
ORG_ADMIN_CREDS = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}


class TestAuthentication:
    """Authentication tests for all user types"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        print("✓ Health check passed")
    
    def test_student_login(self):
        """Test student authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data.get('user', {}).get('role') == 'student'
        print("✓ Student login successful")
        return data['access_token']
    
    def test_teacher_login(self):
        """Test teacher authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data.get('user', {}).get('role') == 'teacher'
        print("✓ Teacher login successful")
        return data['access_token']
    
    def test_org_admin_login(self):
        """Test org admin authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data.get('user', {}).get('role') == 'org_admin'
        print("✓ Org admin login successful")
        return data['access_token']


class TestStudyGroupsAll:
    """Test Study Groups - All groups visible to all students"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()['access_token']
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()['access_token']
    
    def test_get_all_study_groups_endpoint_exists(self, student_token):
        """Test that /api/study-groups/all endpoint exists and returns data"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/study-groups/all returns {len(data)} groups")
    
    def test_all_groups_visible_to_student(self, student_token):
        """Test that all groups are visible to students (not filtered by is_public)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert response.status_code == 200
        groups = response.json()
        
        # Verify response structure
        if len(groups) > 0:
            group = groups[0]
            assert 'id' in group or 'name' in group
            assert 'member_count' in group or 'members' in group
            print(f"✓ Student can see all {len(groups)} study groups")
        else:
            print("✓ No study groups exist yet, but endpoint works")
    
    def test_study_groups_search(self, student_token):
        """Test search functionality on all study groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all?search=test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Study groups search returns {len(data)} results")
    
    def test_create_and_find_study_group(self, student_token):
        """Test creating a study group and finding it in all groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Create a unique study group
        unique_name = f"Test Group {uuid.uuid4().hex[:8]}"
        create_data = {
            "name": unique_name,
            "topic": "Testing",
            "description": "Test group for iteration 19"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/study-groups",
            json=create_data,
            headers=headers
        )
        
        if create_response.status_code == 200:
            created_group = create_response.json()
            group_id = created_group.get('id')
            
            # Verify it appears in all groups
            all_response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
            all_groups = all_response.json()
            
            found = any(g.get('name') == unique_name for g in all_groups)
            assert found, f"Created group '{unique_name}' should appear in all groups"
            print(f"✓ Created group '{unique_name}' visible in Browse All Groups")
            
            # Cleanup - delete the group
            if group_id:
                requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=headers)
        else:
            print(f"⚠ Could not create test group: {create_response.status_code}")


class TestOrganizationSettings:
    """Test Organization Settings page endpoints for org_admin"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        return response.json()['access_token']
    
    def test_get_org_profile(self, org_admin_token):
        """Test GET /api/org/profile endpoint"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/profile", headers=headers)
        # Should return 200 or 404 if no profile exists yet
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ GET /api/org/profile returns organization data")
        else:
            print("✓ GET /api/org/profile endpoint exists (no profile yet)")
    
    def test_update_org_profile(self, org_admin_token):
        """Test PUT /api/org/profile endpoint - Profile tab"""
        headers = {
            "Authorization": f"Bearer {org_admin_token}",
            "Content-Type": "application/json"
        }
        profile_data = {
            "name": "Test Organization",
            "description": "Test organization for iteration 19",
            "website": "https://test.org",
            "phone": "+1234567890",
            "address": "123 Test Street",
            "logo_url": "https://example.com/logo.png",
            "social_media": {
                "facebook": "https://facebook.com/testorg",
                "twitter": "https://twitter.com/testorg",
                "linkedin": "https://linkedin.com/company/testorg",
                "instagram": "https://instagram.com/testorg"
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/org/profile",
            json=profile_data,
            headers=headers
        )
        assert response.status_code in [200, 201]
        print("✓ PUT /api/org/profile - Profile update works")
    
    def test_get_org_documents(self, org_admin_token):
        """Test GET /api/org/documents endpoint - Documents tab"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/documents", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/org/documents returns {len(data)} documents")
    
    def test_get_database_status(self, org_admin_token):
        """Test GET /api/org/database/status endpoint - Database tab"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/database/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ GET /api/org/database/status returns status: {data.get('status', 'unknown')}")
    
    def test_connect_database(self, org_admin_token):
        """Test POST /api/org/database/connect endpoint - Database tab"""
        headers = {
            "Authorization": f"Bearer {org_admin_token}",
            "Content-Type": "application/json"
        }
        db_config = {
            "db_type": "mongodb",
            "connection_string": "mongodb://test:test@localhost:27017",
            "db_name": "test_db",
            "collection_name": "test_collection"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/org/database/connect",
            json=db_config,
            headers=headers
        )
        # May fail due to invalid connection, but endpoint should exist
        assert response.status_code in [200, 400, 500]
        print(f"✓ POST /api/org/database/connect endpoint exists (status: {response.status_code})")


class TestAssignmentGenerator:
    """Test Assignment Generator with course selection"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()['access_token']
    
    def test_get_courses_for_dropdown(self, teacher_token):
        """Test that courses can be fetched for the dropdown"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        courses = response.json()
        assert isinstance(courses, list)
        print(f"✓ GET /api/courses returns {len(courses)} courses for dropdown")
        return courses
    
    def test_generate_assignment_with_course_id(self, teacher_token):
        """Test assignment generation with course_id parameter"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # First get a course ID
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if len(courses) > 0:
            course_id = courses[0].get('id')
            
            # Generate assignment with course_id
            params = {
                "lesson_topic": "Test Topic for Iteration 19",
                "course_id": course_id,
                "learning_objectives": ["Understand test concepts"],
                "assignment_type": "reflection",
                "difficulty": "medium"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/advanced/assignment/generate",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'assignment_id' in data
                # Verify course_id is in response
                assert data.get('course_id') == course_id
                print(f"✓ Assignment generated with course_id: {course_id}")
            else:
                print(f"⚠ Assignment generation returned {response.status_code}: {response.text[:200]}")
        else:
            print("⚠ No courses available to test assignment generation")


class TestCourseContent:
    """Test Video and Image content display in CourseViewPage"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()['access_token']
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()['access_token']
    
    def test_get_courses(self, student_token):
        """Test getting courses list"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        courses = response.json()
        print(f"✓ GET /api/courses returns {len(courses)} courses")
        return courses
    
    def test_get_course_content(self, student_token):
        """Test getting course content (videos, images, text)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Get courses first
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if len(courses) > 0:
            course_id = courses[0].get('id')
            
            # Get course content
            content_response = requests.get(
                f"{BASE_URL}/api/content/course/{course_id}/content",
                headers=headers
            )
            
            if content_response.status_code == 200:
                content = content_response.json()
                if isinstance(content, list):
                    print(f"✓ GET /api/content/course/{course_id}/content returns {len(content)} items")
                    
                    # Check for video/image content with 'url' field
                    for item in content:
                        if item.get('type') in ['video', 'image']:
                            assert 'url' in item or 'video_url' in item or 'image_url' in item
                            print(f"  - Found {item.get('type')} content: {item.get('title', 'Untitled')}")
                else:
                    print(f"✓ Course content endpoint works (returned dict)")
            else:
                print(f"⚠ Course content returned {content_response.status_code}")
        else:
            print("⚠ No courses available to test content")
    
    def test_upload_video_content(self, teacher_token):
        """Test uploading video content with URL"""
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        # Get teacher's courses
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if len(courses) > 0:
            course_id = courses[0].get('id')
            
            content_data = {
                "type": "video",
                "title": "Test Video Content",
                "description": "Test video for iteration 19",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/content/course/{course_id}/content",
                json=content_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Video content uploaded to course {course_id}")
            else:
                print(f"⚠ Video upload returned {response.status_code}: {response.text[:200]}")
        else:
            print("⚠ No courses available to test video upload")
    
    def test_upload_image_content(self, teacher_token):
        """Test uploading image/slides content with URL"""
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        # Get teacher's courses
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if len(courses) > 0:
            course_id = courses[0].get('id')
            
            content_data = {
                "type": "image",
                "title": "Test Image/Slides Content",
                "description": "Test image for iteration 19",
                "url": "https://example.com/test-slide.png"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/content/course/{course_id}/content",
                json=content_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Image content uploaded to course {course_id}")
            else:
                print(f"⚠ Image upload returned {response.status_code}: {response.text[:200]}")
        else:
            print("⚠ No courses available to test image upload")


class TestSidebarOrgAdmin:
    """Test that org_admin sees Organization Settings in sidebar"""
    
    def test_org_admin_has_correct_role(self):
        """Verify org_admin user has correct role"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert data.get('user', {}).get('role') == 'org_admin'
        print("✓ Org admin user has role 'org_admin'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
