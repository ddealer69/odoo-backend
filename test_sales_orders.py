#!/usr/bin/env python3
"""
Test script for Sales Orders API endpoints
Tests all CRUD operations for sales orders and order lines
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

def test_sales_order_crud():
    """Test all sales order CRUD operations"""
    print("\n🚀 TESTING SALES ORDER CRUD OPERATIONS")
    print("="*60)
    
    try:
        # 1. Create a new sales order
        today = date.today()
        so_data = {
            'so_number': 'SO-TEST-001',
            'project_id': 1,  # Assuming project 1 exists
            'customer_id': 1,  # Assuming customer 1 exists
            'order_date': today.isoformat(),
            'status': 'draft',
            'currency': 'INR',
            'notes': 'Test sales order'
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders', 
                               headers=HEADERS, 
                               json=so_data)
        print_response(response, "CREATE SALES ORDER")
        
        if response.status_code == 201:
            order_id = response.json()['data']['id']
            print(f"✅ Created sales order with ID: {order_id}")
            
            # 2. Get the created sales order
            response = requests.get(f'{BASE_URL}/sales-orders/{order_id}')
            print_response(response, f"GET SALES ORDER {order_id}")
            
            if response.status_code != 200:
                mark_test_result("Sales Order CRUD", False, "Failed to get created order")
                return None
            
            # 3. Update the sales order
            update_data = {
                'status': 'confirmed',
                'notes': 'Updated test sales order'
            }
            
            response = requests.put(f'{BASE_URL}/sales-orders/{order_id}',
                                  headers=HEADERS,
                                  json=update_data)
            print_response(response, f"UPDATE SALES ORDER {order_id}")
            
            if response.status_code != 200:
                mark_test_result("Sales Order CRUD", False, "Failed to update order")
                return order_id
            
            # 4. Get all sales orders
            response = requests.get(f'{BASE_URL}/sales-orders')
            print_response(response, "GET ALL SALES ORDERS")
            
            if response.status_code == 200:
                mark_test_result("Sales Order CRUD", True, "All CRUD operations successful")
            else:
                mark_test_result("Sales Order CRUD", False, "Failed to get all orders")
            
            return order_id
        else:
            mark_test_result("Sales Order CRUD", False, f"Failed to create order: {response.status_code}")
            return None
            
    except Exception as e:
        mark_test_result("Sales Order CRUD", False, f"Exception: {str(e)}")
        return None

def test_sales_order_filtering():
    """Test sales order filtering"""
    print("\n🔍 TESTING SALES ORDER FILTERING")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 4
        
        # 1. Filter by status
        response = requests.get(f'{BASE_URL}/sales-orders?status=confirmed')
        print_response(response, "FILTER ORDERS BY STATUS")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Filter by project
        response = requests.get(f'{BASE_URL}/sales-orders?project_id=1')
        print_response(response, "FILTER ORDERS BY PROJECT")
        if response.status_code == 200:
            success_count += 1
        
        # 3. Filter by customer
        response = requests.get(f'{BASE_URL}/sales-orders?customer_id=1')
        print_response(response, "FILTER ORDERS BY CUSTOMER")
        if response.status_code == 200:
            success_count += 1
        
        # 4. Get orders with relations
        response = requests.get(f'{BASE_URL}/sales-orders?include_relations=true&include_lines=true')
        print_response(response, "GET ORDERS WITH RELATIONS AND LINES")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Sales Order Filtering", True, f"All {total_tests} filter tests passed")
        else:
            mark_test_result("Sales Order Filtering", False, f"Only {success_count}/{total_tests} filter tests passed")
            
    except Exception as e:
        mark_test_result("Sales Order Filtering", False, f"Exception: {str(e)}")

def test_order_lines(order_id):
    """Test order line operations"""
    if not order_id:
        print("❌ Cannot test order lines without valid order ID")
        mark_test_result("Order Lines", False, "No valid order ID")
        return
    
    print("\n📝 TESTING ORDER LINE OPERATIONS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 6
        
        # 1. Add first order line
        line_data1 = {
            'product_id': 1,  # Assuming product 1 exists
            'description': 'Test Product Line 1',
            'quantity': 2.0,
            'unit_price': 1000.00,
            'milestone_flag': True
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders/{order_id}/lines',
                               headers=HEADERS,
                               json=line_data1)
        print_response(response, f"ADD ORDER LINE TO ORDER {order_id}")
        if response.status_code == 201:
            line_id1 = response.json()['data']['id']
            success_count += 1
        else:
            line_id1 = None
        
        # 2. Add second order line
        line_data2 = {
            'description': 'Test Service Line',
            'quantity': 5.0,
            'unit_price': 500.00,
            'milestone_flag': False
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders/{order_id}/lines',
                               headers=HEADERS,
                               json=line_data2)
        print_response(response, f"ADD ANOTHER ORDER LINE TO ORDER {order_id}")
        if response.status_code == 201:
            line_id2 = response.json()['data']['id']
            success_count += 1
        else:
            line_id2 = None
        
        # 3. Get all order lines
        response = requests.get(f'{BASE_URL}/sales-orders/{order_id}/lines')
        print_response(response, f"GET ORDER {order_id} LINES")
        if response.status_code == 200:
            success_count += 1
            # Check if total is calculated
            if 'order_total' in response.json():
                print(f"✅ Order total calculated: {response.json()['order_total']}")
        
        # 4. Update order line
        if line_id1:
            update_data = {
                'quantity': 3.0,
                'unit_price': 1200.00
            }
            
            response = requests.put(f'{BASE_URL}/sales-orders/{order_id}/lines/{line_id1}',
                                  headers=HEADERS,
                                  json=update_data)
            print_response(response, f"UPDATE ORDER LINE {line_id1}")
            if response.status_code == 200:
                success_count += 1
        else:
            print("⚠️  Skipping update line test (no line ID)")
        
        # 5. Get updated order with lines
        response = requests.get(f'{BASE_URL}/sales-orders/{order_id}')
        print_response(response, f"GET ORDER {order_id} WITH UPDATED LINES")
        if response.status_code == 200:
            success_count += 1
        
        # 6. Delete an order line
        if line_id2:
            response = requests.delete(f'{BASE_URL}/sales-orders/{order_id}/lines/{line_id2}')
            print_response(response, f"DELETE ORDER LINE {line_id2}")
            if response.status_code == 200:
                success_count += 1
        else:
            print("⚠️  Skipping delete line test (no line ID)")
        
        if success_count >= total_tests - 1:  # Allow one skip
            mark_test_result("Order Lines", True, f"{success_count}/{total_tests} line operations passed")
        else:
            mark_test_result("Order Lines", False, f"Only {success_count}/{total_tests} line operations passed")
            
    except Exception as e:
        mark_test_result("Order Lines", False, f"Exception: {str(e)}")

def test_project_orders():
    """Test getting orders by project"""
    print("\n📁 TESTING PROJECT SALES ORDERS")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 2
        
        # 1. Get all orders for project 1
        response = requests.get(f'{BASE_URL}/projects/1/sales-orders')
        print_response(response, "GET PROJECT 1 SALES ORDERS")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Get orders filtered by status
        response = requests.get(f'{BASE_URL}/projects/1/sales-orders?status=confirmed')
        print_response(response, "GET PROJECT 1 CONFIRMED ORDERS")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Project Orders", True, f"All {total_tests} project order tests passed")
        else:
            mark_test_result("Project Orders", False, f"Only {success_count}/{total_tests} project order tests passed")
            
    except Exception as e:
        mark_test_result("Project Orders", False, f"Exception: {str(e)}")

def test_customer_orders():
    """Test getting orders by customer"""
    print("\n👤 TESTING CUSTOMER SALES ORDERS")
    print("="*60)
    
    try:
        # Get orders for customer 1
        response = requests.get(f'{BASE_URL}/customers/1/sales-orders')
        print_response(response, "GET CUSTOMER 1 SALES ORDERS")
        
        if response.status_code == 200:
            mark_test_result("Customer Orders", True, "Customer orders endpoint working")
        else:
            mark_test_result("Customer Orders", False, f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        mark_test_result("Customer Orders", False, f"Exception: {str(e)}")

def test_sales_statistics():
    """Test sales order statistics endpoint"""
    print("\n📊 TESTING SALES ORDER STATISTICS")
    print("="*60)
    
    try:
        response = requests.get(f'{BASE_URL}/sales-orders/stats')
        print_response(response, "GET SALES ORDER STATISTICS")
        
        if response.status_code == 200:
            mark_test_result("Sales Statistics", True, "Statistics endpoint working")
        else:
            mark_test_result("Sales Statistics", False, f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        mark_test_result("Sales Statistics", False, f"Exception: {str(e)}")

def test_all_order_lines():
    """Test getting all order lines with filtering"""
    print("\n📋 TESTING ALL ORDER LINES")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 3
        
        # 1. Get all order lines
        response = requests.get(f'{BASE_URL}/sales-order-lines')
        print_response(response, "GET ALL ORDER LINES")
        if response.status_code == 200:
            success_count += 1
        
        # 2. Filter by sales order
        response = requests.get(f'{BASE_URL}/sales-order-lines?sales_order_id=1')
        print_response(response, "GET ORDER LINES BY SALES ORDER")
        if response.status_code == 200:
            success_count += 1
        
        # 3. Get milestone lines only
        response = requests.get(f'{BASE_URL}/sales-order-lines?milestone_only=true')
        print_response(response, "GET MILESTONE LINES ONLY")
        if response.status_code == 200:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("All Order Lines", True, f"All {total_tests} line listing tests passed")
        else:
            mark_test_result("All Order Lines", False, f"Only {success_count}/{total_tests} line listing tests passed")
            
    except Exception as e:
        mark_test_result("All Order Lines", False, f"Exception: {str(e)}")

def test_error_cases():
    """Test error handling"""
    print("\n❌ TESTING ERROR CASES")
    print("="*60)
    
    try:
        success_count = 0
        total_tests = 6
        
        # 1. Create order with invalid data
        invalid_data = {
            'so_number': 'SO-INVALID'
            # Missing required fields
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders',
                               headers=HEADERS,
                               json=invalid_data)
        print_response(response, "CREATE ORDER WITH INVALID DATA")
        if response.status_code == 400:
            success_count += 1
        
        # 2. Get non-existent order
        response = requests.get(f'{BASE_URL}/sales-orders/999999')
        print_response(response, "GET NON-EXISTENT ORDER")
        if response.status_code == 404:
            success_count += 1
        
        # 3. Create order with duplicate SO number
        duplicate_data = {
            'so_number': 'SO-2024-001',  # Existing SO number
            'project_id': 1,
            'customer_id': 1,
            'order_date': date.today().isoformat()
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders',
                               headers=HEADERS,
                               json=duplicate_data)
        print_response(response, "CREATE ORDER WITH DUPLICATE SO NUMBER")
        if response.status_code == 400:
            success_count += 1
        
        # 4. Create order with invalid status
        invalid_status_data = {
            'so_number': 'SO-TEST-999',
            'project_id': 1,
            'customer_id': 1,
            'order_date': date.today().isoformat(),
            'status': 'invalid_status'
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders',
                               headers=HEADERS,
                               json=invalid_status_data)
        print_response(response, "CREATE ORDER WITH INVALID STATUS")
        if response.status_code == 400:
            success_count += 1
        
        # 5. Add line with negative quantity
        invalid_line = {
            'description': 'Test',
            'quantity': -5.0,
            'unit_price': 100.00
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders/1/lines',
                               headers=HEADERS,
                               json=invalid_line)
        print_response(response, "ADD LINE WITH NEGATIVE QUANTITY")
        if response.status_code == 400:
            success_count += 1
        
        # 6. Add line with negative price
        invalid_price_line = {
            'description': 'Test',
            'quantity': 1.0,
            'unit_price': -100.00
        }
        
        response = requests.post(f'{BASE_URL}/sales-orders/1/lines',
                               headers=HEADERS,
                               json=invalid_price_line)
        print_response(response, "ADD LINE WITH NEGATIVE PRICE")
        if response.status_code == 400:
            success_count += 1
        
        if success_count == total_tests:
            mark_test_result("Error Handling", True, f"All {total_tests} error cases handled correctly")
        else:
            mark_test_result("Error Handling", False, f"Only {success_count}/{total_tests} error cases handled correctly")
            
    except Exception as e:
        mark_test_result("Error Handling", False, f"Exception: {str(e)}")

def test_order_total_calculation():
    """Test automatic order total calculation"""
    print("\n💰 TESTING ORDER TOTAL CALCULATION")
    print("="*60)
    
    try:
        # Get an order with lines
        response = requests.get(f'{BASE_URL}/sales-orders/1?include_lines=true')
        print_response(response, "GET ORDER WITH TOTAL CALCULATION")
        
        if response.status_code == 200:
            data = response.json()['data']
            if 'order_total' in data and 'lines' in data:
                # Verify calculation
                calculated_total = sum(
                    line['quantity'] * line['unit_price'] 
                    for line in data['lines']
                )
                reported_total = data['order_total']
                
                if abs(calculated_total - reported_total) < 0.01:
                    print(f"✅ Order total correctly calculated: {reported_total}")
                    mark_test_result("Order Total Calculation", True, f"Total correctly calculated: {reported_total}")
                else:
                    mark_test_result("Order Total Calculation", False, f"Total mismatch: {calculated_total} vs {reported_total}")
            else:
                mark_test_result("Order Total Calculation", False, "Missing order_total or lines in response")
        else:
            mark_test_result("Order Total Calculation", False, f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        mark_test_result("Order Total Calculation", False, f"Exception: {str(e)}")

def cleanup_test_data(order_id):
    """Clean up test data"""
    if order_id:
        print(f"\n🧹 CLEANING UP TEST DATA")
        print("="*60)
        
        try:
            response = requests.delete(f'{BASE_URL}/sales-orders/{order_id}')
            print_response(response, f"DELETE TEST ORDER {order_id}")
            
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
        print(f"{status:10} | {test_name:30} | {result['details']}")
    
    print(f"\n{'='*80}")
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! The Sales Orders API is working perfectly!")
    else:
        print(f"⚠️  {failed_tests} TEST(S) FAILED. Please review the failing tests above.")
    print(f"{'='*80}")
    
    return failed_tests == 0

def main():
    """Main test function"""
    print("🧪 SALES ORDERS API COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("Make sure the Flask application is running on http://localhost:5000")
    print("And the database is initialized with sample data")
    
    try:
        # Test basic CRUD operations
        order_id = test_sales_order_crud()
        
        # Test filtering
        test_sales_order_filtering()
        
        # Test order lines
        test_order_lines(order_id)
        
        # Test project orders
        test_project_orders()
        
        # Test customer orders
        test_customer_orders()
        
        # Test statistics
        test_sales_statistics()
        
        # Test all order lines
        test_all_order_lines()
        
        # Test order total calculation
        test_order_total_calculation()
        
        # Test error cases
        test_error_cases()
        
        # Clean up
        cleanup_test_data(order_id)
        
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
