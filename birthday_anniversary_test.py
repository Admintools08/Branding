#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta, date
import time

class BirthdayAnniversaryTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_employees = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, files=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if files:
                headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers, timeout=15)
                else:
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

    def test_login_with_admin_credentials(self):
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

    def test_create_employee_with_birthday(self):
        """Test creating employees with birthday field"""
        if not self.token:
            return self.log_test("Create employee with birthday", False, "No token available")
        
        # Create 3 employees with different birthdays and start dates
        employees_data = [
            {
                "name": "Alice Johnson",
                "employee_id": f"EMP{int(time.time())}001",
                "email": f"alice.{int(time.time())}@test.com",
                "department": "Engineering",
                "manager": "Tech Lead",
                "start_date": "2023-01-15T00:00:00Z",
                "birthday": "1990-12-25T00:00:00Z",  # Christmas birthday
                "status": "active"
            },
            {
                "name": "Bob Smith",
                "employee_id": f"EMP{int(time.time())}002",
                "email": f"bob.{int(time.time())}@test.com",
                "department": "Marketing",
                "manager": "Marketing Head",
                "start_date": "2022-06-01T00:00:00Z",
                "birthday": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%dT00:00:00Z"),  # Birthday in 5 days
                "status": "active"
            },
            {
                "name": "Carol Davis",
                "employee_id": f"EMP{int(time.time())}003",
                "email": f"carol.{int(time.time())}@test.com",
                "department": "HR",
                "manager": "HR Director",
                "start_date": "2021-03-10T00:00:00Z",
                "birthday": datetime.now().strftime("%Y-%m-%dT00:00:00Z"),  # Birthday today
                "status": "active"
            }
        ]
        
        created_count = 0
        for emp_data in employees_data:
            success, status, data = self.make_request(
                'POST',
                'employees',
                emp_data,
                expected_status=200
            )
            
            if success and 'id' in data:
                self.created_employees.append(data['id'])
                created_count += 1
                
                # Verify birthday field is saved correctly
                birthday_saved = data.get('birthday') is not None
                if not birthday_saved:
                    return self.log_test(
                        "Create employee with birthday",
                        False,
                        f"Birthday field not saved for {emp_data['name']}"
                    )
        
        return self.log_test(
            "Create employee with birthday",
            created_count == 3,
            f"Created {created_count}/3 employees with birthday fields"
        )

    def test_update_employee_with_birthday(self):
        """Test updating existing employee to add birthday"""
        if not self.token or not self.created_employees:
            return self.log_test("Update employee with birthday", False, "No token or employees available")
        
        employee_id = self.created_employees[0]
        
        # Update employee with new birthday
        update_data = {
            "birthday": "1985-07-04T00:00:00Z",  # Independence Day birthday
            "name": "Alice Johnson Updated"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{employee_id}/profile',
            update_data,
            expected_status=200
        )
        
        if success:
            # Verify the birthday was updated
            birthday_updated = data.get('birthday') == "1985-07-04T00:00:00+00:00"
            name_updated = data.get('name') == "Alice Johnson Updated"
            
            return self.log_test(
                "Update employee with birthday",
                birthday_updated and name_updated,
                f"Birthday updated: {birthday_updated}, Name updated: {name_updated}"
            )
        else:
            return self.log_test(
                "Update employee with birthday",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_dashboard_upcoming_events_endpoint(self):
        """Test GET /api/dashboard/upcoming-events endpoint"""
        if not self.token:
            return self.log_test("Dashboard upcoming events endpoint", False, "No token available")
        
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if success:
            # Verify response structure
            required_fields = ['upcoming_birthdays', 'upcoming_anniversaries', 'upcoming_events']
            has_required_fields = all(field in data for field in required_fields)
            
            # Check if we have data
            has_birthdays = isinstance(data.get('upcoming_birthdays'), list)
            has_anniversaries = isinstance(data.get('upcoming_anniversaries'), list)
            has_events = isinstance(data.get('upcoming_events'), list)
            
            # Verify event structure if events exist
            event_structure_valid = True
            if data.get('upcoming_events'):
                first_event = data['upcoming_events'][0]
                required_event_fields = ['employee', 'date', 'days_until', 'type']
                event_structure_valid = all(field in first_event for field in required_event_fields)
            
            return self.log_test(
                "Dashboard upcoming events endpoint",
                has_required_fields and has_birthdays and has_anniversaries and has_events and event_structure_valid,
                f"Birthdays: {len(data.get('upcoming_birthdays', []))}, Anniversaries: {len(data.get('upcoming_anniversaries', []))}, Events: {len(data.get('upcoming_events', []))}"
            )
        else:
            return self.log_test(
                "Dashboard upcoming events endpoint",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_dashboard_upcoming_tasks_endpoint(self):
        """Test GET /api/dashboard/upcoming-tasks endpoint"""
        if not self.token:
            return self.log_test("Dashboard upcoming tasks endpoint", False, "No token available")
        
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-tasks',
            expected_status=200
        )
        
        if success:
            # Verify response structure
            required_fields = ['upcoming_tasks', 'overdue_count', 'due_this_week']
            has_required_fields = all(field in data for field in required_fields)
            
            # Check data types
            has_tasks_list = isinstance(data.get('upcoming_tasks'), list)
            has_overdue_count = isinstance(data.get('overdue_count'), int)
            has_due_this_week = isinstance(data.get('due_this_week'), int)
            
            # Verify task structure if tasks exist
            task_structure_valid = True
            if data.get('upcoming_tasks'):
                first_task = data['upcoming_tasks'][0]
                required_task_fields = ['task', 'employee', 'days_until', 'is_overdue', 'priority']
                task_structure_valid = all(field in first_task for field in required_task_fields)
            
            return self.log_test(
                "Dashboard upcoming tasks endpoint",
                has_required_fields and has_tasks_list and has_overdue_count and has_due_this_week and task_structure_valid,
                f"Tasks: {len(data.get('upcoming_tasks', []))}, Overdue: {data.get('overdue_count', 0)}, Due this week: {data.get('due_this_week', 0)}"
            )
        else:
            return self.log_test(
                "Dashboard upcoming tasks endpoint",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_birthday_calculation_logic(self):
        """Test birthday calculation logic with edge cases"""
        if not self.token:
            return self.log_test("Birthday calculation logic", False, "No token available")
        
        # Get upcoming events
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Birthday calculation logic",
                False,
                f"Failed to get events data. Status: {status}"
            )
        
        # Verify birthday calculations
        today = date.today()
        calculation_correct = True
        
        for event in data.get('upcoming_events', []):
            if event.get('type') == 'birthday':
                event_date = datetime.fromisoformat(event['date']).date()
                calculated_days = (event_date - today).days
                reported_days = event['days_until']
                
                # Allow for small differences due to timezone/timing
                if abs(calculated_days - reported_days) > 1:
                    calculation_correct = False
                    break
        
        # Check for today's birthday (should have days_until = 0)
        today_birthdays = [e for e in data.get('upcoming_events', []) if e.get('type') == 'birthday' and e.get('days_until') == 0]
        
        return self.log_test(
            "Birthday calculation logic",
            calculation_correct,
            f"Birthday calculations correct. Today's birthdays: {len(today_birthdays)}"
        )

    def test_work_anniversary_calculation(self):
        """Test work anniversary calculation based on start_date"""
        if not self.token:
            return self.log_test("Work anniversary calculation", False, "No token available")
        
        # Get upcoming events
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Work anniversary calculation",
                False,
                f"Failed to get events data. Status: {status}"
            )
        
        # Verify anniversary calculations
        today = date.today()
        calculation_correct = True
        
        for event in data.get('upcoming_anniversaries', []):
            if 'years_of_service' in event:
                # Verify years of service calculation
                employee = event.get('employee', {})
                if 'start_date' in employee:
                    start_date = datetime.fromisoformat(employee['start_date']).date()
                    expected_years = today.year - start_date.year
                    
                    # Adjust if anniversary hasn't occurred this year
                    anniversary_this_year = start_date.replace(year=today.year)
                    if anniversary_this_year > today:
                        expected_years -= 1
                    
                    reported_years = event.get('years_of_service', 0)
                    
                    # Allow for edge cases around the anniversary date
                    if abs(expected_years - reported_years) > 1:
                        calculation_correct = False
                        break
        
        return self.log_test(
            "Work anniversary calculation",
            calculation_correct,
            f"Anniversary calculations correct. Found {len(data.get('upcoming_anniversaries', []))} upcoming anniversaries"
        )

    def test_edge_case_birthdays_today_tomorrow_future(self):
        """Test edge cases: birthdays today, tomorrow, and in future"""
        if not self.token:
            return self.log_test("Edge case birthdays", False, "No token available")
        
        # Create employees with specific birthday dates for testing
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        future_date = today + timedelta(days=15)
        
        edge_case_employees = [
            {
                "name": "Today Birthday",
                "employee_id": f"TODAY{int(time.time())}",
                "email": f"today.{int(time.time())}@test.com",
                "department": "Testing",
                "manager": "Test Manager",
                "start_date": "2023-01-01T00:00:00Z",
                "birthday": today.strftime("%Y-%m-%dT00:00:00Z"),
                "status": "active"
            },
            {
                "name": "Tomorrow Birthday",
                "employee_id": f"TOMORROW{int(time.time())}",
                "email": f"tomorrow.{int(time.time())}@test.com",
                "department": "Testing",
                "manager": "Test Manager",
                "start_date": "2023-01-01T00:00:00Z",
                "birthday": tomorrow.strftime("%Y-%m-%dT00:00:00Z"),
                "status": "active"
            },
            {
                "name": "Future Birthday",
                "employee_id": f"FUTURE{int(time.time())}",
                "email": f"future.{int(time.time())}@test.com",
                "department": "Testing",
                "manager": "Test Manager",
                "start_date": "2023-01-01T00:00:00Z",
                "birthday": future_date.strftime("%Y-%m-%dT00:00:00Z"),
                "status": "active"
            }
        ]
        
        # Create the test employees
        created_edge_case_employees = []
        for emp_data in edge_case_employees:
            success, status, data = self.make_request(
                'POST',
                'employees',
                emp_data,
                expected_status=200
            )
            
            if success and 'id' in data:
                created_edge_case_employees.append(data['id'])
                self.created_employees.append(data['id'])
        
        # Wait a moment for data to be processed
        time.sleep(1)
        
        # Get upcoming events and verify edge cases
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Edge case birthdays",
                False,
                f"Failed to get events after creating edge case employees. Status: {status}"
            )
        
        # Check for today's birthday (days_until = 0)
        today_birthdays = [e for e in data.get('upcoming_events', []) if e.get('type') == 'birthday' and e.get('days_until') == 0]
        
        # Check for tomorrow's birthday (days_until = 1)
        tomorrow_birthdays = [e for e in data.get('upcoming_events', []) if e.get('type') == 'birthday' and e.get('days_until') == 1]
        
        # Check for future birthday (days_until = 15)
        future_birthdays = [e for e in data.get('upcoming_events', []) if e.get('type') == 'birthday' and e.get('days_until') >= 14 and e.get('days_until') <= 16]
        
        edge_cases_working = len(today_birthdays) >= 1 and len(tomorrow_birthdays) >= 1 and len(future_birthdays) >= 1
        
        return self.log_test(
            "Edge case birthdays",
            edge_cases_working,
            f"Today: {len(today_birthdays)}, Tomorrow: {len(tomorrow_birthdays)}, Future (15 days): {len(future_birthdays)}"
        )

    def test_employee_information_in_events(self):
        """Test that dashboard endpoints return proper employee information"""
        if not self.token:
            return self.log_test("Employee information in events", False, "No token available")
        
        # Get upcoming events
        success, status, data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Employee information in events",
                False,
                f"Failed to get events data. Status: {status}"
            )
        
        # Verify employee information is complete
        employee_info_complete = True
        
        for event in data.get('upcoming_events', []):
            employee = event.get('employee', {})
            required_employee_fields = ['id', 'name', 'email', 'department', 'status']
            
            if not all(field in employee for field in required_employee_fields):
                employee_info_complete = False
                break
        
        # Also check upcoming tasks for employee information
        task_success, task_status, task_data = self.make_request(
            'GET',
            'dashboard/upcoming-tasks',
            expected_status=200
        )
        
        task_employee_info_complete = True
        if task_success:
            for task_item in task_data.get('upcoming_tasks', []):
                employee = task_item.get('employee', {})
                if employee:  # Employee might be None for some tasks
                    required_employee_fields = ['id', 'name', 'email', 'department']
                    if not all(field in employee for field in required_employee_fields):
                        task_employee_info_complete = False
                        break
        
        return self.log_test(
            "Employee information in events",
            employee_info_complete and task_employee_info_complete,
            f"Events employee info complete: {employee_info_complete}, Tasks employee info complete: {task_employee_info_complete}"
        )

    def test_data_format_validation(self):
        """Test that dashboard endpoints return data in expected format"""
        if not self.token:
            return self.log_test("Data format validation", False, "No token available")
        
        # Test upcoming events format
        success1, status1, events_data = self.make_request(
            'GET',
            'dashboard/upcoming-events',
            expected_status=200
        )
        
        # Test upcoming tasks format
        success2, status2, tasks_data = self.make_request(
            'GET',
            'dashboard/upcoming-tasks',
            expected_status=200
        )
        
        if not (success1 and success2):
            return self.log_test(
                "Data format validation",
                False,
                f"API calls failed. Events: {status1}, Tasks: {status2}"
            )
        
        # Validate events data format
        events_format_valid = True
        if events_data.get('upcoming_events'):
            for event in events_data['upcoming_events']:
                # Check required fields and types
                if not isinstance(event.get('days_until'), int):
                    events_format_valid = False
                    break
                if event.get('type') not in ['birthday', 'work_anniversary']:
                    events_format_valid = False
                    break
                if not isinstance(event.get('employee'), dict):
                    events_format_valid = False
                    break
        
        # Validate tasks data format
        tasks_format_valid = True
        if tasks_data.get('upcoming_tasks'):
            for task_item in tasks_data['upcoming_tasks']:
                # Check required fields and types
                if not isinstance(task_item.get('days_until'), int):
                    tasks_format_valid = False
                    break
                if not isinstance(task_item.get('is_overdue'), bool):
                    tasks_format_valid = False
                    break
                if task_item.get('priority') not in ['high', 'medium', 'low']:
                    tasks_format_valid = False
                    break
        
        return self.log_test(
            "Data format validation",
            events_format_valid and tasks_format_valid,
            f"Events format valid: {events_format_valid}, Tasks format valid: {tasks_format_valid}"
        )

    def test_cleanup_test_employees(self):
        """Clean up test employees created during testing"""
        if not self.token or not self.created_employees:
            return self.log_test("Cleanup test employees", True, "No cleanup needed")
        
        cleanup_success = True
        cleaned_count = 0
        
        for employee_id in self.created_employees:
            success, status, data = self.make_request(
                'DELETE',
                f'employees/{employee_id}',
                expected_status=200
            )
            
            if success:
                cleaned_count += 1
            else:
                cleanup_success = False
        
        return self.log_test(
            "Cleanup test employees",
            cleanup_success,
            f"Cleaned up {cleaned_count}/{len(self.created_employees)} test employees"
        )

    def run_all_tests(self):
        """Run all birthday/anniversary reminder system tests"""
        print("🎂 Starting Birthday/Anniversary Reminder System Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Birthday/Anniversary tracking and dashboard improvements")
        print("=" * 80)
        
        # Authentication
        print("\n🔐 Authentication:")
        self.test_login_with_admin_credentials()
        
        # Employee Management with Birthday Field
        print("\n👥 Employee Management with Birthday Field:")
        self.test_create_employee_with_birthday()
        self.test_update_employee_with_birthday()
        
        # Dashboard Endpoints
        print("\n📊 Dashboard Endpoints:")
        self.test_dashboard_upcoming_events_endpoint()
        self.test_dashboard_upcoming_tasks_endpoint()
        
        # Logic Verification
        print("\n🧮 Logic Verification:")
        self.test_birthday_calculation_logic()
        self.test_work_anniversary_calculation()
        
        # Edge Cases
        print("\n🔍 Edge Cases:")
        self.test_edge_case_birthdays_today_tomorrow_future()
        
        # Data Quality
        print("\n📋 Data Quality:")
        self.test_employee_information_in_events()
        self.test_data_format_validation()
        
        # Cleanup
        print("\n🧹 Cleanup:")
        self.test_cleanup_test_employees()
        
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