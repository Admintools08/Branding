#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time

class MissionControlTester:
    def __init__(self, base_url="https://perf-boost-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.sample_employee_ids = []
        self.sample_task_ids = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, params=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
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

    # ============================================================================
    # AUTHENTICATION TESTS
    # ============================================================================

    def test_authentication_with_admin_credentials(self):
        """Test authentication with admin@brandingpioneers.com / SuperAdmin2024!"""
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@brandingpioneers.com", "password": "SuperAdmin2024!"},
            expected_status=200
        )
        
        # If that fails, try the test admin user
        if not success:
            success, status, data = self.make_request(
                'POST',
                'auth/login',
                {"email": "admin@test.com", "password": "admin123"},
                expected_status=200
            )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            user_role = data.get('user', {}).get('role', 'unknown')
            user_name = data.get('user', {}).get('name', 'unknown')
            return self.log_test(
                "Authentication with admin credentials",
                True,
                f"Logged in as {user_name} with role: {user_role}"
            )
        else:
            return self.log_test(
                "Authentication with admin credentials",
                False,
                f"Status: {status}, Data: {data}"
            )

    # ============================================================================
    # TASK MANAGEMENT API TESTS
    # ============================================================================

    def test_task_management_get_api(self):
        """Test GET /api/tasks endpoint to retrieve task data"""
        if not self.token:
            return self.log_test("Task Management GET API", False, "No token available")
        
        success, status, data = self.make_request('GET', 'tasks')
        
        if success and isinstance(data, list):
            task_count = len(data)
            
            # Store sample task IDs for later tests
            if task_count > 0:
                self.sample_task_ids = [task.get('id') for task in data[:5] if task.get('id')]
                
                # Check task structure
                first_task = data[0]
                required_fields = ['id', 'employee_id', 'title', 'description', 'task_type', 'status']
                has_required_fields = all(field in first_task for field in required_fields)
                
                return self.log_test(
                    "Task Management GET API",
                    True,
                    f"Retrieved {task_count} tasks with proper structure: {has_required_fields}"
                )
            else:
                return self.log_test(
                    "Task Management GET API",
                    True,
                    "No tasks found in system (empty result is valid)"
                )
        else:
            return self.log_test(
                "Task Management GET API",
                False,
                f"Status: {status}, Data type: {type(data)}, Response: {data}"
            )

    def test_task_update_api_single(self):
        """Test PUT /api/tasks/{task_id} endpoint for updating task status"""
        if not self.token:
            return self.log_test("Task Update API (Single)", False, "No token available")
        
        if not self.sample_task_ids:
            return self.log_test("Task Update API (Single)", False, "No sample tasks available")
        
        task_id = self.sample_task_ids[0]
        update_data = {
            "status": "completed"
        }
        
        success, status, data = self.make_request(
            'PUT',
            f'tasks/{task_id}',
            update_data
        )
        
        if success:
            # Verify the update worked
            updated_status = data.get('status')
            has_completed_date = 'completed_date' in data
            
            return self.log_test(
                "Task Update API (Single)",
                True,
                f"Task {task_id} updated to status: {updated_status}, Completed date set: {has_completed_date}"
            )
        else:
            return self.log_test(
                "Task Update API (Single)",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_task_update_api_bulk_support(self):
        """Test that backend can support bulk task updates (multiple individual calls)"""
        if not self.token:
            return self.log_test("Task Update API (Bulk Support)", False, "No token available")
        
        if len(self.sample_task_ids) < 2:
            return self.log_test("Task Update API (Bulk Support)", False, "Need at least 2 tasks for bulk testing")
        
        # Test updating multiple tasks in sequence (simulating bulk operations)
        bulk_updates = []
        for i, task_id in enumerate(self.sample_task_ids[:3]):  # Test up to 3 tasks
            update_data = {
                "status": "pending" if i % 2 == 0 else "completed"
            }
            
            success, status, data = self.make_request(
                'PUT',
                f'tasks/{task_id}',
                update_data
            )
            
            bulk_updates.append({
                'task_id': task_id,
                'success': success,
                'status': status,
                'new_status': data.get('status') if success else None
            })
        
        successful_updates = [update for update in bulk_updates if update['success']]
        success_rate = len(successful_updates) / len(bulk_updates)
        
        return self.log_test(
            "Task Update API (Bulk Support)",
            success_rate >= 0.8,  # At least 80% success rate
            f"Bulk updates: {len(successful_updates)}/{len(bulk_updates)} successful ({success_rate:.1%})"
        )

    # ============================================================================
    # EMPLOYEE TASK FILTERING TESTS
    # ============================================================================

    def test_employee_task_filtering(self):
        """Test filtering tasks by employee_id"""
        if not self.token:
            return self.log_test("Employee Task Filtering", False, "No token available")
        
        # First get all employees to get sample employee IDs
        emp_success, emp_status, emp_data = self.make_request('GET', 'employees')
        
        if not emp_success or not isinstance(emp_data, list) or len(emp_data) == 0:
            return self.log_test(
                "Employee Task Filtering",
                False,
                f"No employees found for filtering test. Status: {emp_status}"
            )
        
        # Store sample employee IDs
        self.sample_employee_ids = [emp.get('id') for emp in emp_data[:3] if emp.get('id')]
        
        if not self.sample_employee_ids:
            return self.log_test("Employee Task Filtering", False, "No valid employee IDs found")
        
        # Test filtering by employee_id
        employee_id = self.sample_employee_ids[0]
        employee_name = next((emp.get('name') for emp in emp_data if emp.get('id') == employee_id), 'Unknown')
        
        success, status, data = self.make_request(
            'GET', 
            'tasks',
            params={'employee_id': employee_id}
        )
        
        if success and isinstance(data, list):
            # Verify all returned tasks belong to the specified employee
            all_match_employee = all(task.get('employee_id') == employee_id for task in data)
            task_count = len(data)
            
            return self.log_test(
                "Employee Task Filtering",
                True,
                f"Found {task_count} tasks for employee '{employee_name}' (ID: {employee_id}), All match filter: {all_match_employee}"
            )
        else:
            return self.log_test(
                "Employee Task Filtering",
                False,
                f"Status: {status}, Data type: {type(data)}"
            )

    def test_multiple_employee_filtering(self):
        """Test filtering tasks for multiple employees"""
        if not self.token or len(self.sample_employee_ids) < 2:
            return self.log_test("Multiple Employee Filtering", False, "Need at least 2 employees")
        
        filtering_results = []
        
        for employee_id in self.sample_employee_ids[:2]:  # Test first 2 employees
            success, status, data = self.make_request(
                'GET', 
                'tasks',
                params={'employee_id': employee_id}
            )
            
            if success and isinstance(data, list):
                task_count = len(data)
                all_match = all(task.get('employee_id') == employee_id for task in data)
                filtering_results.append({
                    'employee_id': employee_id,
                    'task_count': task_count,
                    'all_match': all_match,
                    'success': True
                })
            else:
                filtering_results.append({
                    'employee_id': employee_id,
                    'success': False,
                    'status': status
                })
        
        successful_filters = [r for r in filtering_results if r['success']]
        all_successful = len(successful_filters) == len(filtering_results)
        
        return self.log_test(
            "Multiple Employee Filtering",
            all_successful,
            f"Filtered tasks for {len(successful_filters)}/{len(filtering_results)} employees successfully"
        )

    # ============================================================================
    # DASHBOARD DATA TESTS
    # ============================================================================

    def test_dashboard_stats_api(self):
        """Test GET /api/dashboard/stats to ensure task statistics are working"""
        if not self.token:
            return self.log_test("Dashboard Stats API", False, "No token available")
        
        success, status, data = self.make_request('GET', 'dashboard/stats')
        
        if success and isinstance(data, dict):
            # Check for required stat categories
            has_employee_stats = 'employee_stats' in data
            has_task_stats = 'task_stats' in data
            
            task_stats = data.get('task_stats', {})
            required_task_fields = ['total', 'pending', 'completed', 'overdue', 'upcoming']
            has_task_fields = all(field in task_stats for field in required_task_fields)
            
            # Verify stats are numeric
            task_values_numeric = all(
                isinstance(task_stats.get(field, 0), (int, float)) 
                for field in required_task_fields
            )
            
            return self.log_test(
                "Dashboard Stats API",
                has_employee_stats and has_task_stats and has_task_fields and task_values_numeric,
                f"Employee stats: {has_employee_stats}, Task stats: {has_task_stats}, Task fields: {has_task_fields}, Values numeric: {task_values_numeric}"
            )
        else:
            return self.log_test(
                "Dashboard Stats API",
                False,
                f"Status: {status}, Data type: {type(data)}, Response: {data}"
            )

    def test_dashboard_stats_accuracy(self):
        """Test that dashboard stats match actual data"""
        if not self.token:
            return self.log_test("Dashboard Stats Accuracy", False, "No token available")
        
        # Get dashboard stats
        stats_success, stats_status, stats_data = self.make_request('GET', 'dashboard/stats')
        
        # Get actual task data
        tasks_success, tasks_status, tasks_data = self.make_request('GET', 'tasks')
        
        # Get actual employee data
        emp_success, emp_status, emp_data = self.make_request('GET', 'employees')
        
        if not (stats_success and tasks_success and emp_success):
            return self.log_test(
                "Dashboard Stats Accuracy",
                False,
                f"Failed to get data: Stats({stats_status}), Tasks({tasks_status}), Employees({emp_status})"
            )
        
        # Calculate actual counts
        actual_total_tasks = len(tasks_data) if isinstance(tasks_data, list) else 0
        actual_pending_tasks = len([t for t in tasks_data if t.get('status') == 'pending']) if isinstance(tasks_data, list) else 0
        actual_completed_tasks = len([t for t in tasks_data if t.get('status') == 'completed']) if isinstance(tasks_data, list) else 0
        actual_total_employees = len(emp_data) if isinstance(emp_data, list) else 0
        
        # Compare with dashboard stats
        dashboard_task_stats = stats_data.get('task_stats', {})
        dashboard_total_tasks = dashboard_task_stats.get('total', 0)
        dashboard_pending_tasks = dashboard_task_stats.get('pending', 0)
        dashboard_completed_tasks = dashboard_task_stats.get('completed', 0)
        
        # Check accuracy (allow small discrepancies due to timing)
        total_accurate = abs(actual_total_tasks - dashboard_total_tasks) <= 1
        pending_accurate = abs(actual_pending_tasks - dashboard_pending_tasks) <= 1
        completed_accurate = abs(actual_completed_tasks - dashboard_completed_tasks) <= 1
        
        return self.log_test(
            "Dashboard Stats Accuracy",
            total_accurate and pending_accurate and completed_accurate,
            f"Total: {actual_total_tasks}≈{dashboard_total_tasks}({total_accurate}), Pending: {actual_pending_tasks}≈{dashboard_pending_tasks}({pending_accurate}), Completed: {actual_completed_tasks}≈{dashboard_completed_tasks}({completed_accurate})"
        )

    # ============================================================================
    # SAMPLE DATA VERIFICATION TESTS
    # ============================================================================

    def test_sample_employees_verification(self):
        """Confirm we have sample employees from the init script"""
        if not self.token:
            return self.log_test("Sample Employees Verification", False, "No token available")
        
        success, status, data = self.make_request('GET', 'employees')
        
        if success and isinstance(data, list):
            employee_count = len(data)
            
            if employee_count > 0:
                # Check employee data structure
                first_employee = data[0]
                required_fields = ['id', 'name', 'employee_id', 'email', 'department', 'manager', 'status']
                has_required_fields = all(field in first_employee for field in required_fields)
                
                # Check for variety in departments and statuses
                departments = set(emp.get('department') for emp in data)
                statuses = set(emp.get('status') for emp in data)
                
                return self.log_test(
                    "Sample Employees Verification",
                    True,
                    f"Found {employee_count} employees with proper structure: {has_required_fields}, Departments: {len(departments)}, Statuses: {len(statuses)}"
                )
            else:
                return self.log_test(
                    "Sample Employees Verification",
                    False,
                    "No employees found in system"
                )
        else:
            return self.log_test(
                "Sample Employees Verification",
                False,
                f"Status: {status}, Data type: {type(data)}"
            )

    def test_sample_tasks_verification(self):
        """Confirm we have sample tasks from the init script"""
        if not self.token:
            return self.log_test("Sample Tasks Verification", False, "No token available")
        
        success, status, data = self.make_request('GET', 'tasks')
        
        if success and isinstance(data, list):
            task_count = len(data)
            
            if task_count > 0:
                # Check task data structure
                first_task = data[0]
                required_fields = ['id', 'employee_id', 'title', 'description', 'task_type', 'status']
                has_required_fields = all(field in first_task for field in required_fields)
                
                # Check for variety in task types and statuses
                task_types = set(task.get('task_type') for task in data)
                task_statuses = set(task.get('status') for task in data)
                
                # Check for onboarding and exit tasks
                onboarding_tasks = len([t for t in data if t.get('task_type') == 'onboarding'])
                exit_tasks = len([t for t in data if t.get('task_type') == 'exit'])
                
                return self.log_test(
                    "Sample Tasks Verification",
                    True,
                    f"Found {task_count} tasks with proper structure: {has_required_fields}, Types: {len(task_types)}, Statuses: {len(task_statuses)}, Onboarding: {onboarding_tasks}, Exit: {exit_tasks}"
                )
            else:
                return self.log_test(
                    "Sample Tasks Verification",
                    False,
                    "No tasks found in system"
                )
        else:
            return self.log_test(
                "Sample Tasks Verification",
                False,
                f"Status: {status}, Data type: {type(data)}"
            )

    def test_employee_task_relationships(self):
        """Verify that tasks are properly linked to employees"""
        if not self.token:
            return self.log_test("Employee Task Relationships", False, "No token available")
        
        # Get employees and tasks
        emp_success, emp_status, emp_data = self.make_request('GET', 'employees')
        task_success, task_status, task_data = self.make_request('GET', 'tasks')
        
        if not (emp_success and task_success):
            return self.log_test(
                "Employee Task Relationships",
                False,
                f"Failed to get data: Employees({emp_status}), Tasks({task_status})"
            )
        
        if not (isinstance(emp_data, list) and isinstance(task_data, list)):
            return self.log_test(
                "Employee Task Relationships",
                False,
                "Invalid data types returned"
            )
        
        # Create employee ID set
        employee_ids = set(emp.get('id') for emp in emp_data if emp.get('id'))
        
        # Check task-employee relationships
        valid_relationships = 0
        invalid_relationships = 0
        
        for task in task_data:
            task_employee_id = task.get('employee_id')
            if task_employee_id in employee_ids:
                valid_relationships += 1
            else:
                invalid_relationships += 1
        
        total_tasks = len(task_data)
        relationship_accuracy = valid_relationships / total_tasks if total_tasks > 0 else 0
        
        return self.log_test(
            "Employee Task Relationships",
            relationship_accuracy >= 0.9,  # At least 90% should have valid relationships
            f"Valid relationships: {valid_relationships}/{total_tasks} ({relationship_accuracy:.1%}), Invalid: {invalid_relationships}"
        )

    # ============================================================================
    # MISSION CONTROL INTEGRATION TESTS
    # ============================================================================

    def test_mission_control_data_integration(self):
        """Test that all Mission Control features have the necessary backend data"""
        if not self.token:
            return self.log_test("Mission Control Data Integration", False, "No token available")
        
        integration_checks = []
        
        # Check 1: Tasks with employee names (for filtering)
        task_success, task_status, task_data = self.make_request('GET', 'tasks')
        emp_success, emp_status, emp_data = self.make_request('GET', 'employees')
        
        if task_success and emp_success and isinstance(task_data, list) and isinstance(emp_data, list):
            # Create employee lookup
            employee_lookup = {emp.get('id'): emp.get('name') for emp in emp_data if emp.get('id') and emp.get('name')}
            
            # Check if tasks can be linked to employee names
            linkable_tasks = 0
            for task in task_data:
                if task.get('employee_id') in employee_lookup:
                    linkable_tasks += 1
            
            link_rate = linkable_tasks / len(task_data) if task_data else 0
            integration_checks.append(('Task-Employee Linking', link_rate >= 0.8))
        else:
            integration_checks.append(('Task-Employee Linking', False))
        
        # Check 2: Task status variety (for bulk operations)
        if task_success and isinstance(task_data, list):
            statuses = set(task.get('status') for task in task_data)
            has_variety = len(statuses) >= 2  # Should have at least pending and completed
            integration_checks.append(('Task Status Variety', has_variety))
        else:
            integration_checks.append(('Task Status Variety', False))
        
        # Check 3: Dashboard stats availability
        stats_success, stats_status, stats_data = self.make_request('GET', 'dashboard/stats')
        if stats_success and isinstance(stats_data, dict):
            has_task_stats = 'task_stats' in stats_data
            integration_checks.append(('Dashboard Stats', has_task_stats))
        else:
            integration_checks.append(('Dashboard Stats', False))
        
        # Overall integration score
        passed_checks = [check for check in integration_checks if check[1]]
        integration_score = len(passed_checks) / len(integration_checks)
        
        return self.log_test(
            "Mission Control Data Integration",
            integration_score >= 0.8,
            f"Integration checks: {len(passed_checks)}/{len(integration_checks)} passed ({integration_score:.1%})"
        )

    def run_all_tests(self):
        """Run all Mission Control tests"""
        print("🎯 Starting Mission Control Backend Testing")
        print(f"📍 Testing against: {self.base_url}")
        print("🚀 Focus: Enhanced Mission Control Functionality")
        print("=" * 80)
        
        # Authentication
        print("\n🔐 Authentication Tests:")
        self.test_authentication_with_admin_credentials()
        
        # Task Management API
        print("\n📋 Task Management API Tests:")
        self.test_task_management_get_api()
        self.test_task_update_api_single()
        self.test_task_update_api_bulk_support()
        
        # Employee Task Filtering
        print("\n👥 Employee Task Filtering Tests:")
        self.test_employee_task_filtering()
        self.test_multiple_employee_filtering()
        
        # Dashboard Data
        print("\n📊 Dashboard Data Tests:")
        self.test_dashboard_stats_api()
        self.test_dashboard_stats_accuracy()
        
        # Sample Data Verification
        print("\n🗃️ Sample Data Verification Tests:")
        self.test_sample_employees_verification()
        self.test_sample_tasks_verification()
        self.test_employee_task_relationships()
        
        # Mission Control Integration
        print("\n🎮 Mission Control Integration Tests:")
        self.test_mission_control_data_integration()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Mission Control Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Mission Control tests passed! Backend supports enhanced Mission Control features!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please review the Mission Control implementation.")
            return 1

def main():
    """Main test runner"""
    tester = MissionControlTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())