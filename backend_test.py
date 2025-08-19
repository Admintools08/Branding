#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time
import io
import tempfile
import os

class HRSystemAPITester:
    def __init__(self, base_url="https://2307fe85-3f87-4e26-a9d7-6ad6750c69d8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_employee_id = None
        self.excel_imported_employee_id = None

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

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        success, status, data = self.make_request(
            'POST', 
            'auth/login',
            {"email": "invalid@test.com", "password": "wrongpass"},
            expected_status=401
        )
        return self.log_test(
            "Login with invalid credentials", 
            success,
            f"Status: {status}"
        )

    def test_login_valid_credentials(self):
        """Test login with new admin credentials"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "omnathtripathi1@gmail.com", "password": "BrandingPioneers2024!"},
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            return self.log_test(
                "Login with new admin credentials",
                True,
                f"Token received, User: {data.get('user', {}).get('name', 'Unknown')}"
            )
        else:
            return self.log_test(
                "Login with new admin credentials",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_auth_me(self):
        """Test getting current user info"""
        if not self.token:
            return self.log_test("Get current user info", False, "No token available")
        
        success, status, data = self.make_request('GET', 'auth/me')
        return self.log_test(
            "Get current user info",
            success and 'email' in data,
            f"User: {data.get('name', 'Unknown')}"
        )

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, status, data = self.make_request('GET', 'dashboard/stats')
        
        has_required_fields = (
            'employee_stats' in data and 
            'task_stats' in data and
            isinstance(data['employee_stats'], dict) and
            isinstance(data['task_stats'], dict)
        )
        
        return self.log_test(
            "Dashboard stats",
            success and has_required_fields,
            f"Employee stats: {data.get('employee_stats', {})}, Task stats: {data.get('task_stats', {})}"
        )

    def test_get_employees_empty(self):
        """Test getting employees list (initially empty)"""
        success, status, data = self.make_request('GET', 'employees')
        return self.log_test(
            "Get employees list",
            success and isinstance(data, list),
            f"Found {len(data) if isinstance(data, list) else 0} employees"
        )

    def test_create_employee(self):
        """Test creating a new employee"""
        employee_data = {
            "name": "John Doe",
            "employee_id": f"EMP{int(time.time())}",
            "email": f"john.doe.{int(time.time())}@company.com",
            "department": "Engineering",
            "manager": "Jane Smith",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        success, status, data = self.make_request('POST', 'employees', employee_data, expected_status=200)
        
        if success and 'id' in data:
            self.created_employee_id = data['id']
            return self.log_test(
                "Create employee",
                True,
                f"Created employee: {data['name']} (ID: {data['id']})"
            )
        else:
            return self.log_test(
                "Create employee",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_get_employee_by_id(self):
        """Test getting specific employee by ID"""
        if not self.created_employee_id:
            return self.log_test("Get employee by ID", False, "No employee ID available")
        
        success, status, data = self.make_request('GET', f'employees/{self.created_employee_id}')
        return self.log_test(
            "Get employee by ID",
            success and data.get('id') == self.created_employee_id,
            f"Employee: {data.get('name', 'Unknown')}"
        )

    def test_get_tasks_for_employee(self):
        """Test getting tasks for the created employee"""
        if not self.created_employee_id:
            return self.log_test("Get tasks for employee", False, "No employee ID available")
        
        success, status, data = self.make_request('GET', f'tasks?employee_id={self.created_employee_id}')
        
        # Should have default onboarding tasks
        expected_tasks = 7  # Based on DEFAULT_ONBOARDING_TASKS
        has_tasks = isinstance(data, list) and len(data) >= expected_tasks
        
        return self.log_test(
            "Get tasks for employee",
            success and has_tasks,
            f"Found {len(data) if isinstance(data, list) else 0} tasks (expected >= {expected_tasks})"
        )

    def test_update_task_status(self):
        """Test updating task status"""
        if not self.created_employee_id:
            return self.log_test("Update task status", False, "No employee ID available")
        
        # Get tasks first
        success, status, tasks = self.make_request('GET', f'tasks?employee_id={self.created_employee_id}')
        
        if not success or not tasks:
            return self.log_test("Update task status", False, "No tasks found to update")
        
        # Update first task to completed
        task_id = tasks[0]['id']
        success, status, data = self.make_request(
            'PUT', 
            f'tasks/{task_id}',
            {"status": "completed"}
        )
        
        return self.log_test(
            "Update task status",
            success and data.get('status') == 'completed',
            f"Task {task_id} marked as completed"
        )

    def test_update_employee_to_exiting(self):
        """Test updating employee status to exiting (should create exit tasks)"""
        if not self.created_employee_id:
            return self.log_test("Update employee to exiting", False, "No employee ID available")
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}',
            {"status": "exiting", "exit_date": datetime.now(timezone.utc).isoformat()}
        )
        
        return self.log_test(
            "Update employee to exiting",
            success and data.get('status') == 'exiting',
            f"Employee status updated to exiting"
        )

    def test_get_exit_tasks(self):
        """Test that exit tasks were created"""
        if not self.created_employee_id:
            return self.log_test("Get exit tasks", False, "No employee ID available")
        
        success, status, data = self.make_request('GET', f'tasks?employee_id={self.created_employee_id}&task_type=exit')
        
        # Should have default exit tasks
        expected_exit_tasks = 7  # Based on DEFAULT_EXIT_TASKS
        has_exit_tasks = isinstance(data, list) and len(data) >= expected_exit_tasks
        
        return self.log_test(
            "Get exit tasks",
            success and has_exit_tasks,
            f"Found {len(data) if isinstance(data, list) else 0} exit tasks (expected >= {expected_exit_tasks})"
        )

    def test_dashboard_recent_activities(self):
        """Test dashboard recent activities endpoint"""
        success, status, data = self.make_request('GET', 'dashboard/recent-activities')
        
        has_required_fields = (
            'recent_employees' in data and 
            'recent_tasks' in data and
            isinstance(data['recent_employees'], list) and
            isinstance(data['recent_tasks'], list)
        )
        
        return self.log_test(
            "Dashboard recent activities",
            success and has_required_fields,
            f"Recent employees: {len(data.get('recent_employees', []))}, Recent tasks: {len(data.get('recent_tasks', []))}"
        )

    def test_excel_import(self):
        """Test Excel import functionality"""
        # Create a simple CSV content for testing
        csv_content = """Name,Employee ID,Email,Department,Manager,Start Date
Alice Johnson,EMP2024001,alice.johnson@brandingpioneers.com,Engineering,John Smith,2024-01-15
Bob Wilson,EMP2024002,bob.wilson@brandingpioneers.com,Marketing,Sarah Davis,2024-01-20"""
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Prepare multipart form data
            url = f"{self.api_url}/employees/import-excel"
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_employees.csv', f, 'text/csv')}
                response = requests.post(url, files=files, headers=headers, timeout=15)
            
            success = response.status_code == 200
            try:
                data = response.json()
            except:
                data = {"error": "Invalid JSON response"}
            
            # Check if employees were imported
            if success and data.get('imported_count', 0) > 0:
                # Try to get the imported employees to get their IDs
                emp_success, emp_status, employees = self.make_request('GET', 'employees')
                if emp_success and employees:
                    # Find the imported employee
                    for emp in employees:
                        if emp.get('employee_id') == 'EMP2024001':
                            self.excel_imported_employee_id = emp.get('id')
                            break
            
            return self.log_test(
                "Excel import functionality",
                success and data.get('imported_count', 0) >= 2,
                f"Imported {data.get('imported_count', 0)} employees, Errors: {len(data.get('errors', []))}"
            )
            
        except Exception as e:
            return self.log_test(
                "Excel import functionality",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_delete_employee(self):
        """Test employee deletion functionality"""
        employee_to_delete = self.excel_imported_employee_id or self.created_employee_id
        
        if not employee_to_delete:
            return self.log_test("Delete employee", False, "No employee ID available for deletion")
        
        success, status, data = self.make_request(
            'DELETE',
            f'employees/{employee_to_delete}',
            expected_status=200
        )
        
        # Verify employee is actually deleted
        if success:
            verify_success, verify_status, verify_data = self.make_request(
                'GET',
                f'employees/{employee_to_delete}',
                expected_status=404
            )
            success = verify_success  # Should return 404 (not found)
        
        return self.log_test(
            "Delete employee",
            success,
            f"Employee {employee_to_delete} deleted successfully" if success else f"Status: {status}, Data: {data}"
        )

    def test_pdf_reports(self):
        """Test PDF report generation"""
        # Test employee report
        success, status, data = self.make_request(
            'GET',
            'reports/employees',
            expected_status=200
        )
        
        employee_report_success = success
        
        # Test tasks report
        success, status, data = self.make_request(
            'GET',
            'reports/tasks',
            expected_status=200
        )
        
        tasks_report_success = success
        
        return self.log_test(
            "PDF reports generation",
            employee_report_success and tasks_report_success,
            f"Employee report: {'✓' if employee_report_success else '✗'}, Tasks report: {'✓' if tasks_report_success else '✗'}"
        )

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting HR System API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Authentication tests
        print("\n🔐 Authentication Tests:")
        self.test_login_invalid_credentials()
        self.test_login_valid_credentials()
        self.test_auth_me()
        
        # Dashboard tests
        print("\n📊 Dashboard Tests:")
        self.test_dashboard_stats()
        self.test_dashboard_recent_activities()
        
        # Employee management tests
        print("\n👥 Employee Management Tests:")
        self.test_get_employees_empty()
        self.test_create_employee()
        self.test_get_employee_by_id()
        
        # Task management tests
        print("\n✅ Task Management Tests:")
        self.test_get_tasks_for_employee()
        self.test_update_task_status()
        
        # Business logic tests
        print("\n🔄 Business Logic Tests:")
        self.test_update_employee_to_exiting()
        self.test_get_exit_tasks()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📈 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Please check the issues above.")
            return 1

def main():
    """Main test runner"""
    tester = HRSystemAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())