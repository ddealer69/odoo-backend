#!/usr/bin/env python3
"""
Test script for Tasks & Collaboration API endpoints
Tests all CRUD operations for tasks, assignments, comments, and attachments
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

def test_task_crud():
    """Test all task CRUD operations"""
    print("\n🚀 TESTING TASK CRUD OPERATIONS")
    print("="*60)
    
    try:
        # 1. Create a new task
        today = date.today()
        task_data = {
            'project_id': 1,  # Assuming project 1 exists
            'title': 'Test Task API',
            'description': 'Testing task creation via API',
            'priority': 'high',
            'state': 'new',
            'due_date': (today + timedelta(days=7)).isoformat(),
            'created_by': 2  # Assuming user 2 exists
        }
        
        response = requests.post(f'{BASE_URL}/tasks', 
                               headers=HEADERS, 
                               json=task_data)
        print_response(response, "CREATE TASK")
        
        if response.status_code == 201:
            task_id = response.json()['data']['id']
            print(f"✅ Created task with ID: {task_id}")
            
            # 2. Get the created task
            response = requests.get(f'{BASE_URL}/tasks/{task_id}')
            print_response(response, f"GET TASK {task_id}")
            
            if response.status_code != 200:
                mark_test_result("Task CRUD", False, "Failed to get created task")
                return None
            
            # 3. Update the task
            update_data = {
                'title': 'Updated Test Task API',
                'state': 'in_progress',
                'priority': 'urgent'
            }
            
            response = requests.put(f'{BASE_URL}/tasks/{task_id}',
                                  headers=HEADERS,
                                  json=update_data)
            print_response(response, f"UPDATE TASK {task_id}")
            
            if response.status_code != 200:
                mark_test_result("Task CRUD", False, "Failed to update task")
                return task_id
            
            # 4. Get all tasks
            response = requests.get(f'{BASE_URL}/tasks')
            print_response(response, "GET ALL TASKS")
            
            if response.status_code == 200:
                mark_test_result("Task CRUD", True, "All CRUD operations successful")
            else:
                mark_test_result("Task CRUD", False, "Failed to get all tasks")
            
            return task_id
        else:
            mark_test_result("Task CRUD", False, f"Failed to create task: {response.status_code}")
            return None
            
    except Exception as e:
        mark_test_result("Task CRUD", False, f"Exception: {str(e)}")
        return None

def test_task_filtering():
    """Test task filtering and search"""
    print("\n🔍 TESTING TASK FILTERING")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Filter by state
        response = requests.get(f'{BASE_URL}/tasks?state=in_progress')
        print_response(response, "FILTER TASKS BY STATE")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Filter by priority
        response = requests.get(f'{BASE_URL}/tasks?priority=high')
        print_response(response, "FILTER TASKS BY PRIORITY")
        if response.status_code == 200:
            success_count += 1
        
        # 3. Filter by project
        response = requests.get(f'{BASE_URL}/tasks?project_id=1')
        print_response(response, "FILTER TASKS BY PROJECT")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Get tasks with relations
        response = requests.get(f'{BASE_URL}/tasks?include_relations=true')
        print_response(response, "GET TASKS WITH RELATIONS")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Task Filtering", True, f"All {total_tests} filter tests passed")
        else:
            mark_test_result("Task Filtering", False, f"Only {success_count}/{total_tests} filter tests passed")
            
    except Exception as e:
        mark_test_result("Task Filtering", False, f"Exception: {str(e)}")

def test_task_assignments(task_id):
    """Test task assignment operations"""
    if not task_id:
        print("❌ Cannot test task assignments without valid task ID")
        mark_test_result("Task Assignments", False, "No valid task ID")
        return
    
    print("\n👥 TESTING TASK ASSIGNMENT OPERATIONS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Assign user to task
        assignment_data = {
            'user_id': 3  # Assuming user 3 exists
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/assignments',
                               headers=HEADERS,
                               json=assignment_data)
        print_response(response, f"ASSIGN USER TO TASK {task_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 2. Assign another user
        assignment_data2 = {
            'user_id': 4  # Assuming user 4 exists
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/assignments',
                               headers=HEADERS,
                               json=assignment_data2)
        print_response(response, f"ASSIGN ANOTHER USER TO TASK {task_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 3. Get task assignments
        response = requests.get(f'{BASE_URL}/tasks/{task_id}/assignments')
        print_response(response, f"GET TASK {task_id} ASSIGNMENTS")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Remove user from task
        response = requests.delete(f'{BASE_URL}/tasks/{task_id}/assignments/4')
        print_response(response, f"REMOVE USER FROM TASK {task_id}")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Task Assignments", True, f"All {total_tests} assignment operations passed")
        else:
            mark_test_result("Task Assignments", False, f"Only {success_count}/{total_tests} assignment operations passed")
            
    except Exception as e:
        mark_test_result("Task Assignments", False, f"Exception: {str(e)}")

def test_task_comments(task_id):
    """Test task comment operations"""
    if not task_id:
        print("❌ Cannot test task comments without valid task ID")
        mark_test_result("Task Comments", False, "No valid task ID")
        return
    
    print("\n💬 TESTING TASK COMMENT OPERATIONS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Add comment to task
        comment_data = {
            'user_id': 2,
            'comment': 'This is a test comment'
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/comments',
                               headers=HEADERS,
                               json=comment_data)
        print_response(response, f"ADD COMMENT TO TASK {task_id}")
        if response.status_code == 201:
            comment_id = response.json()['data']['id']
            success_count += 1
        else:
            comment_id = None
        
        # 2. Add another comment
        comment_data2 = {
            'user_id': 3,
            'comment': 'Another test comment with more details'
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/comments',
                               headers=HEADERS,
                               json=comment_data2)
        print_response(response, f"ADD ANOTHER COMMENT TO TASK {task_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 3. Get all comments for task
        response = requests.get(f'{BASE_URL}/tasks/{task_id}/comments')
        print_response(response, f"GET TASK {task_id} COMMENTS")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Delete a comment
        if comment_id:
            response = requests.delete(f'{BASE_URL}/tasks/{task_id}/comments/{comment_id}')
            print_response(response, f"DELETE COMMENT FROM TASK {task_id}")
            if response.status_code == 200:
                success_count += 1
        else:
            print("⚠️  Skipping delete comment test (no comment ID)")
            success_count += 1  # Don't penalize for this
        
        if success_count == total_tests:
            mark_test_result("Task Comments", True, f"All {total_tests} comment operations passed")
        else:
            mark_test_result("Task Comments", False, f"Only {success_count}/{total_tests} comment operations passed")
            
    except Exception as e:
        mark_test_result("Task Comments", False, f"Exception: {str(e)}")

def test_task_attachments(task_id):
    """Test task attachment operations"""
    if not task_id:
        print("❌ Cannot test task attachments without valid task ID")
        mark_test_result("Task Attachments", False, "No valid task ID")
        return
    
    print("\n📎 TESTING TASK ATTACHMENT OPERATIONS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Upload attachment to task
        attachment_data = {
            'uploaded_by': 2,
            'file_name': 'test_document.pdf',
            'file_url': 'https://example.com/files/test_document.pdf'
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/attachments',
                               headers=HEADERS,
                               json=attachment_data)
        print_response(response, f"UPLOAD ATTACHMENT TO TASK {task_id}")
        if response.status_code == 201:
            attachment_id = response.json()['data']['id']
            success_count += 1
        else:
            attachment_id = None
        
        # 2. Upload another attachment
        attachment_data2 = {
            'uploaded_by': 3,
            'file_name': 'screenshot.png',
            'file_url': 'https://example.com/files/screenshot.png'
        }
        
        response = requests.post(f'{BASE_URL}/tasks/{task_id}/attachments',
                               headers=HEADERS,
                               json=attachment_data2)
        print_response(response, f"UPLOAD ANOTHER ATTACHMENT TO TASK {task_id}")
        if response.status_code == 201:
            success_count += 1
        
        # 3. Get all attachments for task
        response = requests.get(f'{BASE_URL}/tasks/{task_id}/attachments')
        print_response(response, f"GET TASK {task_id} ATTACHMENTS")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Delete an attachment
        if attachment_id:
            response = requests.delete(f'{BASE_URL}/tasks/{task_id}/attachments/{attachment_id}')
            print_response(response, f"DELETE ATTACHMENT FROM TASK {task_id}")
            if response.status_code == 200:
                success_count += 1
        else:
            print("⚠️  Skipping delete attachment test (no attachment ID)")
            success_count += 1  # Don't penalize for this
        
        if success_count == total_tests:
            mark_test_result("Task Attachments", True, f"All {total_tests} attachment operations passed")
        else:
            mark_test_result("Task Attachments", False, f"Only {success_count}/{total_tests} attachment operations passed")
            
    except Exception as e:
        mark_test_result("Task Attachments", False, f"Exception: {str(e)}")

def test_project_tasks():
    """Test getting tasks by project"""
    print("\n📁 TESTING PROJECT TASKS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 2
        
        # 1. Get all tasks for project 1
        response = requests.get(f'{BASE_URL}/projects/1/tasks')
        print_response(response, "GET PROJECT 1 TASKS")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Get tasks filtered by state
        response = requests.get(f'{BASE_URL}/projects/1/tasks?state=in_progress')
        print_response(response, "GET PROJECT 1 TASKS (IN PROGRESS)")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Project Tasks", True, f"All {total_tests} project task tests passed")
        else:
            mark_test_result("Project Tasks", False, f"Only {success_count}/{total_tests} project task tests passed")
            
    except Exception as e:
        mark_test_result("Project Tasks", False, f"Exception: {str(e)}")

def test_user_tasks():
    """Test getting tasks by user"""
    print("\n👤 TESTING USER TASKS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 2
        
        # 1. Get tasks for user 2
        response = requests.get(f'{BASE_URL}/users/2/tasks')
        print_response(response, "GET USER 2 TASKS")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Get tasks for user 3
        response = requests.get(f'{BASE_URL}/users/3/tasks')
        print_response(response, "GET USER 3 TASKS")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("User Tasks", True, f"All {total_tests} user task tests passed")
        else:
            mark_test_result("User Tasks", False, f"Only {success_count}/{total_tests} user task tests passed")
            
    except Exception as e:
        mark_test_result("User Tasks", False, f"Exception: {str(e)}")

def test_task_statistics():
    """Test task statistics endpoint"""
    print("\n📊 TESTING TASK STATISTICS")
    print("="*60)
    
    try:
        response = requests.get(f'{BASE_URL}/tasks/stats')
        print_response(response, "GET TASK STATISTICS")
        
        if response.status_code == 200:
            mark_test_result("Task Statistics", True, "Statistics endpoint working")
        else:
            mark_test_result("Task Statistics", False, f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        mark_test_result("Task Statistics", False, f"Exception: {str(e)}")

def test_error_cases():
    """Test error handling"""
    print("\n❌ TESTING ERROR CASES")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 5
        
        # 1. Create task with invalid data
        invalid_data = {
            'title': 'Test Task'
            # Missing required fields
        }
        
        response = requests.post(f'{BASE_URL}/tasks',
                               headers=HEADERS,
                               json=invalid_data)
        print_response(response, "CREATE TASK WITH INVALID DATA")
        if response.status_code == 400:
            success_count += 1
        
        # 2. Get non-existent task
        response = requests.get(f'{BASE_URL}/tasks/999999')
        print_response(response, "GET NON-EXISTENT TASK")
        if response.status_code == 404:
            success_count += 1
        
        # 3. Assign non-existent user to task
        invalid_assignment = {
            'user_id': 999999
        }
        
        response = requests.post(f'{BASE_URL}/tasks/1/assignments',
                               headers=HEADERS,
                               json=invalid_assignment)
        print_response(response, "ASSIGN NON-EXISTENT USER TO TASK")
        if response.status_code in [400, 404]:
            success_count += 1
        
        # 4. Create task with invalid priority
        invalid_priority_data = {
            'project_id': 1,
            'title': 'Test Task',
            'priority': 'super_urgent',  # Invalid priority
            'created_by': 2
        }
        
        response = requests.post(f'{BASE_URL}/tasks',
                               headers=HEADERS,
                               json=invalid_priority_data)
        print_response(response, "CREATE TASK WITH INVALID PRIORITY")
        if response.status_code == 400:
            success_count += 1
        
        # 5. Add empty comment
        empty_comment = {
            'comment': '   ',  # Empty comment
            'user_id': 2
        }
        
        response = requests.post(f'{BASE_URL}/tasks/1/comments',
                               headers=HEADERS,
                               json=empty_comment)
        print_response(response, "ADD EMPTY COMMENT")
        if response.status_code == 400:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Error Handling", True, f"All {total_tests} error cases handled correctly")
        else:
            mark_test_result("Error Handling", False, f"Only {success_count}/{total_tests} error cases handled correctly")
            
    except Exception as e:
        mark_test_result("Error Handling", False, f"Exception: {str(e)}")

def cleanup_test_data(task_id):
    """Clean up test data"""
    if task_id:
        print(f"\n🧹 CLEANING UP TEST DATA")
        print("="*60)
        
        try:
            response = requests.delete(f'{BASE_URL}/tasks/{task_id}')
            print_response(response, f"DELETE TEST TASK {task_id}")
            
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
        print("🎉 ALL TESTS PASSED! The Tasks & Collaboration API is working perfectly!")
    else:
        print(f"⚠️  {failed_tests} TEST(S) FAILED. Please review the failing tests above.")
    print(f"{'='*80}")
    
    return failed_tests == 0

def main():
    """Main test function"""
    print("🧪 TASKS & COLLABORATION API COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("Make sure the Flask application is running on http://localhost:5000")
    print("And the database is initialized with sample data")
    
    try:
        # Test basic CRUD operations
        task_id = test_task_crud()
        
        # Test filtering
        test_task_filtering()
        
        # Test assignments
        test_task_assignments(task_id)
        
        # Test comments
        test_task_comments(task_id)
        
        # Test attachments
        test_task_attachments(task_id)
        
        # Test project tasks
        test_project_tasks()
        
        # Test user tasks
        test_user_tasks()
        
        # Test statistics
        test_task_statistics()
        
        # Test error cases
        test_error_cases()
        
        # Clean up
        cleanup_test_data(task_id)
        
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
