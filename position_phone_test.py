#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time

class PositionPhoneFieldTester:
    def __init__(self, base_url="https://data-import-tool-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_employee_id = None

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

    def test_login_with_admin(self):
        """Test login with admin credentials"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@test.com", "password": "admin123"},
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            return self.log_test(
                "Login with admin credentials",
                True,
                f"Admin logged in successfully"
            )
        else:
            return self.log_test(
                "Login with admin credentials",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_create_employee_with_position_phone(self):
        """Test creating a new employee with position and phone fields"""
        if not self.token:
            return self.log_test("Create employee with position and phone", False, "No token available")
        
        employee_data = {
            "name": "John Smith",
            "employee_id": f"EMP{int(time.time())}",
            "email": f"john.smith.{int(time.time())}@company.com",
            "department": "Engineering",
            "position": "Senior Software Engineer",
            "manager": "Jane Doe",
            "phone": "+1-555-123-4567",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if success:
            self.created_employee_id = data.get('id')
            # Verify position and phone are saved correctly
            position_saved = data.get('position') == employee_data['position']
            phone_saved = data.get('phone') == employee_data['phone']
            
            return self.log_test(
                "Create employee with position and phone",
                position_saved and phone_saved,
                f"Employee created with position: '{data.get('position')}', phone: '{data.get('phone')}'"
            )
        else:
            return self.log_test(
                "Create employee with position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_retrieve_employee_with_position_phone(self):
        """Test retrieving employee and verifying position and phone fields are returned"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Retrieve employee with position and phone", False, "No token or employee ID available")
        
        success, status, data = self.make_request(
            'GET',
            f'employees/{self.created_employee_id}',
            expected_status=200
        )
        
        if success:
            has_position = 'position' in data and data['position'] is not None
            has_phone = 'phone' in data and data['phone'] is not None
            
            return self.log_test(
                "Retrieve employee with position and phone",
                has_position and has_phone,
                f"Retrieved employee with position: '{data.get('position')}', phone: '{data.get('phone')}'"
            )
        else:
            return self.log_test(
                "Retrieve employee with position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_update_employee_profile_position_phone(self):
        """Test updating employee profile with position and phone via PUT /api/employees/{employee_id}/profile"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Update employee profile position and phone", False, "No token or employee ID available")
        
        update_data = {
            "position": "Lead Software Engineer",
            "phone": "+1-555-987-6543"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            position_updated = data.get('position') == update_data['position']
            phone_updated = data.get('phone') == update_data['phone']
            
            return self.log_test(
                "Update employee profile position and phone",
                position_updated and phone_updated,
                f"Profile updated with position: '{data.get('position')}', phone: '{data.get('phone')}'"
            )
        else:
            return self.log_test(
                "Update employee profile position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_update_employee_with_empty_position_phone(self):
        """Test updating employee with empty strings for position and phone"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Update employee with empty position and phone", False, "No token or employee ID available")
        
        update_data = {
            "position": "",
            "phone": ""
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            # Empty strings should be accepted
            position_empty = data.get('position') == ""
            phone_empty = data.get('phone') == ""
            
            return self.log_test(
                "Update employee with empty position and phone",
                position_empty and phone_empty,
                f"Profile updated with empty position: '{data.get('position')}', phone: '{data.get('phone')}'"
            )
        else:
            return self.log_test(
                "Update employee with empty position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_update_employee_with_null_position_phone(self):
        """Test updating employee with null values for position and phone"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Update employee with null position and phone", False, "No token or employee ID available")
        
        update_data = {
            "position": None,
            "phone": None
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            # Null values should be accepted (fields are optional)
            return self.log_test(
                "Update employee with null position and phone",
                True,
                f"Profile updated with null values - position: {data.get('position')}, phone: {data.get('phone')}"
            )
        else:
            return self.log_test(
                "Update employee with null position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_create_employee_without_position_phone(self):
        """Test creating employee without position and phone fields (should work as they're optional)"""
        if not self.token:
            return self.log_test("Create employee without position and phone", False, "No token available")
        
        employee_data = {
            "name": "Jane Wilson",
            "employee_id": f"EMP{int(time.time())}_2",
            "email": f"jane.wilson.{int(time.time())}@company.com",
            "department": "Marketing",
            "manager": "John Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if success:
            # Position and phone should be None or not present
            position_optional = data.get('position') is None
            phone_optional = data.get('phone') is None
            
            return self.log_test(
                "Create employee without position and phone",
                position_optional and phone_optional,
                f"Employee created without position/phone - position: {data.get('position')}, phone: {data.get('phone')}"
            )
        else:
            return self.log_test(
                "Create employee without position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_update_existing_employee_add_position_phone(self):
        """Test updating an existing employee to add position and phone fields"""
        if not self.token:
            return self.log_test("Update existing employee add position and phone", False, "No token available")
        
        # First get list of employees to find an existing one
        success, status, employees_data = self.make_request('GET', 'employees')
        
        if not success or not isinstance(employees_data, list) or len(employees_data) == 0:
            return self.log_test(
                "Update existing employee add position and phone",
                False,
                "No existing employees found to update"
            )
        
        # Use the first employee
        existing_employee = employees_data[0]
        employee_id = existing_employee.get('id')
        
        if not employee_id:
            return self.log_test(
                "Update existing employee add position and phone",
                False,
                "No employee ID found in existing employee data"
            )
        
        # Update with position and phone
        update_data = {
            "position": "Updated Position Title",
            "phone": "+1-555-111-2222"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            position_added = data.get('position') == update_data['position']
            phone_added = data.get('phone') == update_data['phone']
            
            return self.log_test(
                "Update existing employee add position and phone",
                position_added and phone_added,
                f"Existing employee updated with position: '{data.get('position')}', phone: '{data.get('phone')}'"
            )
        else:
            return self.log_test(
                "Update existing employee add position and phone",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_data_persistence_position_phone(self):
        """Test that position and phone data persists correctly in database"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Data persistence position and phone", False, "No token or employee ID available")
        
        # First update with specific values
        update_data = {
            "position": "Data Persistence Test Position",
            "phone": "+1-555-PERSIST"
        }
        
        success1, status1, data1 = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if not success1:
            return self.log_test(
                "Data persistence position and phone",
                False,
                f"Failed to update employee: Status {status1}"
            )
        
        # Wait a moment for database write
        time.sleep(1)
        
        # Retrieve the employee again to verify persistence
        success2, status2, data2 = self.make_request(
            'GET',
            f'employees/{self.created_employee_id}',
            expected_status=200
        )
        
        if success2:
            position_persisted = data2.get('position') == update_data['position']
            phone_persisted = data2.get('phone') == update_data['phone']
            
            return self.log_test(
                "Data persistence position and phone",
                position_persisted and phone_persisted,
                f"Data persisted correctly - position: '{data2.get('position')}', phone: '{data2.get('phone')}'"
            )
        else:
            return self.log_test(
                "Data persistence position and phone",
                False,
                f"Failed to retrieve employee: Status {status2}"
            )

    def test_position_phone_in_employee_list(self):
        """Test that position and phone fields are included in employee list endpoint"""
        if not self.token:
            return self.log_test("Position and phone in employee list", False, "No token available")
        
        success, status, data = self.make_request('GET', 'employees')
        
        if success and isinstance(data, list) and len(data) > 0:
            # Check if any employee has position and phone fields
            has_position_field = any('position' in emp for emp in data)
            has_phone_field = any('phone' in emp for emp in data)
            
            # Find employees with actual position/phone values
            employees_with_position = [emp for emp in data if emp.get('position')]
            employees_with_phone = [emp for emp in data if emp.get('phone')]
            
            return self.log_test(
                "Position and phone in employee list",
                has_position_field and has_phone_field,
                f"Employee list includes position/phone fields. {len(employees_with_position)} have position, {len(employees_with_phone)} have phone"
            )
        else:
            return self.log_test(
                "Position and phone in employee list",
                False,
                f"Status: {status}, Data: {data}"
            )

    def run_all_tests(self):
        """Run all position and phone field tests"""
        print("🚀 Starting Position and Phone Field Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Position and Phone field functionality")
        print("=" * 80)
        
        # Login first
        if not self.test_login_with_admin():
            print("❌ Cannot proceed without admin login")
            return 1
        
        print("\n📝 Position and Phone Field Tests:")
        self.test_create_employee_with_position_phone()
        self.test_retrieve_employee_with_position_phone()
        self.test_update_employee_profile_position_phone()
        self.test_update_employee_with_empty_position_phone()
        self.test_update_employee_with_null_position_phone()
        self.test_create_employee_without_position_phone()
        self.test_update_existing_employee_add_position_phone()
        self.test_data_persistence_position_phone()
        self.test_position_phone_in_employee_list()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Position and Phone Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All position and phone field tests passed!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Position and phone field implementation needs review.")
            return 1

def main():
    """Main test runner"""
    tester = PositionPhoneFieldTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())