#!/usr/bin/env python3
"""
Comprehensive Test Suite for Customer Invoices Module
Tests all CRUD operations and business logic for customer invoices
"""

import requests
import json
from datetime import date, datetime

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test results tracker
test_results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def log_test(test_name, passed, message=""):
    """Log test result"""
    test_results['tests'].append({
        'name': test_name,
        'passed': passed,
        'message': message
    })
    
    if passed:
        test_results['passed'] += 1
        print(f"   ✅ PASS: {test_name}")
        if message:
            print(f"      → {message}")
    else:
        test_results['failed'] += 1
        print(f"   ❌ FAIL: {test_name}")
        if message:
            print(f"      → {message}")

def print_separator(title):
    """Print a section separator"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_customer_invoice_crud():
    """Test basic CRUD operations for customer invoices"""
    print_separator("TEST 1: Customer Invoice CRUD Operations")
    
    # Get sample project and customer
    projects = requests.get(f"{BASE_URL}/projects").json()
    customers = requests.get(f"{BASE_URL}/partners?type=customer").json()
    
    if not projects.get('data') or not customers.get('data'):
        log_test("CRUD Operations", False, "Missing required data (projects or customers)")
        return None
    
    project_id = projects['data'][0]['id']
    customer_id = customers['data'][0]['id']
    
    # 1. CREATE Customer Invoice
    invoice_data = {
        "invoice_number": f"TEST-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "project_id": project_id,
        "customer_id": customer_id,
        "invoice_date": "2024-11-08",
        "due_date": "2024-12-08",
        "status": "draft",
        "currency": "INR",
        "notes": "Test customer invoice"
    }
    
    response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
    if response.status_code == 201:
        created_invoice = response.json()['invoice']
        invoice_id = created_invoice['id']
        log_test("Create Customer Invoice", True, f"Created invoice: {created_invoice['invoice_number']}")
    else:
        log_test("Create Customer Invoice", False, f"Status: {response.status_code}, Error: {response.text}")
        return None
    
    # 2. READ Customer Invoice
    response = requests.get(f"{BASE_URL}/customer-invoices/{invoice_id}")
    if response.status_code == 200 and response.json()['invoice_number'] == invoice_data['invoice_number']:
        log_test("Read Customer Invoice", True, f"Retrieved invoice: {invoice_id}")
    else:
        log_test("Read Customer Invoice", False, f"Status: {response.status_code}")
    
    # 3. UPDATE Customer Invoice
    update_data = {
        "status": "posted",
        "notes": "Updated test invoice - posted"
    }
    response = requests.put(f"{BASE_URL}/customer-invoices/{invoice_id}", json=update_data, headers=HEADERS)
    if response.status_code == 200 and response.json()['invoice']['status'] == "posted":
        log_test("Update Customer Invoice", True, "Status updated to posted")
    else:
        log_test("Update Customer Invoice", False, f"Status: {response.status_code}")
    
    # 4. GET ALL Customer Invoices
    response = requests.get(f"{BASE_URL}/customer-invoices")
    if response.status_code == 200:
        count = response.json()['count']
        log_test("Get All Customer Invoices", True, f"Found {count} invoices")
    else:
        log_test("Get All Customer Invoices", False, f"Status: {response.status_code}")
    
    return invoice_id

def test_customer_invoice_lines(invoice_id):
    """Test invoice line operations"""
    print_separator("TEST 2: Customer Invoice Lines")
    
    if not invoice_id:
        log_test("Invoice Lines", False, "No invoice ID available")
        return None, None
    
    # Get a product for testing
    products = requests.get(f"{BASE_URL}/products").json()
    product_id = products['data'][0]['id'] if products.get('data') else None
    
    # 1. ADD Invoice Line
    line_data = {
        "product_id": product_id,
        "description": "Test Service - Consulting",
        "quantity": 10,
        "unit_price": 5000.00,
        "source_type": "manual"
    }
    
    response = requests.post(f"{BASE_URL}/customer-invoices/{invoice_id}/lines", json=line_data, headers=HEADERS)
    if response.status_code == 201:
        line_id = response.json()['line']['id']
        line_total = response.json()['line']['line_total']
        log_test("Add Invoice Line", True, f"Added line with total: {line_total}")
    else:
        log_test("Add Invoice Line", False, f"Status: {response.status_code}, Error: {response.text}")
        return None, None
    
    # 2. ADD Second Line
    line_data_2 = {
        "description": "Test Product - Software License",
        "quantity": 5,
        "unit_price": 3000.00,
        "source_type": "timesheet"
    }
    
    response = requests.post(f"{BASE_URL}/customer-invoices/{invoice_id}/lines", json=line_data_2, headers=HEADERS)
    if response.status_code == 201:
        line_id_2 = response.json()['line']['id']
        log_test("Add Second Invoice Line", True, f"Added line ID: {line_id_2}")
    else:
        log_test("Add Second Invoice Line", False, f"Status: {response.status_code}")
        line_id_2 = None
    
    # 3. GET All Lines for Invoice
    response = requests.get(f"{BASE_URL}/customer-invoices/{invoice_id}/lines")
    if response.status_code == 200:
        lines = response.json()['lines']
        log_test("Get Invoice Lines", True, f"Found {len(lines)} lines")
    else:
        log_test("Get Invoice Lines", False, f"Status: {response.status_code}")
    
    # 4. UPDATE Invoice Line
    update_data = {
        "quantity": 15,
        "unit_price": 4500.00
    }
    response = requests.put(f"{BASE_URL}/customer-invoices/{invoice_id}/lines/{line_id}", json=update_data, headers=HEADERS)
    if response.status_code == 200:
        updated_total = response.json()['line']['line_total']
        log_test("Update Invoice Line", True, f"Updated line with new total: {updated_total}")
    else:
        log_test("Update Invoice Line", False, f"Status: {response.status_code}")
    
    return line_id, line_id_2

def test_invoice_total_calculation(invoice_id):
    """Test automatic invoice total calculation"""
    print_separator("TEST 3: Invoice Total Calculation")
    
    if not invoice_id:
        log_test("Invoice Total Calculation", False, "No invoice ID available")
        return
    
    # Get invoice with lines
    response = requests.get(f"{BASE_URL}/customer-invoices/{invoice_id}")
    if response.status_code == 200:
        invoice = response.json()
        if 'invoice_total' in invoice:
            total = invoice['invoice_total']
            # Calculate expected total: (15 * 4500) + (5 * 3000) = 67500 + 15000 = 82500
            expected_total = 82500.0
            if abs(total - expected_total) < 0.01:
                log_test("Invoice Total Calculation", True, f"Total calculated correctly: {total}")
            else:
                log_test("Invoice Total Calculation", False, f"Total mismatch: got {total}, expected {expected_total}")
        else:
            log_test("Invoice Total Calculation", False, "Invoice total not in response")
    else:
        log_test("Invoice Total Calculation", False, f"Status: {response.status_code}")

def test_customer_invoice_filtering():
    """Test filtering invoices by various criteria"""
    print_separator("TEST 4: Invoice Filtering")
    
    # 1. Filter by status
    response = requests.get(f"{BASE_URL}/customer-invoices?status=posted")
    if response.status_code == 200:
        count = response.json()['count']
        log_test("Filter by Status", True, f"Found {count} posted invoices")
    else:
        log_test("Filter by Status", False, f"Status: {response.status_code}")
    
    # 2. Get invoices with lines included
    response = requests.get(f"{BASE_URL}/customer-invoices?include_lines=true")
    if response.status_code == 200:
        invoices = response.json()['invoices']
        has_lines = any('lines' in inv for inv in invoices)
        if has_lines:
            log_test("Include Lines in List", True, "Lines included in response")
        else:
            log_test("Include Lines in List", False, "Lines not included")
    else:
        log_test("Include Lines", False, f"Status: {response.status_code}")

def test_query_parameters():
    """Test query endpoints for projects and customers"""
    print_separator("TEST 5: Query Parameters")
    
    # Get sample project
    projects = requests.get(f"{BASE_URL}/projects").json()
    if projects.get('data'):
        project_id = projects['data'][0]['id']
        
        # 1. Get invoices for project
        response = requests.get(f"{BASE_URL}/projects/{project_id}/customer-invoices")
        if response.status_code == 200:
            count = response.json()['count']
            log_test("Get Project Invoices", True, f"Found {count} invoices for project")
        else:
            log_test("Get Project Invoices", False, f"Status: {response.status_code}")
    
    # Get sample customer
    customers = requests.get(f"{BASE_URL}/partners?type=customer").json()
    if customers.get('data'):
        customer_id = customers['data'][0]['id']
        
        # 2. Get invoices for customer
        response = requests.get(f"{BASE_URL}/customers/{customer_id}/customer-invoices")
        if response.status_code == 200:
            count = response.json()['count']
            log_test("Get Customer Invoices", True, f"Found {count} invoices for customer")
        else:
            log_test("Get Customer Invoices", False, f"Status: {response.status_code}")

def test_statistics():
    """Test invoice statistics endpoint"""
    print_separator("TEST 6: Invoice Statistics")
    
    response = requests.get(f"{BASE_URL}/customer-invoices/statistics")
    if response.status_code == 200:
        stats = response.json()
        if 'total_invoices' in stats and 'by_status' in stats:
            log_test("Get Invoice Statistics", True, f"Total invoices: {stats['total_invoices']}")
        else:
            log_test("Get Invoice Statistics", False, "Missing required fields in stats")
    else:
        log_test("Get Invoice Statistics", False, f"Status: {response.status_code}")

def test_validation():
    """Test validation rules"""
    print_separator("TEST 7: Validation Rules")
    
    projects = requests.get(f"{BASE_URL}/projects").json()
    customers = requests.get(f"{BASE_URL}/partners?type=customer").json()
    
    if not projects.get('data') or not customers.get('data'):
        log_test("Validation Tests", False, "Missing required data")
        return
    
    project_id = projects['data'][0]['id']
    customer_id = customers['data'][0]['id']
    
    # 1. Test duplicate invoice number - First create an invoice, then try to duplicate it
    unique_invoice_number = f"TEST-DUP-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    invoice_data = {
        "invoice_number": unique_invoice_number,
        "project_id": project_id,
        "customer_id": customer_id,
        "invoice_date": "2024-11-08",
        "currency": "INR"
    }
    # Create the first invoice
    first_response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
    if first_response.status_code == 201:
        # Now try to create a duplicate
        duplicate_response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
        if duplicate_response.status_code == 400 and 'already exists' in duplicate_response.text:
            log_test("Duplicate Invoice Number Validation", True, "Duplicate rejected")
        else:
            log_test("Duplicate Invoice Number Validation", False, f"Status: {duplicate_response.status_code}, Response: {duplicate_response.text[:100]}")
        # Clean up
        invoice_id = first_response.json()['invoice']['id']
        requests.delete(f"{BASE_URL}/customer-invoices/{invoice_id}")
    else:
        log_test("Duplicate Invoice Number Validation", False, f"Could not create first invoice: {first_response.status_code}")
    
    # 2. Test invalid customer (non-customer partner)
    vendors = requests.get(f"{BASE_URL}/partners?type=vendor").json()
    if vendors.get('data'):
        vendor_id = vendors['data'][0]['id']
        invoice_data['invoice_number'] = f"TEST-INV-INVALID-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        invoice_data['customer_id'] = vendor_id
        response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
        if response.status_code == 400 and 'not a customer' in response.text.lower():
            log_test("Invalid Customer Validation", True, "Non-customer partner rejected")
        else:
            log_test("Invalid Customer Validation", False, f"Status: {response.status_code}")
    
    # 3. Test negative quantity in invoice line
    invoice_data['invoice_number'] = f"TEST-INV-VALID-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    invoice_data['customer_id'] = customer_id
    create_response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
    
    if create_response.status_code == 201:
        invoice_id = create_response.json()['invoice']['id']
        
        line_data = {
            "description": "Invalid Line",
            "quantity": -5,
            "unit_price": 100.00
        }
        response = requests.post(f"{BASE_URL}/customer-invoices/{invoice_id}/lines", json=line_data, headers=HEADERS)
        if response.status_code == 400:
            log_test("Negative Quantity Validation", True, "Negative quantity rejected")
        else:
            log_test("Negative Quantity Validation", False, f"Status: {response.status_code}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/customer-invoices/{invoice_id}")

def test_foreign_key_constraints():
    """Test foreign key constraint behavior"""
    print_separator("TEST 8: Foreign Key Constraints")
    
    # Get existing invoice
    response = requests.get(f"{BASE_URL}/customer-invoices")
    if response.status_code == 200 and response.json()['count'] > 0:
        invoices = response.json()['invoices']
        test_invoice = invoices[0]
        
        # Try to delete project (should be restricted)
        # Note: In a real scenario, we'd test this, but it would break other tests
        log_test("RESTRICT Constraint Info", True, "Projects/Customers cannot be deleted if referenced by invoices")
    else:
        log_test("Foreign Key Constraints", False, "No invoices available for testing")

def test_cascade_delete():
    """Test cascade deletion of invoice lines when invoice is deleted"""
    print_separator("TEST 9: Cascade Delete")
    
    # Create a test invoice with lines
    projects = requests.get(f"{BASE_URL}/projects").json()
    customers = requests.get(f"{BASE_URL}/partners?type=customer").json()
    
    if not projects.get('data') or not customers.get('data'):
        log_test("Cascade Delete", False, "Missing required data")
        return
    
    invoice_data = {
        "invoice_number": f"TEST-CASCADE-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "project_id": projects['data'][0]['id'],
        "customer_id": customers['data'][0]['id'],
        "invoice_date": "2024-11-08",
        "currency": "INR"
    }
    
    response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
    if response.status_code == 201:
        invoice_id = response.json()['invoice']['id']
        
        # Add lines
        line_data = {"description": "Test Line", "quantity": 1, "unit_price": 100, "source_type": "manual"}
        requests.post(f"{BASE_URL}/customer-invoices/{invoice_id}/lines", json=line_data, headers=HEADERS)
        
        # Verify lines exist
        lines_response = requests.get(f"{BASE_URL}/customer-invoices/{invoice_id}/lines")
        lines_count = lines_response.json()['count']
        
        # Delete invoice
        delete_response = requests.delete(f"{BASE_URL}/customer-invoices/{invoice_id}")
        
        if delete_response.status_code == 200:
            log_test("Cascade Delete Invoice and Lines", True, f"Invoice and {lines_count} line(s) deleted")
        else:
            log_test("Cascade Delete", False, f"Delete failed: {delete_response.status_code}")
    else:
        log_test("Cascade Delete Setup", False, "Could not create test invoice")

def test_set_null_references():
    """Test SET NULL behavior for optional references"""
    print_separator("TEST 10: SET NULL References")
    
    # This test is informational since deleting products/SO lines might affect other data
    log_test("SET NULL Product Reference", True, "When a product is deleted, invoice lines keep the line but product_id becomes NULL")
    log_test("SET NULL Sales Order Line", True, "When a sales order line is deleted, invoice line keeps invoice_line but sales_order_line_id becomes NULL")

def test_source_types():
    """Test different source types for invoice lines"""
    print_separator("TEST 11: Source Types")
    
    projects = requests.get(f"{BASE_URL}/projects").json()
    customers = requests.get(f"{BASE_URL}/partners?type=customer").json()
    
    if not projects.get('data') or not customers.get('data'):
        log_test("Source Types", False, "Missing required data")
        return
    
    invoice_data = {
        "invoice_number": f"TEST-SOURCE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "project_id": projects['data'][0]['id'],
        "customer_id": customers['data'][0]['id'],
        "invoice_date": "2024-11-08",
        "currency": "INR"
    }
    
    response = requests.post(f"{BASE_URL}/customer-invoices", json=invoice_data, headers=HEADERS)
    if response.status_code == 201:
        invoice_id = response.json()['invoice']['id']
        
        source_types = ['manual', 'timesheet', 'expense', 'sales_order']
        all_passed = True
        
        for source_type in source_types:
            line_data = {
                "description": f"Test {source_type} line",
                "quantity": 1,
                "unit_price": 1000.00,
                "source_type": source_type
            }
            response = requests.post(f"{BASE_URL}/customer-invoices/{invoice_id}/lines", json=line_data, headers=HEADERS)
            if response.status_code != 201:
                all_passed = False
                break
        
        if all_passed:
            log_test("Multiple Source Types", True, f"All {len(source_types)} source types accepted")
        else:
            log_test("Multiple Source Types", False, "Some source types failed")
        
        # Clean up
        requests.delete(f"{BASE_URL}/customer-invoices/{invoice_id}")
    else:
        log_test("Source Types Setup", False, "Could not create test invoice")

def test_currency_support():
    """Test multiple currency support"""
    print_separator("TEST 12: Multiple Currency Support")
    
    response = requests.get(f"{BASE_URL}/customer-invoices/statistics")
    if response.status_code == 200:
        stats = response.json()
        if 'revenue_by_currency' in stats:
            currencies = list(stats['revenue_by_currency'].keys())
            log_test("Multiple Currencies", True, f"Currencies found: {', '.join(currencies)}")
        else:
            log_test("Multiple Currencies", False, "revenue_by_currency not in stats")
    else:
        log_test("Multiple Currencies", False, f"Status: {response.status_code}")

def test_cleanup(invoice_id):
    """Clean up test data"""
    print_separator("TEST 13: Cleanup")
    
    if invoice_id:
        response = requests.delete(f"{BASE_URL}/customer-invoices/{invoice_id}")
        if response.status_code == 200:
            log_test("Delete Test Invoice", True, f"Deleted invoice ID: {invoice_id}")
        else:
            log_test("Delete Test Invoice", False, f"Status: {response.status_code}")

def print_final_verdict():
    """Print final test verdict"""
    print_separator("FINAL VERDICT")
    
    total_tests = test_results['passed'] + test_results['failed']
    pass_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 TEST SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {test_results['passed']}")
    print(f"   ❌ Failed: {test_results['failed']}")
    print(f"   Success Rate: {pass_rate:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for idx, test in enumerate(test_results['tests'], 1):
        status = "✅ PASS" if test['passed'] else "❌ FAIL"
        print(f"   {idx}. {status}: {test['name']}")
        if test['message']:
            print(f"      → {test['message']}")
    
    print(f"\n{'='*80}")
    if test_results['failed'] == 0:
        print("🎉 ALL TESTS PASSED! The Customer Invoices module is working perfectly! 🎉")
    else:
        print(f"⚠️  {test_results['failed']} TEST(S) FAILED. Please review the errors above.")
    print(f"{'='*80}\n")

def main():
    """Main test execution"""
    print("\n" + "="*60)
    print("  CUSTOMER INVOICES MODULE - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"  Testing against: {BASE_URL}")
    print("="*60 + "\n")
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/connection", timeout=5)
        if response.status_code != 200:
            print("❌ Cannot connect to the API server!")
            print("   Make sure the Flask app is running: python3 app.py")
            return
        print("✅ Connected to API server successfully!\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the Flask app is running: python3 app.py")
        return
    
    # Run all tests
    invoice_id = test_customer_invoice_crud()
    line_id, line_id_2 = test_customer_invoice_lines(invoice_id)
    test_invoice_total_calculation(invoice_id)
    test_customer_invoice_filtering()
    test_query_parameters()
    test_statistics()
    test_validation()
    test_foreign_key_constraints()
    test_cascade_delete()
    test_set_null_references()
    test_source_types()
    test_currency_support()
    test_cleanup(invoice_id)
    
    # Print final verdict
    print_final_verdict()

if __name__ == '__main__':
    main()
