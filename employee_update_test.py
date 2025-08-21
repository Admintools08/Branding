#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time

class EmployeeUpdateTester:
    def __init__(self, base_url="https://perf-boost-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_employee_id = None
        self.test_employee_data = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_login(self):
        """Test login with admin credentials"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@test.com", "password": "admin123"},
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            user_role = data.get('user', {}).get('role', 'unknown')
            return self.log_test(
                "Login with admin credentials",
                True,
                f"Admin logged in successfully, Role: {user_role}"
            )
        else:
            return self.log_test(
                "Login with admin credentials",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_create_test_employee(self):
        """Create a test employee for update testing"""
        if not self.token:
            return self.log_test("Create test employee", False, "No token available")
        
        employee_data = {
            "name": "John Update Test",
            "employee_id": f"UPD{int(time.time())}",
            "email": f"john.update.{int(time.time())}@testcompany.com",
            "department": "Testing Department",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if success and 'id' in data:
            self.test_employee_id = data['id']
            self.test_employee_data = employee_data
            return self.log_test(
                "Create test employee",
                True,
                f"Created employee: {data['name']} (ID: {data['employee_id']})"
            )
        else:
            return self.log_test(
                "Create test employee",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_employee_profile_update_endpoint(self):
        """Test employee profile update via '/employees/{employee_id}/profile' endpoint"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Employee profile update endpoint", False, "No token or employee available")
        
        # Test updating multiple fields including the new ones mentioned in the review
        update_data = {
            "name": "John Updated Profile",
            "email": f"john.updated.{int(time.time())}@testcompany.com",
            "employee_id": f"UPDPROF{int(time.time())}",
            "department": "Updated Department",
            "manager": "Updated Manager",
            "start_date": "2024-01-15T00:00:00Z",
            "status": "active"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.test_employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            # Verify the data was actually updated
            get_success, get_status, get_data = self.make_request(
                'GET',
                f'employees/{self.test_employee_id}',
                expected_status=200
            )
            
            if get_success:
                data_persisted = (
                    get_data.get('name') == update_data['name'] and
                    get_data.get('email') == update_data['email'] and
                    get_data.get('employee_id') == update_data['employee_id'] and
                    get_data.get('department') == update_data['department'] and
                    get_data.get('status') == update_data['status']
                )
                
                return self.log_test(
                    "Employee profile update endpoint",
                    data_persisted,
                    f"Profile updated and data persisted correctly. Name: {get_data.get('name')}, Status: {get_data.get('status')}"
                )
            else:
                return self.log_test(
                    "Employee profile update endpoint",
                    False,
                    f"Update succeeded but failed to retrieve updated data. Get status: {get_status}"
                )
        else:
            return self.log_test(
                "Employee profile update endpoint",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_employee_status_update_endpoint(self):
        """Test employee status update via '/employees/{employee_id}' endpoint"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Employee status update endpoint", False, "No token or employee available")
        
        # Test updating status to different values
        status_updates = [
            {"status": "active", "description": "Active status"},
            {"status": "exiting", "description": "Exiting status"},
            {"status": "inactive", "description": "New Inactive status"},
            {"status": "exited", "description": "Exited status"}
        ]
        
        all_updates_successful = True
        update_details = []
        
        for update in status_updates:
            success, status_code, data = self.make_request(
                'PUT',
                f'employees/{self.test_employee_id}',
                {"status": update["status"]},
                expected_status=200
            )
            
            if success:
                # Verify the status was actually updated
                get_success, get_status, get_data = self.make_request(
                    'GET',
                    f'employees/{self.test_employee_id}',
                    expected_status=200
                )
                
                if get_success and get_data.get('status') == update["status"]:
                    update_details.append(f"{update['description']}: ✅")
                else:
                    update_details.append(f"{update['description']}: ❌ (not persisted)")
                    all_updates_successful = False
            else:
                update_details.append(f"{update['description']}: ❌ (update failed)")
                all_updates_successful = False
        
        return self.log_test(
            "Employee status update endpoint",
            all_updates_successful,
            f"Status updates: {', '.join(update_details)}"
        )

    def test_inactive_status_functionality(self):
        """Test the new 'inactive' status functionality"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Inactive status functionality", False, "No token or employee available")
        
        # Set employee to inactive status
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.test_employee_id}',
            {"status": "inactive"},
            expected_status=200
        )
        
        if success:
            # Verify inactive status is properly stored and retrieved
            get_success, get_status, get_data = self.make_request(
                'GET',
                f'employees/{self.test_employee_id}',
                expected_status=200
            )
            
            if get_success and get_data.get('status') == 'inactive':
                # Test that inactive employees appear in employee list
                list_success, list_status, list_data = self.make_request(
                    'GET',
                    'employees',
                    expected_status=200
                )
                
                if list_success:
                    inactive_employee_found = any(
                        emp.get('id') == self.test_employee_id and emp.get('status') == 'inactive'
                        for emp in list_data
                    )
                    
                    return self.log_test(
                        "Inactive status functionality",
                        inactive_employee_found,
                        f"Inactive status set and employee found in list with inactive status"
                    )
                else:
                    return self.log_test(
                        "Inactive status functionality",
                        False,
                        f"Failed to retrieve employee list. Status: {list_status}"
                    )
            else:
                return self.log_test(
                    "Inactive status functionality",
                    False,
                    f"Inactive status not properly persisted. Current status: {get_data.get('status')}"
                )
        else:
            return self.log_test(
                "Inactive status functionality",
                False,
                f"Failed to set inactive status. Status: {status}, Data: {data}"
            )

    def test_email_uniqueness_validation(self):
        """Test email uniqueness validation"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Email uniqueness validation", False, "No token or employee available")
        
        # Create another employee first
        employee_data = {
            "name": "Jane Duplicate Test",
            "employee_id": f"DUP{int(time.time())}",
            "email": f"jane.duplicate.{int(time.time())}@testcompany.com",
            "department": "Testing Department",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if not create_success:
            return self.log_test(
                "Email uniqueness validation",
                False,
                f"Failed to create second employee for testing. Status: {create_status}"
            )
        
        second_employee_id = create_data['id']
        second_employee_email = create_data['email']
        
        # Try to update first employee with second employee's email (should fail)
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.test_employee_id}/profile',
            {"email": second_employee_email},
            expected_status=400
        )
        
        # Clean up second employee
        self.make_request('DELETE', f'employees/{second_employee_id}')
        
        validation_working = success and "already exists" in data.get('detail', '').lower()
        
        return self.log_test(
            "Email uniqueness validation",
            validation_working,
            f"Email uniqueness properly validated. Status: {status}, Message: {data.get('detail', 'No message')}"
        )

    def test_employee_id_uniqueness_validation(self):
        """Test employee_id uniqueness validation"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Employee ID uniqueness validation", False, "No token or employee available")
        
        # Create another employee first
        employee_data = {
            "name": "Bob Duplicate ID Test",
            "employee_id": f"DUPID{int(time.time())}",
            "email": f"bob.duplicate.{int(time.time())}@testcompany.com",
            "department": "Testing Department",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if not create_success:
            return self.log_test(
                "Employee ID uniqueness validation",
                False,
                f"Failed to create second employee for testing. Status: {create_status}"
            )
        
        second_employee_id = create_data['id']
        second_employee_emp_id = create_data['employee_id']
        
        # Try to update first employee with second employee's employee_id (should fail)
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.test_employee_id}/profile',
            {"employee_id": second_employee_emp_id},
            expected_status=400
        )
        
        # Clean up second employee
        self.make_request('DELETE', f'employees/{second_employee_id}')
        
        validation_working = success and "already exists" in data.get('detail', '').lower()
        
        return self.log_test(
            "Employee ID uniqueness validation",
            validation_working,
            f"Employee ID uniqueness properly validated. Status: {status}, Message: {data.get('detail', 'No message')}"
        )

    def test_data_persistence_no_loss(self):
        """Test data persistence - ensure no data loss during updates"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Data persistence no loss", False, "No token or employee available")
        
        # Get current employee data
        get_success, get_status, original_data = self.make_request(
            'GET',
            f'employees/{self.test_employee_id}',
            expected_status=200
        )
        
        if not get_success:
            return self.log_test(
                "Data persistence no loss",
                False,
                f"Failed to get original employee data. Status: {get_status}"
            )
        
        # Update only one field (name) and ensure other fields remain unchanged
        partial_update = {"name": "Updated Name Only"}
        
        update_success, update_status, update_data = self.make_request(
            'PUT',
            f'employees/{self.test_employee_id}/profile',
            partial_update,
            expected_status=200
        )
        
        if not update_success:
            return self.log_test(
                "Data persistence no loss",
                False,
                f"Failed to update employee. Status: {update_status}"
            )
        
        # Get updated employee data
        get_updated_success, get_updated_status, updated_data = self.make_request(
            'GET',
            f'employees/{self.test_employee_id}',
            expected_status=200
        )
        
        if not get_updated_success:
            return self.log_test(
                "Data persistence no loss",
                False,
                f"Failed to get updated employee data. Status: {get_updated_status}"
            )
        
        # Check that only name changed and other fields remained the same
        fields_to_check = ['email', 'employee_id', 'department', 'manager', 'status']
        data_preserved = True
        changed_fields = []
        
        for field in fields_to_check:
            if original_data.get(field) != updated_data.get(field):
                data_preserved = False
                changed_fields.append(f"{field}: {original_data.get(field)} -> {updated_data.get(field)}")
        
        # Name should have changed
        name_updated = updated_data.get('name') == "Updated Name Only"
        
        return self.log_test(
            "Data persistence no loss",
            data_preserved and name_updated,
            f"Name updated: {name_updated}, Other fields preserved: {data_preserved}. Changed fields: {changed_fields}"
        )

    def test_invalid_data_handling(self):
        """Test edge cases: invalid data, missing fields"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Invalid data handling", False, "No token or employee available")
        
        test_cases = [
            {
                "name": "Invalid email format",
                "data": {"email": "invalid-email-format"},
                "expected_status": 400,
                "should_fail": True
            },
            {
                "name": "Invalid date format",
                "data": {"start_date": "invalid-date"},
                "expected_status": 400,
                "should_fail": True
            },
            {
                "name": "Invalid status",
                "data": {"status": "invalid_status"},
                "expected_status": 400,
                "should_fail": True
            },
            {
                "name": "Empty name",
                "data": {"name": ""},
                "expected_status": 400,
                "should_fail": True
            }
        ]
        
        all_tests_passed = True
        test_results = []
        
        for test_case in test_cases:
            success, status, data = self.make_request(
                'PUT',
                f'employees/{self.test_employee_id}/profile',
                test_case["data"],
                expected_status=test_case["expected_status"]
            )
            
            test_passed = success if test_case["should_fail"] else not success
            test_results.append(f"{test_case['name']}: {'✅' if test_passed else '❌'}")
            
            if not test_passed:
                all_tests_passed = False
        
        return self.log_test(
            "Invalid data handling",
            all_tests_passed,
            f"Edge case tests: {', '.join(test_results)}"
        )

    def test_employee_not_found_error_fix(self):
        """Test that the 'Employee not found' error has been fixed"""
        if not self.token:
            return self.log_test("Employee not found error fix", False, "No token available")
        
        # Test with non-existent employee ID
        fake_employee_id = "non-existent-employee-id"
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{fake_employee_id}/profile',
            {"name": "Test Update"},
            expected_status=404
        )
        
        # Should return 404 with proper error message
        proper_error_handling = success and "not found" in data.get('detail', '').lower()
        
        # Test with valid employee ID (should work)
        if self.test_employee_id:
            valid_success, valid_status, valid_data = self.make_request(
                'PUT',
                f'employees/{self.test_employee_id}/profile',
                {"name": "Valid Update Test"},
                expected_status=200
            )
            
            return self.log_test(
                "Employee not found error fix",
                proper_error_handling and valid_success,
                f"Invalid ID properly returns 404, Valid ID works: {valid_success}"
            )
        else:
            return self.log_test(
                "Employee not found error fix",
                proper_error_handling,
                f"Invalid ID properly returns 404: {proper_error_handling}"
            )

    def test_cleanup(self):
        """Clean up test employee"""
        if not self.token or not self.test_employee_id:
            return self.log_test("Cleanup test employee", True, "No cleanup needed")
        
        success, status, data = self.make_request(
            'DELETE',
            f'employees/{self.test_employee_id}',
            expected_status=200
        )
        
        return self.log_test(
            "Cleanup test employee",
            success,
            f"Test employee deleted: {success}"
        )

    def run_all_tests(self):
        """Run all employee update tests"""
        print("🚀 Starting Employee Update Functionality Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Employee Update Functionality Fixes")
        print("=" * 80)
        
        # Authentication
        print("\n🔐 Authentication:")
        if not self.test_login():
            print("❌ Cannot proceed without authentication")
            return 1
        
        # Setup
        print("\n🏗️ Test Setup:")
        if not self.test_create_test_employee():
            print("❌ Cannot proceed without test employee")
            return 1
        
        # Core Update Tests
        print("\n📝 Employee Update Tests:")
        self.test_employee_profile_update_endpoint()
        self.test_employee_status_update_endpoint()
        self.test_inactive_status_functionality()
        
        # Validation Tests
        print("\n✅ Validation Tests:")
        self.test_email_uniqueness_validation()
        self.test_employee_id_uniqueness_validation()
        
        # Data Integrity Tests
        print("\n🔒 Data Integrity Tests:")
        self.test_data_persistence_no_loss()
        self.test_invalid_data_handling()
        
        # Bug Fix Verification
        print("\n🐛 Bug Fix Verification:")
        self.test_employee_not_found_error_fix()
        
        # Cleanup
        print("\n🧹 Cleanup:")
        self.test_cleanup()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Employee Update Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All employee update tests passed! The fixes are working correctly!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please review the implementation.")
            return 1

def main():
    """Main test runner"""
    tester = EmployeeUpdateTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())