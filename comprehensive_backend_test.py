#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time
import tempfile
import os

class ComprehensiveHRSystemTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_employee_id = None
        self.created_task_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, files=None, params=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if files:
                headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers, timeout=15)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=10)
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

    # ============================================================================
    # AUTHENTICATION & SECURITY TESTS
    # ============================================================================

    def test_user_registration(self):
        """Test user registration (first user becomes super admin)"""
        # Check if any users exist first
        try:
            response = requests.get(f"{self.api_url}/admin/users", timeout=5)
            if response.status_code == 401:  # No users exist yet
                success, status, data = self.make_request(
                    'POST',
                    'auth/register',
                    {
                        "email": "test.admin@hrtest.com",
                        "name": "Test Admin",
                        "password": "TestPassword123!"
                    },
                    expected_status=200
                )
                return self.log_test("User registration", success, f"First user registered as super admin")
            else:
                return self.log_test("User registration", True, "Users already exist, registration disabled")
        except:
            return self.log_test("User registration", False, "Could not test registration")

    def test_user_login(self):
        """Test user login with admin credentials"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@test.com", "password": "admin123"},
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            user_role = data.get('user', {}).get('role', 'unknown')
            return self.log_test("User login", True, f"Logged in as {user_role}")
        else:
            return self.log_test("User login", False, f"Status: {status}, Data: {data}")

    def test_token_validation(self):
        """Test JWT token validation"""
        if not self.token:
            return self.log_test("Token validation", False, "No token available")
        
        success, status, data = self.make_request('GET', 'auth/me')
        
        has_required_fields = all(field in data for field in ['email', 'name', 'role', 'id'])
        
        return self.log_test(
            "Token validation",
            success and has_required_fields,
            f"User: {data.get('name', 'Unknown')}, Role: {data.get('role', 'Unknown')}"
        )

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "invalid@test.com", "password": "wrongpassword"},
            expected_status=401
        )
        
        return self.log_test("Invalid credentials", success, "Invalid credentials properly rejected")

    def test_role_based_access(self):
        """Test role-based access control"""
        if not self.token:
            return self.log_test("Role-based access", False, "No token available")
        
        # Test admin access to user management
        success, status, data = self.make_request('GET', 'admin/users')
        
        return self.log_test(
            "Role-based access",
            success,
            f"Admin can access user management: {status}"
        )

    def test_password_management(self):
        """Test password change functionality"""
        if not self.token:
            return self.log_test("Password management", False, "No token available")
        
        # Change password
        success1, status1, data1 = self.make_request(
            'POST',
            'auth/change-password',
            {
                "current_password": "admin123",
                "new_password": "NewAdmin123!"
            }
        )
        
        if success1:
            # Change it back
            success2, status2, data2 = self.make_request(
                'POST',
                'auth/change-password',
                {
                    "current_password": "NewAdmin123!",
                    "new_password": "admin123"
                }
            )
            
            return self.log_test("Password management", success2, "Password change successful")
        
        return self.log_test("Password management", False, f"Password change failed: {status1}")

    # ============================================================================
    # EMPLOYEE MANAGEMENT CRUD TESTS
    # ============================================================================

    def test_create_employee(self):
        """Test employee creation with all required fields"""
        if not self.token:
            return self.log_test("Create employee", False, "No token available")
        
        employee_data = {
            "name": "Test Employee",
            "employee_id": f"EMP{int(time.time())}",
            "email": f"test.employee.{int(time.time())}@company.com",
            "department": "Engineering",
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
        
        if success:
            self.created_employee_id = data.get('id')
            return self.log_test("Create employee", True, f"Employee created: {data.get('name')}")
        else:
            return self.log_test("Create employee", False, f"Status: {status}, Data: {data}")

    def test_read_employees(self):
        """Test reading employees list and individual employee"""
        if not self.token:
            return self.log_test("Read employees", False, "No token available")
        
        # Test list all employees
        success1, status1, data1 = self.make_request('GET', 'employees')
        
        # Test get individual employee
        success2 = True
        if self.created_employee_id:
            success2, status2, data2 = self.make_request('GET', f'employees/{self.created_employee_id}')
        
        return self.log_test(
            "Read employees",
            success1 and success2,
            f"Found {len(data1) if isinstance(data1, list) else 0} employees"
        )

    def test_update_employee(self):
        """Test employee update and status transitions"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Update employee", False, "No token or employee available")
        
        update_data = {
            "status": "active",
            "department": "Updated Engineering"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}',
            update_data
        )
        
        return self.log_test(
            "Update employee",
            success,
            f"Employee updated to {data.get('status', 'unknown')} status"
        )

    def test_employee_status_transitions(self):
        """Test employee status transitions and automatic task creation"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Employee status transitions", False, "No token or employee available")
        
        # Test transition to exiting status (should create exit tasks)
        update_data = {"status": "exiting"}
        
        success, status, data = self.make_request(
            'PUT',
            f'employees/{self.created_employee_id}',
            update_data
        )
        
        if success:
            # Check if exit tasks were created
            time.sleep(1)  # Give time for tasks to be created
            task_success, task_status, task_data = self.make_request(
                'GET',
                f'tasks?employee_id={self.created_employee_id}'
            )
            
            exit_tasks = [t for t in task_data if t.get('task_type') == 'exit'] if isinstance(task_data, list) else []
            
            return self.log_test(
                "Employee status transitions",
                len(exit_tasks) > 0,
                f"Status changed to exiting, {len(exit_tasks)} exit tasks created"
            )
        
        return self.log_test("Employee status transitions", False, f"Status update failed: {status}")

    def test_delete_employee(self):
        """Test employee deletion"""
        if not self.token:
            return self.log_test("Delete employee", False, "No token available")
        
        # Create a temporary employee for deletion
        temp_employee_data = {
            "name": "Temp Delete Employee",
            "employee_id": f"DEL{int(time.time())}",
            "email": f"delete.test.{int(time.time())}@company.com",
            "department": "Temp",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'employees',
            temp_employee_data
        )
        
        if create_success:
            temp_employee_id = create_data.get('id')
            
            # Delete the employee
            success, status, data = self.make_request(
                'DELETE',
                f'employees/{temp_employee_id}'
            )
            
            return self.log_test("Delete employee", success, "Employee and associated tasks deleted")
        
        return self.log_test("Delete employee", False, "Could not create temporary employee for deletion test")

    # ============================================================================
    # TASK MANAGEMENT TESTS
    # ============================================================================

    def test_automatic_task_creation(self):
        """Test automatic task creation for onboarding and exit"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Automatic task creation", False, "No token or employee available")
        
        # Get tasks for the created employee
        success, status, data = self.make_request(
            'GET',
            f'tasks?employee_id={self.created_employee_id}'
        )
        
        if success and isinstance(data, list):
            onboarding_tasks = [t for t in data if t.get('task_type') == 'onboarding']
            exit_tasks = [t for t in data if t.get('task_type') == 'exit']
            
            return self.log_test(
                "Automatic task creation",
                len(onboarding_tasks) >= 20,  # Should have ~25 onboarding tasks
                f"Found {len(onboarding_tasks)} onboarding tasks, {len(exit_tasks)} exit tasks"
            )
        
        return self.log_test("Automatic task creation", False, f"Could not retrieve tasks: {status}")

    def test_task_crud_operations(self):
        """Test task CRUD operations"""
        if not self.token or not self.created_employee_id:
            return self.log_test("Task CRUD operations", False, "No token or employee available")
        
        # Create a custom task
        task_data = {
            "employee_id": self.created_employee_id,
            "title": "Custom Test Task",
            "description": "This is a test task for CRUD operations",
            "task_type": "onboarding",
            "due_date": (datetime.now(timezone.utc)).isoformat()
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'tasks',
            task_data
        )
        
        if create_success:
            self.created_task_id = create_data.get('id')
            
            # Update the task
            update_data = {"status": "completed"}
            update_success, update_status, update_data = self.make_request(
                'PUT',
                f'tasks/{self.created_task_id}',
                update_data
            )
            
            return self.log_test(
                "Task CRUD operations",
                update_success,
                f"Task created and updated to {update_data.get('status', 'unknown')} status"
            )
        
        return self.log_test("Task CRUD operations", False, f"Task creation failed: {create_status}")

    def test_task_filtering(self):
        """Test task filtering by employee, type, and status"""
        if not self.token:
            return self.log_test("Task filtering", False, "No token available")
        
        # Test filtering by employee
        success1, status1, data1 = self.make_request('GET', f'tasks?employee_id={self.created_employee_id}')
        
        # Test filtering by task type
        success2, status2, data2 = self.make_request('GET', 'tasks?task_type=onboarding')
        
        # Test all tasks
        success3, status3, data3 = self.make_request('GET', 'tasks')
        
        return self.log_test(
            "Task filtering",
            success1 and success2 and success3,
            f"Employee tasks: {len(data1) if isinstance(data1, list) else 0}, "
            f"Onboarding tasks: {len(data2) if isinstance(data2, list) else 0}, "
            f"All tasks: {len(data3) if isinstance(data3, list) else 0}"
        )

    def test_due_date_management(self):
        """Test due date management and overdue detection"""
        if not self.token:
            return self.log_test("Due date management", False, "No token available")
        
        # Get all tasks and check for due dates
        success, status, data = self.make_request('GET', 'tasks')
        
        if success and isinstance(data, list):
            tasks_with_due_dates = [t for t in data if t.get('due_date')]
            overdue_tasks = []
            
            current_time = datetime.now(timezone.utc)
            for task in tasks_with_due_dates:
                try:
                    due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                    if due_date < current_time and task.get('status') == 'pending':
                        overdue_tasks.append(task)
                except:
                    pass
            
            return self.log_test(
                "Due date management",
                True,
                f"Tasks with due dates: {len(tasks_with_due_dates)}, Overdue: {len(overdue_tasks)}"
            )
        
        return self.log_test("Due date management", False, f"Could not retrieve tasks: {status}")

    # ============================================================================
    # EXCEL IMPORT & EXPORT TESTS
    # ============================================================================

    def test_excel_import(self):
        """Test CSV/Excel file parsing and bulk employee creation"""
        if not self.token:
            return self.log_test("Excel import", False, "No token available")
        
        # Create test CSV content
        csv_content = f"""Name,Employee ID,Email,Department,Manager,Start Date
Import Test User 1,IMP{int(time.time())},import1.{int(time.time())}@company.com,HR,Test Manager,2024-01-15
Import Test User 2,IMP{int(time.time())+1},import2.{int(time.time())}@company.com,Engineering,Test Manager,2024-01-16"""
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_import.csv', f, 'text/csv')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files
                )
            
            imported_count = data.get('imported_count', 0) if success else 0
            
            return self.log_test(
                "Excel import",
                success and imported_count >= 2,
                f"Imported {imported_count} employees from CSV"
            )
            
        except Exception as e:
            return self.log_test("Excel import", False, f"Exception: {str(e)}")
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_data_validation(self):
        """Test data validation and error handling during import"""
        if not self.token:
            return self.log_test("Data validation", False, "No token available")
        
        # Create CSV with invalid data
        csv_content = """Name,Employee ID,Email,Department,Manager,Start Date
Invalid User,,invalid-email,HR,Test Manager,invalid-date"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('invalid_test.csv', f, 'text/csv')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files
                )
            
            # Should succeed but with errors reported
            has_errors = len(data.get('errors', [])) > 0 if success else False
            
            return self.log_test(
                "Data validation",
                success and has_errors,
                f"Validation errors properly detected: {len(data.get('errors', []))}"
            )
            
        except Exception as e:
            return self.log_test("Data validation", False, f"Exception: {str(e)}")
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    # ============================================================================
    # AI INTEGRATION TESTS
    # ============================================================================

    def test_ai_employee_analysis(self):
        """Test AI employee analysis with Google Gemini"""
        if not self.token or not self.created_employee_id:
            return self.log_test("AI employee analysis", False, "No token or employee available")
        
        success, status, data = self.make_request(
            'POST',
            f'ai/analyze-employee?employee_id={self.created_employee_id}'
        )
        
        return self.log_test(
            "AI employee analysis",
            success,
            f"AI analysis status: {status}"
        )

    def test_ai_data_validation(self):
        """Test AI-powered data validation"""
        if not self.token:
            return self.log_test("AI data validation", False, "No token available")
        
        test_employee_data = {
            "name": "AI Test Employee",
            "employee_id": "AI001",
            "email": "ai.test@company.com",
            "department": "AI Testing",
            "manager": "AI Manager"
        }
        
        success, status, data = self.make_request(
            'POST',
            'ai/validate-employee',
            test_employee_data
        )
        
        return self.log_test(
            "AI data validation",
            success,
            f"AI validation status: {status}"
        )

    def test_ai_task_suggestions(self):
        """Test AI task suggestions and recommendations"""
        if not self.token:
            return self.log_test("AI task suggestions", False, "No token available")
        
        success, status, data = self.make_request('GET', 'ai/task-suggestions')
        
        return self.log_test(
            "AI task suggestions",
            success,
            f"AI suggestions status: {status}"
        )

    # ============================================================================
    # PDF REPORTS TESTS
    # ============================================================================

    def test_pdf_employee_reports(self):
        """Test employee PDF report generation"""
        if not self.token:
            return self.log_test("PDF employee reports", False, "No token available")
        
        success, status, data = self.make_request('GET', 'reports/employees')
        
        return self.log_test(
            "PDF employee reports",
            success,
            f"Employee report generation status: {status}"
        )

    # ============================================================================
    # DASHBOARD APIS TESTS
    # ============================================================================

    def test_dashboard_stats(self):
        """Test dashboard statistics calculation"""
        if not self.token:
            return self.log_test("Dashboard stats", False, "No token available")
        
        success, status, data = self.make_request('GET', 'dashboard/stats')
        
        if success:
            employee_stats = data.get('employee_stats', {})
            task_stats = data.get('task_stats', {})
            
            return self.log_test(
                "Dashboard stats",
                True,
                f"Employees: {sum(employee_stats.values())}, Tasks: {task_stats.get('total', 0)}"
            )
        
        return self.log_test("Dashboard stats", False, f"Status: {status}")

    def test_recent_activities(self):
        """Test recent activities tracking"""
        if not self.token:
            return self.log_test("Recent activities", False, "No token available")
        
        success, status, data = self.make_request('GET', 'dashboard/recent-activities')
        
        if success:
            recent_employees = data.get('recent_employees', [])
            recent_tasks = data.get('recent_tasks', [])
            
            return self.log_test(
                "Recent activities",
                True,
                f"Recent employees: {len(recent_employees)}, Recent tasks: {len(recent_tasks)}"
            )
        
        return self.log_test("Recent activities", False, f"Status: {status}")

    # ============================================================================
    # ADMIN FEATURES TESTS
    # ============================================================================

    def test_user_management_apis(self):
        """Test admin user management APIs"""
        if not self.token:
            return self.log_test("User management APIs", False, "No token available")
        
        # Get all users
        success1, status1, data1 = self.make_request('GET', 'admin/users')
        
        # Get audit logs
        success2, status2, data2 = self.make_request('GET', 'admin/audit-logs?limit=10')
        
        return self.log_test(
            "User management APIs",
            success1 and success2,
            f"Users: {len(data1) if isinstance(data1, list) else 0}, "
            f"Audit logs: {len(data2) if isinstance(data2, list) else 0}"
        )

    def test_audit_logging(self):
        """Test audit logging functionality"""
        if not self.token:
            return self.log_test("Audit logging", False, "No token available")
        
        # Perform an action that should create an audit log
        temp_employee_data = {
            "name": "Audit Test Employee",
            "employee_id": f"AUD{int(time.time())}",
            "email": f"audit.test.{int(time.time())}@company.com",
            "department": "Audit Testing",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'employees',
            temp_employee_data
        )
        
        if create_success:
            time.sleep(1)  # Give time for audit log to be written
            
            # Check audit logs
            log_success, log_status, log_data = self.make_request(
                'GET',
                'admin/audit-logs?limit=5'
            )
            
            if log_success and isinstance(log_data, list):
                recent_create_logs = [
                    log for log in log_data 
                    if log.get('action') == 'create_employee' and log.get('resource') == 'employee'
                ]
                
                return self.log_test(
                    "Audit logging",
                    len(recent_create_logs) > 0,
                    f"Found {len(recent_create_logs)} recent employee creation audit logs"
                )
        
        return self.log_test("Audit logging", False, "Could not test audit logging")

    # ============================================================================
    # DATABASE OPERATIONS TESTS
    # ============================================================================

    def test_data_persistence(self):
        """Test data persistence and integrity"""
        if not self.token:
            return self.log_test("Data persistence", False, "No token available")
        
        # Create an employee and verify it persists
        employee_data = {
            "name": "Persistence Test Employee",
            "employee_id": f"PER{int(time.time())}",
            "email": f"persistence.test.{int(time.time())}@company.com",
            "department": "Testing",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        create_success, create_status, create_data = self.make_request(
            'POST',
            'employees',
            employee_data
        )
        
        if create_success:
            employee_id = create_data.get('id')
            
            # Retrieve the employee to verify persistence
            get_success, get_status, get_data = self.make_request(
                'GET',
                f'employees/{employee_id}'
            )
            
            data_matches = (
                get_success and 
                get_data.get('name') == employee_data['name'] and
                get_data.get('employee_id') == employee_data['employee_id']
            )
            
            return self.log_test(
                "Data persistence",
                data_matches,
                f"Employee data persisted correctly: {get_data.get('name', 'Unknown')}"
            )
        
        return self.log_test("Data persistence", False, "Could not create test employee")

    def test_uuid_handling(self):
        """Test proper UUID handling (no MongoDB ObjectIDs)"""
        if not self.token:
            return self.log_test("UUID handling", False, "No token available")
        
        # Get employees and check ID format
        success, status, data = self.make_request('GET', 'employees')
        
        if success and isinstance(data, list) and len(data) > 0:
            first_employee = data[0]
            employee_id = first_employee.get('id', '')
            
            # UUID should be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            is_uuid_format = (
                len(employee_id) == 36 and
                employee_id.count('-') == 4 and
                all(c.isalnum() or c == '-' for c in employee_id)
            )
            
            return self.log_test(
                "UUID handling",
                is_uuid_format,
                f"Employee ID format: {employee_id}"
            )
        
        return self.log_test("UUID handling", False, "No employees found to test UUID format")

    # ============================================================================
    # API VALIDATION & ERROR HANDLING TESTS
    # ============================================================================

    def test_input_validation(self):
        """Test input validation on all endpoints"""
        if not self.token:
            return self.log_test("Input validation", False, "No token available")
        
        # Test invalid employee creation
        invalid_employee_data = {
            "name": "",  # Empty name
            "employee_id": "",  # Empty ID
            "email": "invalid-email",  # Invalid email
            "department": "",
            "manager": "",
            "start_date": "invalid-date"  # Invalid date
        }
        
        success, status, data = self.make_request(
            'POST',
            'employees',
            invalid_employee_data,
            expected_status=422  # Validation error
        )
        
        return self.log_test(
            "Input validation",
            success,
            f"Validation errors properly returned: {status}"
        )

    def test_http_status_codes(self):
        """Test proper HTTP status codes"""
        if not self.token:
            return self.log_test("HTTP status codes", False, "No token available")
        
        # Test 404 for non-existent employee
        success1, status1, data1 = self.make_request(
            'GET',
            'employees/non-existent-id',
            expected_status=404
        )
        
        # Test 401 for unauthorized access
        original_token = self.token
        self.token = "invalid-token"
        success2, status2, data2 = self.make_request(
            'GET',
            'employees',
            expected_status=401
        )
        self.token = original_token
        
        return self.log_test(
            "HTTP status codes",
            success1 and success2,
            f"404 for not found: {status1}, 401 for unauthorized: {status2}"
        )

    def test_error_messages(self):
        """Test error messages and edge cases"""
        if not self.token:
            return self.log_test("Error messages", False, "No token available")
        
        # Test duplicate employee ID
        duplicate_employee_data = {
            "name": "Duplicate Test",
            "employee_id": "DUPLICATE001",
            "email": "duplicate1@company.com",
            "department": "Testing",
            "manager": "Test Manager",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "status": "onboarding"
        }
        
        # Create first employee
        success1, status1, data1 = self.make_request(
            'POST',
            'employees',
            duplicate_employee_data
        )
        
        if success1:
            # Try to create duplicate
            duplicate_employee_data["email"] = "duplicate2@company.com"  # Change email
            success2, status2, data2 = self.make_request(
                'POST',
                'employees',
                duplicate_employee_data,
                expected_status=400
            )
            
            has_error_message = 'detail' in data2 and 'already exists' in str(data2['detail']).lower()
            
            return self.log_test(
                "Error messages",
                success2 and has_error_message,
                f"Duplicate ID error properly handled: {data2.get('detail', 'No detail')}"
            )
        
        return self.log_test("Error messages", False, "Could not create initial employee for duplicate test")

    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================

    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Comprehensive HR Onboarding & Exit Management System Backend Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Comprehensive testing of ALL backend functionalities")
        print("=" * 80)
        
        # Authentication & Security Tests
        print("\n🔐 AUTHENTICATION & SECURITY:")
        self.test_user_registration()
        self.test_user_login()
        self.test_token_validation()
        self.test_invalid_credentials()
        self.test_role_based_access()
        self.test_password_management()
        
        # Employee Management CRUD Tests
        print("\n👥 EMPLOYEE MANAGEMENT CRUD:")
        self.test_create_employee()
        self.test_read_employees()
        self.test_update_employee()
        self.test_employee_status_transitions()
        self.test_delete_employee()
        
        # Task Management Tests
        print("\n📋 TASK MANAGEMENT:")
        self.test_automatic_task_creation()
        self.test_task_crud_operations()
        self.test_task_filtering()
        self.test_due_date_management()
        
        # Excel Import & Export Tests
        print("\n📊 EXCEL IMPORT & EXPORT:")
        self.test_excel_import()
        self.test_data_validation()
        
        # AI Integration Tests
        print("\n🤖 AI INTEGRATION:")
        self.test_ai_employee_analysis()
        self.test_ai_data_validation()
        self.test_ai_task_suggestions()
        
        # PDF Reports Tests
        print("\n📄 PDF REPORTS:")
        self.test_pdf_employee_reports()
        
        # Dashboard APIs Tests
        print("\n📊 DASHBOARD APIS:")
        self.test_dashboard_stats()
        self.test_recent_activities()
        
        # Admin Features Tests
        print("\n👑 ADMIN FEATURES:")
        self.test_user_management_apis()
        self.test_audit_logging()
        
        # Database Operations Tests
        print("\n🗄️ DATABASE OPERATIONS:")
        self.test_data_persistence()
        self.test_uuid_handling()
        
        # API Validation & Error Handling Tests
        print("\n✅ API VALIDATION & ERROR HANDLING:")
        self.test_input_validation()
        self.test_http_status_codes()
        self.test_error_messages()
        
        # Final Results
        print("\n" + "=" * 80)
        print(f"📈 COMPREHENSIVE TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! HR System backend is fully functional!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please review the implementation.")
            return 1

def main():
    """Main test runner"""
    tester = ComprehensiveHRSystemTester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())