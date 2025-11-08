#!/usr/bin/env python3
"""
Comprehensive test script for Master Data API endpoints
Tests all CRUD operations for partners and products
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
API_PREFIX = "/api/v1"

class MasterDataTester:
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
    
    def test_partner_crud(self):
        """Test Partner CRUD operations"""
        print("\n🤝 Testing Partner CRUD Operations")
        print("-" * 40)
        
        # 1. Create Partner
        partner_data = {
            "name": "Test Partner Ltd",
            "type": "customer",
            "email": "contact@testpartner.com",
            "phone": "+1-555-0123",
            "tax_id": "TAX123456",
            "billing_address": "123 Main St, City, State 12345",
            "shipping_address": "456 Oak Ave, City, State 54321"
        }
        response, error = self.make_request('POST', '/partners', partner_data)
        if error:
            self.log_test("Create Partner", False, error=error)
            return None
        
        success = response.status_code == 201
        partner_id = None
        if success:
            partner_id = response.json().get('data', {}).get('id')
        self.log_test("Create Partner", success, response.json() if success else None)
        
        if not partner_id:
            print("    ⚠️  Cannot continue partner tests without partner ID")
            return None
        
        # 2. Get All Partners
        response, error = self.make_request('GET', '/partners')
        if error:
            self.log_test("Get All Partners", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get All Partners", success, response.json() if success else None)
        
        # 3. Get Single Partner
        response, error = self.make_request('GET', f'/partners/{partner_id}')
        if error:
            self.log_test("Get Single Partner", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Single Partner", success, response.json() if success else None)
        
        # 4. Filter Partners by Type
        response, error = self.make_request('GET', '/partners?type=customer')
        if error:
            self.log_test("Filter Partners by Type", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Filter Partners by Type", success, response.json() if success else None)
        
        # 5. Search Partners by Name
        response, error = self.make_request('GET', '/partners?search=Test')
        if error:
            self.log_test("Search Partners by Name", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Search Partners by Name", success, response.json() if success else None)
        
        # 6. Update Partner
        update_data = {
            "name": "Updated Test Partner Ltd",
            "type": "both",
            "phone": "+1-555-9999"
        }
        response, error = self.make_request('PUT', f'/partners/{partner_id}', update_data)
        if error:
            self.log_test("Update Partner", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Update Partner", success, response.json() if success else None)
        
        return partner_id
    
    def test_product_crud(self):
        """Test Product CRUD operations"""
        print("\n📦 Testing Product CRUD Operations")
        print("-" * 40)
        
        # 1. Create Product
        product_data = {
            "sku": "TEST-SKU-001",
            "name": "Test Product",
            "description": "This is a test product for API testing",
            "uom": "pieces",
            "default_price": 99.99
        }
        response, error = self.make_request('POST', '/products', product_data)
        if error:
            self.log_test("Create Product", False, error=error)
            return None
        
        success = response.status_code == 201
        product_id = None
        if success:
            product_id = response.json().get('data', {}).get('id')
        self.log_test("Create Product", success, response.json() if success else None)
        
        if not product_id:
            print("    ⚠️  Cannot continue product tests without product ID")
            return None
        
        # 2. Get All Products
        response, error = self.make_request('GET', '/products')
        if error:
            self.log_test("Get All Products", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get All Products", success, response.json() if success else None)
        
        # 3. Get Single Product
        response, error = self.make_request('GET', f'/products/{product_id}')
        if error:
            self.log_test("Get Single Product", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Single Product", success, response.json() if success else None)
        
        # 4. Get Product by SKU
        response, error = self.make_request('GET', '/products/sku/TEST-SKU-001')
        if error:
            self.log_test("Get Product by SKU", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Product by SKU", success, response.json() if success else None)
        
        # 5. Search Products by Name
        response, error = self.make_request('GET', '/products?search=Test')
        if error:
            self.log_test("Search Products by Name", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Search Products by Name", success, response.json() if success else None)
        
        # 6. Search Products by SKU
        response, error = self.make_request('GET', '/products?sku=TEST')
        if error:
            self.log_test("Search Products by SKU", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Search Products by SKU", success, response.json() if success else None)
        
        # 7. Update Product
        update_data = {
            "name": "Updated Test Product",
            "default_price": 129.99,
            "description": "Updated description for test product"
        }
        response, error = self.make_request('PUT', f'/products/{product_id}', update_data)
        if error:
            self.log_test("Update Product", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Update Product", success, response.json() if success else None)
        
        return product_id
    
    def test_advanced_search(self):
        """Test advanced search endpoints"""
        print("\n🔍 Testing Advanced Search")
        print("-" * 40)
        
        # 1. Advanced Partner Search
        response, error = self.make_request('GET', '/partners/search?name=Test&type=customer')
        if error:
            self.log_test("Advanced Partner Search", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Advanced Partner Search", success, response.json() if success else None)
        
        # 2. Advanced Product Search
        response, error = self.make_request('GET', '/products/search?name=Test&min_price=50&max_price=200')
        if error:
            self.log_test("Advanced Product Search", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Advanced Product Search", success, response.json() if success else None)
    
    def test_statistics(self):
        """Test statistics endpoint"""
        print("\n📊 Testing Statistics")
        print("-" * 40)
        
        response, error = self.make_request('GET', '/master-data/stats')
        if error:
            self.log_test("Get Master Data Statistics", False, error=error)
        else:
            success = response.status_code == 200
            self.log_test("Get Master Data Statistics", success, response.json() if success else None)
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling")
        print("-" * 40)
        
        # Test 404 - Non-existent partner
        response, error = self.make_request('GET', '/partners/99999')
        if error:
            self.log_test("404 Error Handling (Partner)", False, error=error)
        else:
            success = response.status_code == 404
            self.log_test("404 Error Handling (Partner)", success)
        
        # Test 404 - Non-existent product
        response, error = self.make_request('GET', '/products/99999')
        if error:
            self.log_test("404 Error Handling (Product)", False, error=error)
        else:
            success = response.status_code == 404
            self.log_test("404 Error Handling (Product)", success)
        
        # Test 400 - Invalid partner data
        invalid_partner = {"type": "invalid_type"}
        response, error = self.make_request('POST', '/partners', invalid_partner)
        if error:
            self.log_test("400 Error Handling (Partner)", False, error=error)
        else:
            success = response.status_code == 400
            self.log_test("400 Error Handling (Partner)", success)
        
        # Test 400 - Invalid product data
        invalid_product = {"sku": "TEST", "default_price": "invalid"}
        response, error = self.make_request('POST', '/products', invalid_product)
        if error:
            self.log_test("400 Error Handling (Product)", False, error=error)
        else:
            success = response.status_code == 400
            self.log_test("400 Error Handling (Product)", success)
    
    def test_cleanup(self, partner_id, product_id):
        """Clean up test data"""
        print("\n🧹 Cleaning Up Test Data")
        print("-" * 40)
        
        # Delete Product (if exists)
        if product_id:
            response, error = self.make_request('DELETE', f'/products/{product_id}')
            if error:
                self.log_test("Delete Test Product", False, error=error)
            else:
                success = response.status_code == 200
                self.log_test("Delete Test Product", success, response.json() if success else None)
        
        # Delete Partner (if exists)
        if partner_id:
            response, error = self.make_request('DELETE', f'/partners/{partner_id}')
            if error:
                self.log_test("Delete Test Partner", False, error=error)
            else:
                success = response.status_code == 200
                self.log_test("Delete Test Partner", success, response.json() if success else None)
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Master Data API Tests")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test health endpoints
        self.test_health_endpoints()
        
        # Test statistics
        self.test_statistics()
        
        # Test CRUD operations
        partner_id = self.test_partner_crud()
        product_id = self.test_product_crud()
        
        # Test advanced search
        self.test_advanced_search()
        
        # Test error handling
        self.test_error_handling()
        
        # Clean up test data
        self.test_cleanup(partner_id, product_id)
        
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
    tester = MasterDataTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()