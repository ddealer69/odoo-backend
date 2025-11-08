#!/usr/bin/env python3
"""
Comprehensive test script for Flask SQLAlchemy User Management API
Tests all CRUD operations for roles, users, and user-role assignments
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
API_PREFIX = "/api/v1"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL + API_PREFIX
        self.test_results = []
        
    def log_test(self, test_name, success, response=None, error=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'name': test_name,
            'success': success,
            'response': response,
            'error': error
        })
        print(f"{status} {test_name}")
        if response and success:
            print(f"    Response: {response.get('message', 'OK')}")
        elif error:
            print(f"    Error: {error}")
    
    def make_request(self, method, endpoint, data=None, use_api_prefix=True):
        """Make HTTP request"""
        if use_api_prefix:
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
        except Exception as e:
            return None, str(e)
    
    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🏥 Testing Health Endpoints")
        print("-" * 40)
        
        # Test root health check
        response, error = self.make_request('GET', '/', use_api_prefix=False)
        if error:
            self.log_test("Health Check (/)", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Health Check (/)", success, response.json() if success else None)
        
        # Test database connection
        response, error = self.make_request('GET', '/connection', use_api_prefix=False)
        if error:
            self.log_test("Database Connection", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Database Connection", success, response.json() if success else None)
    
    def test_role_crud(self):
        """Test Role CRUD operations"""
        print("\n👑 Testing Role CRUD Operations")
        print("-" * 40)
        
        # 1. Create Role
        role_data = {
            "name": "Test Role",
            "description": "Test role for API testing"
        }
        response, error = self.make_request('POST', '/roles', role_data)
        if error:
            self.log_test("Create Role", False, error=error)
            return None
        
        success = response.status_code == 201
        role_id = None
        if success:
            role_id = response.json().get('data', {}).get('id')
        self.log_test("Create Role", success, response.json() if success else None)
        
        if not role_id:
            print("    ⚠️  Cannot continue role tests without role ID")
            return None
        
        # 2. Get All Roles
        response, error = self.make_request('GET', '/roles')
        if error:
            self.log_test("Get All Roles", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get All Roles", success, response.json() if success else None)
        
        # 3. Get Single Role
        response, error = self.make_request('GET', f'/roles/{role_id}')
        if error:
            self.log_test("Get Single Role", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Single Role", success, response.json() if success else None)
        
        # 4. Update Role
        update_data = {
            "name": "Updated Test Role",
            "description": "Updated description"
        }
        response, error = self.make_request('PUT', f'/roles/{role_id}', update_data)
        if error:
            self.log_test("Update Role", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Update Role", success, response.json() if success else None)
        
        return role_id
    
    def test_user_crud(self):
        """Test User CRUD operations"""
        print("\n👤 Testing User CRUD Operations")
        print("-" * 40)
        
        # 1. Create User
        user_data = {
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password": "testpassword123",
            "hourly_rate": 75.50,
            "is_active": True
        }
        response, error = self.make_request('POST', '/users', user_data)
        if error:
            self.log_test("Create User", False, error=error)
            return None
        
        success = response.status_code == 201
        user_id = None
        if success:
            user_id = response.json().get('data', {}).get('id')
        self.log_test("Create User", success, response.json() if success else None)
        
        if not user_id:
            print("    ⚠️  Cannot continue user tests without user ID")
            return None
        
        # 2. Get All Users
        response, error = self.make_request('GET', '/users')
        if error:
            self.log_test("Get All Users", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get All Users", success, response.json() if success else None)
        
        # 3. Get All Users with Roles
        response, error = self.make_request('GET', '/users?include_roles=true')
        if error:
            self.log_test("Get Users with Roles", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Users with Roles", success, response.json() if success else None)
        
        # 4. Get Single User
        response, error = self.make_request('GET', f'/users/{user_id}')
        if error:
            self.log_test("Get Single User", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Single User", success, response.json() if success else None)
        
        # 5. Update User
        update_data = {
            "full_name": "Updated Test User",
            "hourly_rate": 85.00,
            "is_active": True
        }
        response, error = self.make_request('PUT', f'/users/{user_id}', update_data)
        if error:
            self.log_test("Update User", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Update User", success, response.json() if success else None)
        
        return user_id
    
    def test_user_role_operations(self, user_id, role_id):
        """Test User-Role assignment operations"""
        print("\n🔗 Testing User-Role Operations")
        print("-" * 40)
        
        if not user_id or not role_id:
            print("    ⚠️  Cannot test user-role operations without valid user and role IDs")
            return
        
        # 1. Assign Role to User
        assign_data = {"role_id": role_id}
        response, error = self.make_request('POST', f'/users/{user_id}/roles', assign_data)
        if error:
            self.log_test("Assign Role to User", False, error=error)
        else:
            success = response.status_code == 201
            self.log_test("Assign Role to User", success, response.json() if success else None)
        
        # 2. Get User Roles
        response, error = self.make_request('GET', f'/users/{user_id}/roles')
        if error:
            self.log_test("Get User Roles", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get User Roles", success, response.json() if success else None)
        
        # 3. Get All User-Role Assignments
        response, error = self.make_request('GET', '/user-roles')
        if error:
            self.log_test("Get All User-Role Assignments", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get All User-Role Assignments", success, response.json() if success else None)
        
        # 4. Remove Role from User
        response, error = self.make_request('DELETE', f'/users/{user_id}/roles/{role_id}')
        if error:
            self.log_test("Remove Role from User", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Remove Role from User", success, response.json() if success else None)
    
    def test_cleanup(self, user_id, role_id):
        """Clean up test data"""
        print("\n🧹 Cleaning Up Test Data")
        print("-" * 40)
        
        # Delete User (if exists)
        if user_id:
            response, error = self.make_request('DELETE', f'/users/{user_id}')
            if error:
                self.log_test("Delete Test User", False, error=error)
            else:
                success = response.status_code == 200
                self.log_test("Delete Test User", success, response.json() if success else None)
        
        # Delete Role (if exists)
        if role_id:
            response, error = self.make_request('DELETE', f'/roles/{role_id}')
            if error:
                self.log_test("Delete Test Role", False, error=error)
            else:
                success = response.status_code == 200
                self.log_test("Delete Test Role", success, response.json() if success else None)
    
    def test_statistics(self):
        """Test statistics endpoint"""
        print("\n📊 Testing Statistics")
        print("-" * 40)
        
        response, error = self.make_request('GET', '/stats')
        if error:
            self.log_test("Get Statistics", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Statistics", success, response.json() if success else None)
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling")
        print("-" * 40)
        
        # Test 404 - Non-existent user
        response, error = self.make_request('GET', '/users/99999')
        if error:
            self.log_test("404 Error Handling", False, error=error)
        else:
            success = response.status_code == 404
            self.log_test("404 Error Handling", success)
        
        # Test 400 - Invalid data
        invalid_user = {"email": "invalid-email", "full_name": "Test"}
        response, error = self.make_request('POST', '/users', invalid_user)
        if error:
            self.log_test("400 Error Handling", False, error=error)
        else:
            success = response.status_code == 400
            self.log_test("400 Error Handling", success)
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive API Tests")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test health endpoints
        self.test_health_endpoints()
        
        # Test statistics
        self.test_statistics()
        
        # Test CRUD operations
        role_id = self.test_role_crud()
        user_id = self.test_user_crud()
        
        # Test user-role operations
        self.test_user_role_operations(user_id, role_id)
        
        # Test error handling
        self.test_error_handling()
        
        # Clean up test data
        self.test_cleanup(user_id, role_id)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['name']}: {test['error']}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if failed_tests == 0 else '⚠️  Some tests failed. Check your Flask app and database.'}")

def main():
    """Main function"""
    print("Make sure your Flask app is running on http://localhost:5000")
    print("Initialize the database first with: python3 init_db.py")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Flask app is not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Flask app: {e}")
        print("Make sure the app is running with: python3 app.py")
        return
    
    # Run all tests
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()