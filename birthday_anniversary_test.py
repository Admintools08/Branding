#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta, date
import time

class BirthdayAnniversaryTester:
    def __init__(self, base_url="https://employee-fix-plus.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_employees = []

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

    def test_employee_model_with_birthday(self):
        """Test Employee model updates - verify birthday field is included in Employee creation"""
        if not self.token:
            return self.log_test("Employee model with birthday", False, "No token available")
        
        # Create employee with birthday field
        birthday_date = datetime(1990, 6, 15, tzinfo=timezone.utc)
        start_date = datetime(2023, 1, 15, tzinfo=timezone.utc)
        
        employee_data = {
            "name": "John Birthday Test",
            "employee_id": f"BDAY{int(time.time())}",
            "email": f"john.birthday.{int(time.time())}@test.com",
            "department": "Testing",
            "manager": "Test Manager",
            "start_date": start_date.isoformat(),
            "birthday": birthday_date.isoformat(),
            "status": "active"
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if success:
            self.test_employees.append(data.get('id'))
            # Verify birthday field is present in response
            has_birthday = 'birthday' in data and data['birthday'] is not None
            birthday_correct = data.get('birthday', '').startswith('1990-06-15')
            
            return self.log_test(
                "Employee model with birthday",
                has_birthday and birthday_correct,
                f"Employee created with birthday: {data.get('birthday', 'None')}"
            )
        else:
            return self.log_test(
                "Employee model with birthday",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_post_employees_endpoint_with_birthday(self):
        """Test POST /employees endpoint with birthday field"""
        if not self.token:
            return self.log_test("POST employees with birthday", False, "No token available")
        
        # Create another employee with different birthday
        birthday_date = datetime(1985, 12, 25, tzinfo=timezone.utc)  # Christmas birthday
        start_date = datetime(2022, 3, 10, tzinfo=timezone.utc)
        
        employee_data = {
            "name": "Sarah Christmas Test",
            "employee_id": f"XMAS{int(time.time())}",
            "email": f"sarah.christmas.{int(time.time())}@test.com",
            "department": "HR",
            "manager": "HR Director",
            "start_date": start_date.isoformat(),
            "birthday": birthday_date.isoformat(),
            "status": "active"
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            employee_data,
            expected_status=200
        )
        
        if success:
            self.test_employees.append(data.get('id'))
            # Verify all fields including birthday
            has_required_fields = all(field in data for field in ['name', 'employee_id', 'email', 'birthday'])
            birthday_correct = data.get('birthday', '').startswith('1985-12-25')
            
            return self.log_test(
                "POST employees with birthday",
                has_required_fields and birthday_correct,
                f"Employee created successfully with birthday: {data.get('birthday', 'None')}"
            )
        else:
            return self.log_test(
                "POST employees with birthday",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_put_employee_profile_with_birthday(self):
        """Test PUT /employees/{employee_id}/profile endpoint with birthday field updates"""
        if not self.token or not self.test_employees:
            return self.log_test("PUT employee profile with birthday", False, "No token or test employees available")
        
        employee_id = self.test_employees[0]
        
        # Update employee birthday
        new_birthday = datetime(1992, 8, 20, tzinfo=timezone.utc)
        update_data = {
            "name": "John Updated Birthday",
            "birthday": new_birthday.isoformat(),
            "department": "Updated Testing Department"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            # Verify birthday was updated
            birthday_updated = data.get('birthday', '').startswith('1992-08-20')
            name_updated = data.get('name') == "John Updated Birthday"
            department_updated = data.get('department') == "Updated Testing Department"
            
            return self.log_test(
                "PUT employee profile with birthday",
                birthday_updated and name_updated and department_updated,
                f"Employee updated - Birthday: {data.get('birthday', 'None')}, Name: {data.get('name', 'None')}"
            )
        else:
            return self.log_test(
                "PUT employee profile with birthday",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_dashboard_upcoming_events_endpoint(self):
        """Test GET /api/dashboard/upcoming-events endpoint"""
        if not self.token:
            return self.log_test("Dashboard upcoming events", False, "No token available")
        
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if success:
            # Verify response structure
            has_birthdays = 'upcoming_birthdays' in data
            has_anniversaries = 'upcoming_anniversaries' in data
            has_events = 'upcoming_events' in data
            
            # Check if data is properly structured
            birthdays_is_list = isinstance(data.get('upcoming_birthdays', []), list)
            anniversaries_is_list = isinstance(data.get('upcoming_anniversaries', []), list)
            events_is_list = isinstance(data.get('upcoming_events', []), list)
            
            structure_valid = has_birthdays and has_anniversaries and has_events
            data_types_valid = birthdays_is_list and anniversaries_is_list and events_is_list
            
            # Count events
            birthday_count = len(data.get('upcoming_birthdays', []))
            anniversary_count = len(data.get('upcoming_anniversaries', []))
            total_events = len(data.get('upcoming_events', []))
            
            return self.log_test(
                "Dashboard upcoming events",
                structure_valid and data_types_valid,
                f"Birthdays: {birthday_count}, Anniversaries: {anniversary_count}, Total events: {total_events}"
            )
        else:
            return self.log_test(
                "Dashboard upcoming events",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_dashboard_upcoming_tasks_endpoint(self):
        """Test GET /api/dashboard/upcoming-tasks endpoint"""
        if not self.token:
            return self.log_test("Dashboard upcoming tasks", False, "No token available")
        
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-tasks',
            expected_status=200
        )
        
        if success:
            # Verify response structure
            has_upcoming_tasks = 'upcoming_tasks' in data
            has_overdue_count = 'overdue_count' in data
            has_due_this_week = 'due_this_week' in data
            
            # Check data types
            tasks_is_list = isinstance(data.get('upcoming_tasks', []), list)
            overdue_is_number = isinstance(data.get('overdue_count', 0), int)
            due_week_is_number = isinstance(data.get('due_this_week', 0), int)
            
            structure_valid = has_upcoming_tasks and has_overdue_count and has_due_this_week
            data_types_valid = tasks_is_list and overdue_is_number and due_week_is_number
            
            # Count tasks
            upcoming_count = len(data.get('upcoming_tasks', []))
            overdue_count = data.get('overdue_count', 0)
            due_this_week = data.get('due_this_week', 0)
            
            return self.log_test(
                "Dashboard upcoming tasks",
                structure_valid and data_types_valid,
                f"Upcoming: {upcoming_count}, Overdue: {overdue_count}, Due this week: {due_this_week}"
            )
        else:
            return self.log_test(
                "Dashboard upcoming tasks",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_create_employees_with_different_birthdays(self):
        """Create test employees with different birthdays and start dates to verify upcoming events logic"""
        if not self.token:
            return self.log_test("Create employees with different birthdays", False, "No token available")
        
        # Create employees with birthdays in the next 30 days
        today = date.today()
        
        test_employees_data = [
            {
                "name": "Alice Tomorrow Birthday",
                "birthday": datetime(1988, today.month, (today + timedelta(days=1)).day, tzinfo=timezone.utc),
                "start_date": datetime(2020, 1, 15, tzinfo=timezone.utc),
                "department": "Marketing"
            },
            {
                "name": "Bob Next Week Birthday", 
                "birthday": datetime(1990, today.month, (today + timedelta(days=7)).day, tzinfo=timezone.utc),
                "start_date": datetime(2019, 6, 10, tzinfo=timezone.utc),
                "department": "Sales"
            },
            {
                "name": "Carol Anniversary Soon",
                "birthday": datetime(1987, 3, 15, tzinfo=timezone.utc),
                "start_date": datetime(today.year, today.month, (today + timedelta(days=5)).day, tzinfo=timezone.utc),
                "department": "Engineering"
            }
        ]
        
        created_count = 0
        
        for i, emp_data in enumerate(test_employees_data):
            employee_data = {
                "name": emp_data["name"],
                "employee_id": f"TEST{int(time.time())}{i}",
                "email": f"test.employee.{int(time.time())}.{i}@test.com",
                "department": emp_data["department"],
                "manager": "Test Manager",
                "start_date": emp_data["start_date"].isoformat(),
                "birthday": emp_data["birthday"].isoformat(),
                "status": "active"
            }
            
            success, status, data = self.make_request(
                'POST',
                'employees',
                employee_data,
                expected_status=200
            )
            
            if success:
                self.test_employees.append(data.get('id'))
                created_count += 1
        
        return self.log_test(
            "Create employees with different birthdays",
            created_count == len(test_employees_data),
            f"Created {created_count}/{len(test_employees_data)} test employees with varied birthdays and anniversaries"
        )

    def test_upcoming_events_logic_verification(self):
        """Verify the upcoming events logic works correctly with test data"""
        if not self.token:
            return self.log_test("Upcoming events logic verification", False, "No token available")
        
        # Get upcoming events after creating test employees
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if success:
            upcoming_birthdays = data.get('upcoming_birthdays', [])
            upcoming_anniversaries = data.get('upcoming_anniversaries', [])
            
            # Check if our test employees appear in the results
            birthday_names = [event.get('employee', {}).get('name', '') for event in upcoming_birthdays]
            anniversary_names = [event.get('employee', {}).get('name', '') for event in upcoming_anniversaries]
            
            # Look for our test employees
            alice_found = any('Alice Tomorrow Birthday' in name for name in birthday_names)
            bob_found = any('Bob Next Week Birthday' in name for name in birthday_names)
            carol_anniversary_found = any('Carol Anniversary Soon' in name for name in anniversary_names)
            
            # Verify days_until calculation
            valid_days_calculation = True
            for event in upcoming_birthdays + upcoming_anniversaries:
                days_until = event.get('days_until', -1)
                if days_until < 0 or days_until > 30:
                    valid_days_calculation = False
                    break
            
            logic_working = alice_found or bob_found or carol_anniversary_found
            
            return self.log_test(
                "Upcoming events logic verification",
                logic_working and valid_days_calculation,
                f"Test employees found in events: Alice({alice_found}), Bob({bob_found}), Carol Anniversary({carol_anniversary_found}). Days calculation valid: {valid_days_calculation}"
            )
        else:
            return self.log_test(
                "Upcoming events logic verification",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_birthday_field_persistence(self):
        """Test that birthday field persists correctly in database"""
        if not self.token or not self.test_employees:
            return self.log_test("Birthday field persistence", False, "No token or test employees available")
        
        employee_id = self.test_employees[0]
        
        # Get employee details
        success, status, data = self.make_request(
            'GET',
            f'employees/{employee_id}',
            expected_status=200
        )
        
        if success:
            has_birthday = 'birthday' in data and data['birthday'] is not None
            birthday_format_valid = False
            
            if has_birthday:
                birthday_str = data['birthday']
                # Check if it's a valid ISO format datetime string
                try:
                    parsed_birthday = datetime.fromisoformat(birthday_str.replace('Z', '+00:00'))
                    birthday_format_valid = True
                except:
                    birthday_format_valid = False
            
            return self.log_test(
                "Birthday field persistence",
                has_birthday and birthday_format_valid,
                f"Birthday field persisted: {data.get('birthday', 'None')}, Format valid: {birthday_format_valid}"
            )
        else:
            return self.log_test(
                "Birthday field persistence",
                False,
                f"Status: {status}, Data: {data}"
            )

    def cleanup_test_data(self):
        """Clean up test employees created during testing"""
        if not self.token:
            return self.log_test("Cleanup test data", True, "No cleanup needed - no token")
        
        cleanup_count = 0
        
        for employee_id in self.test_employees:
            success, status, data = self.make_request(
                'DELETE',
                f'employees/{employee_id}',
                expected_status=200
            )
            if success:
                cleanup_count += 1
        
        return self.log_test(
            "Cleanup test data",
            cleanup_count == len(self.test_employees),
            f"Cleaned up {cleanup_count}/{len(self.test_employees)} test employees"
        )

    def run_all_tests(self):
        """Run all birthday/anniversary reminder system tests"""
        print("🎂 Starting Birthday/Anniversary Reminder System Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Birthday field functionality and new dashboard endpoints")
        print("=" * 80)
        
        # Authentication
        print("\n🔐 Authentication:")
        self.test_login_with_admin()
        
        # Employee Model Tests
        print("\n👤 Employee Model with Birthday Field Tests:")
        self.test_employee_model_with_birthday()
        self.test_post_employees_endpoint_with_birthday()
        self.test_put_employee_profile_with_birthday()
        self.test_birthday_field_persistence()
        
        # Dashboard Endpoints Tests
        print("\n📊 Dashboard Endpoints Tests:")
        self.test_dashboard_upcoming_events_endpoint()
        self.test_dashboard_upcoming_tasks_endpoint()
        
        # Logic Verification Tests
        print("\n🧪 Logic Verification Tests:")
        self.test_create_employees_with_different_birthdays()
        self.test_upcoming_events_logic_verification()
        
        # Cleanup
        print("\n🧹 Cleanup:")
        self.cleanup_test_data()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Birthday/Anniversary Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All birthday/anniversary reminder system tests passed!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please review the implementation.")
            return 1

def main():
    """Main test runner"""
    tester = BirthdayAnniversaryTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())