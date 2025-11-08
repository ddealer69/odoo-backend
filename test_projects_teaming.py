#!/usr/bin/env python3
"""
Test script for Projects & Teaming API endpoints
Tests all CRUD operations and advanced features
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = 'http://localhost:5000/api/v1'
HEADERS = {'Content-Type': 'application/json'}

# Test results tracking
test_results = {}

def mark_test_result(test_name, passed, details=""):
    """Mark test result for final summary"""
    test_results[test_name] = {
        'passed': passed,
        'details': details
    }

def print_response(response, title):
    """Helper function to print formatted response"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")

def test_project_crud():
    """Test all project CRUD operations"""
    print("\n🚀 TESTING PROJECT CRUD OPERATIONS")
    print("="*60)
    
    try:
        # 1. Create a new project
        today = date.today()
        project_data = {
            'project_code': 'TEST-2024-001',
            'name': 'Test Project API',
            'description': 'Testing project creation via API',
            'project_manager_id': 2,  # Assuming manager user has ID 2
            'start_date': today.isoformat(),
            'end_date': (today + timedelta(days=60)).isoformat(),
            'status': 'planned',
            'budget_amount': 30000.50
        }
        
        response = requests.post(f'{BASE_URL}/projects', 
                               headers=HEADERS, 
                               json=project_data)
        print_response(response, "CREATE PROJECT")
        
        if response.status_code == 201:
            project_id = response.json()['data']['id']
            print(f"✅ Created project with ID: {project_id}")
            
            # 2. Get the created project
            response = requests.get(f'{BASE_URL}/projects/{project_id}')
            print_response(response, f"GET PROJECT {project_id}")
            
            if response.status_code != 200:
                mark_test_result("Project CRUD", False, "Failed to get created project")
                return None
            
            # 3. Update the project
            update_data = {
                'name': 'Updated Test Project API',
                'status': 'in_progress',
                'budget_amount': 35000.00
            }
            
            response = requests.put(f'{BASE_URL}/projects/{project_id}',
                                  headers=HEADERS,
                                  json=update_data)
            print_response(response, f"UPDATE PROJECT {project_id}")
            
            if response.status_code != 200:
                mark_test_result("Project CRUD", False, "Failed to update project")
                return project_id
            
            # 4. Get all projects
            response = requests.get(f'{BASE_URL}/projects')
            print_response(response, "GET ALL PROJECTS")
            
            if response.status_code == 200:
                mark_test_result("Project CRUD", True, "All CRUD operations successful")
            else:
                mark_test_result("Project CRUD", False, "Failed to get all projects")
            
            return project_id
        else:
            mark_test_result("Project CRUD", False, f"Failed to create project: {response.status_code}")
            return None
            
    except Exception as e:
        mark_test_result("Project CRUD", False, f"Exception: {str(e)}")
        return None

def test_project_search_and_filter():
    """Test project search and filtering"""
    print("\n🔍 TESTING PROJECT SEARCH AND FILTERING")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 3
        
        # 1. Filter by status
        response = requests.get(f'{BASE_URL}/projects?status=in_progress')
        print_response(response, "FILTER PROJECTS BY STATUS")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Search by name
        response = requests.get(f'{BASE_URL}/projects?search=website')
        print_response(response, "SEARCH PROJECTS BY NAME")
        if response.status_code == 200:
            success_count += 1
        
        # 3. Include manager and members
        response = requests.get(f'{BASE_URL}/projects?include_manager=true&include_members=true')
        print_response(response, "GET PROJECTS WITH MANAGER AND MEMBERS")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Project Search & Filter", True, f"All {total_tests} filter tests passed")
        else:
            mark_test_result("Project Search & Filter", False, f"Only {success_count}/{total_tests} filter tests passed")
            
    except Exception as e:
        mark_test_result("Project Search & Filter", False, f"Exception: {str(e)}")

def test_project_members(project_id):
    """Test project member operations"""
    if not project_id:
        print("❌ Cannot test project members without valid project ID")
        mark_test_result("Project Members", False, "No valid project ID")
        return
    
    print("\n👥 TESTING PROJECT MEMBER OPERATIONS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 5
        
        # 1. Assign member to project
        member_data = {
            'user_id': 3,  # Assuming developer user has ID 3
            'role_in_project': 'Lead Developer'
        }
        
        response = requests.post(f'{BASE_URL}/projects/{project_id}/members',
                               headers=HEADERS,
                               json=member_data)
        print_response(response, f"ASSIGN MEMBER TO PROJECT {project_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 2. Assign another member
        member_data2 = {
            'user_id': 4,  # Assuming designer user has ID 4
            'role_in_project': 'UI Designer'
        }
        
        response = requests.post(f'{BASE_URL}/projects/{project_id}/members',
                               headers=HEADERS,
                               json=member_data2)
        print_response(response, f"ASSIGN ANOTHER MEMBER TO PROJECT {project_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 3. Get project members
        response = requests.get(f'{BASE_URL}/projects/{project_id}/members')
        print_response(response, f"GET PROJECT {project_id} MEMBERS")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Update member role
        update_data = {
            'role_in_project': 'Senior Developer'
        }
        
        response = requests.put(f'{BASE_URL}/projects/{project_id}/members/3',
                              headers=HEADERS,
                              json=update_data)
        print_response(response, f"UPDATE MEMBER ROLE IN PROJECT {project_id}")
        if response.status_code == 200:
            success_count += 1
        
        # 5. Remove a member
        response = requests.delete(f'{BASE_URL}/projects/{project_id}/members/4')
        print_response(response, f"REMOVE MEMBER FROM PROJECT {project_id}")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Project Members", True, f"All {total_tests} member operations passed")
        else:
            mark_test_result("Project Members", False, f"Only {success_count}/{total_tests} member operations passed")
            
    except Exception as e:
        mark_test_result("Project Members", False, f"Exception: {str(e)}")

def test_user_projects():
    """Test user projects endpoint"""
    print("\n👤 TESTING USER PROJECTS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 2
        
        # Get projects for user ID 2 (manager)
        response = requests.get(f'{BASE_URL}/users/2/projects')
        print_response(response, "GET USER 2 PROJECTS")
        if response.status_code == 200:
            success_count += 1
        
        # Get projects for user ID 3 (developer)
        response = requests.get(f'{BASE_URL}/users/3/projects')
        print_response(response, "GET USER 3 PROJECTS")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("User Projects", True, f"All {total_tests} user project tests passed")
        else:
            mark_test_result("User Projects", False, f"Only {success_count}/{total_tests} user project tests passed")
            
    except Exception as e:
        mark_test_result("User Projects", False, f"Exception: {str(e)}")

def test_project_statistics():
    """Test project statistics endpoint"""
    print("\n📊 TESTING PROJECT STATISTICS")
    print("="*60)
    
    try:
        response = requests.get(f'{BASE_URL}/projects/stats')
        print_response(response, "GET PROJECT STATISTICS")
        
        if response.status_code == 200:
            mark_test_result("Project Statistics", True, "Statistics endpoint working")
        else:
            mark_test_result("Project Statistics", False, f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        mark_test_result("Project Statistics", False, f"Exception: {str(e)}")

def test_all_project_members():
    """Test all project members endpoint"""
    print("\n📋 TESTING ALL PROJECT MEMBERS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 3
        
        # Get all project members
        response = requests.get(f'{BASE_URL}/project-members')
        print_response(response, "GET ALL PROJECT MEMBERS")
        if response.status_code == 200:
            success_count += 1
        
        # Filter by project
        response = requests.get(f'{BASE_URL}/project-members?project_id=1')
        print_response(response, "GET PROJECT MEMBERS BY PROJECT ID")
        if response.status_code == 200:
            success_count += 1
        
        # Filter by user
        response = requests.get(f'{BASE_URL}/project-members?user_id=3')
        print_response(response, "GET PROJECT MEMBERS BY USER ID")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("All Project Members", True, f"All {total_tests} member listing tests passed")
        else:
            mark_test_result("All Project Members", False, f"Only {success_count}/{total_tests} member listing tests passed")
            
    except Exception as e:
        mark_test_result("All Project Members", False, f"Exception: {str(e)}")

def test_error_cases():
    """Test error handling"""
    print("\n❌ TESTING ERROR CASES")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Create project with invalid data
        invalid_data = {
            'project_code': '',  # Empty project code
            'name': ''  # Empty name
        }
        
        response = requests.post(f'{BASE_URL}/projects',
                               headers=HEADERS,
                               json=invalid_data)
        print_response(response, "CREATE PROJECT WITH INVALID DATA")
        if response.status_code == 400:  # Should return error
            success_count += 1
        
        # 2. Get non-existent project
        response = requests.get(f'{BASE_URL}/projects/999999')
        print_response(response, "GET NON-EXISTENT PROJECT")
        if response.status_code == 404:  # Should return not found
            success_count += 1
        
        # 3. Assign non-existent user to project
        invalid_member = {
            'user_id': 999999,  # Non-existent user
            'role_in_project': 'Developer'
        }
        
        response = requests.post(f'{BASE_URL}/projects/1/members',
                               headers=HEADERS,
                               json=invalid_member)
        print_response(response, "ASSIGN NON-EXISTENT USER TO PROJECT")
        if response.status_code in [400, 404]:  # Should return error
            success_count += 1
        
        # 4. Create project with duplicate code
        duplicate_data = {
            'project_code': 'WEB-2024-001',  # Existing project code
            'name': 'Duplicate Project'
        }
        
        response = requests.post(f'{BASE_URL}/projects',
                               headers=HEADERS,
                               json=duplicate_data)
        print_response(response, "CREATE PROJECT WITH DUPLICATE CODE")
        if response.status_code == 400:  # Should return error
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Error Handling", True, f"All {total_tests} error cases handled correctly")
        else:
            mark_test_result("Error Handling", False, f"Only {success_count}/{total_tests} error cases handled correctly")
            
    except Exception as e:
        mark_test_result("Error Handling", False, f"Exception: {str(e)}")

def test_date_validation():
    """Test date validation"""
    print("\n📅 TESTING DATE VALIDATION")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 2
        
        # 1. Invalid date format
        invalid_date_data = {
            'project_code': 'DATE-TEST-001',
            'name': 'Date Test Project',
            'start_date': '2024-13-45',  # Invalid date
            'end_date': '2024-12-31'
        }
        
        response = requests.post(f'{BASE_URL}/projects',
                               headers=HEADERS,
                               json=invalid_date_data)
        print_response(response, "CREATE PROJECT WITH INVALID DATE FORMAT")
        if response.status_code == 400:  # Should return error
            success_count += 1
        
        # 2. End date before start date
        today = date.today()
        invalid_logic_data = {
            'project_code': 'DATE-TEST-002',
            'name': 'Date Logic Test Project',
            'start_date': today.isoformat(),
            'end_date': (today - timedelta(days=30)).isoformat()  # End before start
        }
        
        response = requests.post(f'{BASE_URL}/projects',
                               headers=HEADERS,
                               json=invalid_logic_data)
        print_response(response, "CREATE PROJECT WITH END DATE BEFORE START DATE")
        if response.status_code == 400:  # Should return error
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Date Validation", True, f"All {total_tests} date validation tests passed")
        else:
            mark_test_result("Date Validation", False, f"Only {success_count}/{total_tests} date validation tests passed")
            
    except Exception as e:
        mark_test_result("Date Validation", False, f"Exception: {str(e)}")

def cleanup_test_data(project_id):
    """Clean up test data"""
    if project_id:
        print(f"\n🧹 CLEANING UP TEST DATA")
        print("="*60)
        
        try:
            response = requests.delete(f'{BASE_URL}/projects/{project_id}')
            print_response(response, f"DELETE TEST PROJECT {project_id}")
            
            if response.status_code == 200:
                mark_test_result("Cleanup", True, "Test data cleaned up successfully")
            else:
                mark_test_result("Cleanup", False, f"Failed to cleanup: {response.status_code}")
                
        except Exception as e:
            mark_test_result("Cleanup", False, f"Exception during cleanup: {str(e)}")

def print_final_verdict():
    """Print final test results summary"""
    print(f"\n{'='*80}")
    print("🏁 FINAL TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\n{'='*80}")
    print("📋 DETAILED RESULTS:")
    print(f"{'='*80}")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status:10} | {test_name:25} | {result['details']}")
    
    print(f"\n{'='*80}")
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! The Projects & Teaming API is working perfectly!")
    else:
        print(f"⚠️  {failed_tests} TEST(S) FAILED. Please review the failing tests above.")
    print(f"{'='*80}")
    
    return failed_tests == 0

def main():
    """Main test function"""
    print("🧪 PROJECTS & TEAMING API COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("Make sure the Flask application is running on http://localhost:5000")
    print("And the database is initialized with sample data")
    
    try:
        # Test basic CRUD operations
        project_id = test_project_crud()
        
        # Test search and filtering
        test_project_search_and_filter()
        
        # Test project member operations
        test_project_members(project_id)
        
        # Test user projects
        test_user_projects()
        
        # Test statistics
        test_project_statistics()
        
        # Test all project members
        test_all_project_members()
        
        # Test error cases
        test_error_cases()
        
        # Test date validation
        test_date_validation()
        
        # Clean up
        cleanup_test_data(project_id)
        
        # Print final verdict
        all_passed = print_final_verdict()
        
        # Exit with appropriate code
        return 0 if all_passed else 1
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to Flask application")
        print("Make sure the application is running on http://localhost:5000")
        mark_test_result("Connection Test", False, "Could not connect to Flask application")
        print_final_verdict()
        return 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        mark_test_result("General Test", False, f"Unexpected error: {str(e)}")
        print_final_verdict()
        return 1

if __name__ == '__main__':
    import sys
    exit_code = main()
    sys.exit(exit_code)