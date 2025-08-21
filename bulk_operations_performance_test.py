#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import time
import concurrent.futures
import threading
from typing import List, Dict, Any

class BulkOperationsPerformanceTester:
    def __init__(self, base_url="https://perf-boost-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_task_ids = []
        self.created_employee_ids = []
        self.performance_metrics = {}

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, timeout=30):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            
            response_time = time.time() - start_time
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data, response_time
            
        except Exception as e:
            response_time = time.time() - start_time
            return False, 0, {"error": str(e)}, response_time

    def authenticate(self):
        """Authenticate with admin credentials"""
        # Try different admin credentials based on test_result.md
        credentials = [
            {"email": "admin@brandingpioneers.com", "password": "SuperAdmin2024!"},
            {"email": "admin@test.com", "password": "admin123"}
        ]
        
        for cred in credentials:
            success, status, data, _ = self.make_request(
                'POST',
                'auth/login',
                cred,
                expected_status=200
            )
            
            if success and 'access_token' in data:
                self.token = data['access_token']
                return self.log_test(
                    "Authentication",
                    True,
                    f"Logged in as {cred['email']}"
                )
        
        return self.log_test("Authentication", False, "Failed to authenticate with any credentials")

    def create_test_employees(self, count=5):
        """Create test employees for task creation"""
        if not self.token:
            return False
        
        created_count = 0
        for i in range(count):
            employee_data = {
                "name": f"Bulk Test Employee {i+1}",
                "employee_id": f"BULK{int(time.time())}{i:03d}",
                "email": f"bulktest{i+1}.{int(time.time())}@test.com",
                "department": "Testing",
                "manager": "Test Manager",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "status": "onboarding"
            }
            
            success, status, data, _ = self.make_request(
                'POST',
                'employees',
                employee_data,
                expected_status=200
            )
            
            if success and 'id' in data:
                self.created_employee_ids.append(data['id'])
                created_count += 1
        
        return self.log_test(
            "Create test employees",
            created_count == count,
            f"Created {created_count}/{count} test employees"
        )

    def create_test_tasks(self, count=200):
        """Create test tasks for bulk operations"""
        if not self.token or not self.created_employee_ids:
            return False
        
        created_count = 0
        employee_count = len(self.created_employee_ids)
        
        for i in range(count):
            employee_id = self.created_employee_ids[i % employee_count]
            task_data = {
                "employee_id": employee_id,
                "title": f"Bulk Test Task {i+1}",
                "description": f"This is bulk test task number {i+1} for performance testing",
                "task_type": "onboarding",
                "due_date": datetime.now(timezone.utc).isoformat()
            }
            
            success, status, data, _ = self.make_request(
                'POST',
                'tasks',
                task_data,
                expected_status=200
            )
            
            if success and 'id' in data:
                self.created_task_ids.append(data['id'])
                created_count += 1
        
        return self.log_test(
            "Create test tasks",
            created_count >= count * 0.9,  # Allow 10% failure rate
            f"Created {created_count}/{count} test tasks"
        )

    # ============================================================================
    # BULK ENDPOINT TESTING
    # ============================================================================

    def test_bulk_endpoint_small_dataset(self):
        """Test bulk update with small dataset (5-10 tasks)"""
        if not self.created_task_ids:
            return self.log_test("Bulk endpoint small dataset", False, "No test tasks available")
        
        # Use first 10 tasks or all if less than 10
        task_subset = self.created_task_ids[:min(10, len(self.created_task_ids))]
        
        bulk_data = {
            "task_ids": task_subset,
            "status": "completed"
        }
        
        start_time = time.time()
        success, status, data, response_time = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            expected_count = len(task_subset)
            success_rate = updated_count / expected_count if expected_count > 0 else 0
            
            self.performance_metrics['small_dataset'] = {
                'task_count': len(task_subset),
                'response_time': response_time,
                'updated_count': updated_count,
                'success_rate': success_rate
            }
            
            return self.log_test(
                "Bulk endpoint small dataset",
                success and success_rate >= 0.9,
                f"Updated {updated_count}/{expected_count} tasks in {response_time:.3f}s"
            )
        else:
            return self.log_test(
                "Bulk endpoint small dataset",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_bulk_endpoint_medium_dataset(self):
        """Test bulk update with medium dataset (50-100 tasks)"""
        if len(self.created_task_ids) < 50:
            return self.log_test("Bulk endpoint medium dataset", False, "Not enough test tasks (need 50+)")
        
        # Use 50-100 tasks
        task_subset = self.created_task_ids[:min(100, len(self.created_task_ids))]
        
        bulk_data = {
            "task_ids": task_subset,
            "status": "pending"  # Change back to pending
        }
        
        start_time = time.time()
        success, status, data, response_time = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200,
            timeout=60  # Longer timeout for medium dataset
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            expected_count = len(task_subset)
            success_rate = updated_count / expected_count if expected_count > 0 else 0
            
            self.performance_metrics['medium_dataset'] = {
                'task_count': len(task_subset),
                'response_time': response_time,
                'updated_count': updated_count,
                'success_rate': success_rate
            }
            
            return self.log_test(
                "Bulk endpoint medium dataset",
                success and success_rate >= 0.9,
                f"Updated {updated_count}/{expected_count} tasks in {response_time:.3f}s"
            )
        else:
            return self.log_test(
                "Bulk endpoint medium dataset",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_bulk_endpoint_large_dataset(self):
        """Test bulk update with large dataset (200+ tasks)"""
        if len(self.created_task_ids) < 200:
            return self.log_test("Bulk endpoint large dataset", False, "Not enough test tasks (need 200+)")
        
        # Use all available tasks
        task_subset = self.created_task_ids
        
        bulk_data = {
            "task_ids": task_subset,
            "status": "completed"
        }
        
        start_time = time.time()
        success, status, data, response_time = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200,
            timeout=120  # Longer timeout for large dataset
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            expected_count = len(task_subset)
            success_rate = updated_count / expected_count if expected_count > 0 else 0
            
            self.performance_metrics['large_dataset'] = {
                'task_count': len(task_subset),
                'response_time': response_time,
                'updated_count': updated_count,
                'success_rate': success_rate
            }
            
            # Performance should be reasonable even for large datasets
            performance_acceptable = response_time < 30.0  # Should complete within 30 seconds
            
            return self.log_test(
                "Bulk endpoint large dataset",
                success and success_rate >= 0.9 and performance_acceptable,
                f"Updated {updated_count}/{expected_count} tasks in {response_time:.3f}s (Performance: {'Good' if performance_acceptable else 'Poor'})"
            )
        else:
            return self.log_test(
                "Bulk endpoint large dataset",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_bulk_vs_individual_performance(self):
        """Compare bulk update performance vs individual updates"""
        if len(self.created_task_ids) < 20:
            return self.log_test("Bulk vs individual performance", False, "Not enough test tasks")
        
        # Test with 20 tasks for comparison
        test_tasks = self.created_task_ids[:20]
        
        # Test individual updates
        individual_start = time.time()
        individual_success_count = 0
        
        for task_id in test_tasks:
            success, status, data, _ = self.make_request(
                'PUT',
                f'tasks/{task_id}',
                {"status": "pending"},
                expected_status=200
            )
            if success:
                individual_success_count += 1
        
        individual_time = time.time() - individual_start
        
        # Test bulk update
        bulk_data = {
            "task_ids": test_tasks,
            "status": "completed"
        }
        
        bulk_start = time.time()
        bulk_success, bulk_status, bulk_data_response, bulk_time = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if bulk_success:
            bulk_updated_count = bulk_data_response.get('updated_count', 0)
            
            # Calculate performance improvement
            performance_improvement = (individual_time - bulk_time) / individual_time * 100 if individual_time > 0 else 0
            
            self.performance_metrics['comparison'] = {
                'task_count': len(test_tasks),
                'individual_time': individual_time,
                'individual_success': individual_success_count,
                'bulk_time': bulk_time,
                'bulk_success': bulk_updated_count,
                'performance_improvement': performance_improvement
            }
            
            # Bulk should be significantly faster
            bulk_faster = bulk_time < individual_time * 0.5  # At least 50% faster
            
            return self.log_test(
                "Bulk vs individual performance",
                bulk_faster and bulk_updated_count >= len(test_tasks) * 0.9,
                f"Individual: {individual_time:.3f}s ({individual_success_count} tasks), Bulk: {bulk_time:.3f}s ({bulk_updated_count} tasks), Improvement: {performance_improvement:.1f}%"
            )
        else:
            return self.log_test(
                "Bulk vs individual performance",
                False,
                f"Bulk operation failed: {bulk_status}"
            )

    def test_concurrent_bulk_operations(self):
        """Test concurrent bulk operations"""
        if len(self.created_task_ids) < 60:
            return self.log_test("Concurrent bulk operations", False, "Not enough test tasks (need 60+)")
        
        # Split tasks into 3 groups for concurrent operations
        task_groups = [
            self.created_task_ids[0:20],
            self.created_task_ids[20:40],
            self.created_task_ids[40:60]
        ]
        
        def bulk_update_group(task_group, status):
            bulk_data = {
                "task_ids": task_group,
                "status": status
            }
            return self.make_request('PUT', 'tasks/bulk', bulk_data, expected_status=200)
        
        # Execute concurrent bulk operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(bulk_update_group, task_groups[0], "pending"),
                executor.submit(bulk_update_group, task_groups[1], "completed"),
                executor.submit(bulk_update_group, task_groups[2], "pending")
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Check results
        successful_operations = sum(1 for success, status, data, _ in results if success)
        total_updated = sum(data.get('updated_count', 0) for success, status, data, _ in results if success)
        
        self.performance_metrics['concurrent'] = {
            'operations': len(task_groups),
            'total_time': total_time,
            'successful_operations': successful_operations,
            'total_updated': total_updated
        }
        
        return self.log_test(
            "Concurrent bulk operations",
            successful_operations >= 2,  # At least 2 out of 3 should succeed
            f"{successful_operations}/3 operations succeeded, {total_updated} tasks updated in {total_time:.3f}s"
        )

    # ============================================================================
    # BULK FUNCTIONALITY TESTING
    # ============================================================================

    def test_bulk_mark_completed_with_dates(self):
        """Test bulk marking tasks as completed sets completed_date correctly"""
        if len(self.created_task_ids) < 10:
            return self.log_test("Bulk mark completed with dates", False, "Not enough test tasks")
        
        test_tasks = self.created_task_ids[:10]
        
        # Mark tasks as completed via bulk
        bulk_data = {
            "task_ids": test_tasks,
            "status": "completed"
        }
        
        before_time = datetime.now(timezone.utc)
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        after_time = datetime.now(timezone.utc)
        
        if not success:
            return self.log_test(
                "Bulk mark completed with dates",
                False,
                f"Bulk operation failed: {status}"
            )
        
        # Verify completed_date is set for updated tasks
        completed_dates_set = 0
        for task_id in test_tasks:
            task_success, task_status, task_data, _ = self.make_request(
                'GET',
                f'tasks/{task_id}',
                expected_status=200
            )
            
            if task_success and task_data.get('status') == 'completed':
                completed_date_str = task_data.get('completed_date')
                if completed_date_str:
                    try:
                        completed_date = datetime.fromisoformat(completed_date_str.replace('Z', '+00:00'))
                        if before_time <= completed_date <= after_time:
                            completed_dates_set += 1
                    except:
                        pass
        
        return self.log_test(
            "Bulk mark completed with dates",
            completed_dates_set >= len(test_tasks) * 0.8,  # At least 80% should have correct dates
            f"{completed_dates_set}/{len(test_tasks)} tasks have correct completed_date"
        )

    def test_bulk_mark_pending(self):
        """Test bulk marking tasks as pending"""
        if len(self.created_task_ids) < 10:
            return self.log_test("Bulk mark pending", False, "Not enough test tasks")
        
        test_tasks = self.created_task_ids[:10]
        
        # Mark tasks as pending via bulk
        bulk_data = {
            "task_ids": test_tasks,
            "status": "pending"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Bulk mark pending",
                False,
                f"Bulk operation failed: {status}"
            )
        
        # Verify tasks are marked as pending
        pending_count = 0
        for task_id in test_tasks:
            task_success, task_status, task_data, _ = self.make_request(
                'GET',
                f'tasks/{task_id}',
                expected_status=200
            )
            
            if task_success and task_data.get('status') == 'pending':
                pending_count += 1
        
        return self.log_test(
            "Bulk mark pending",
            pending_count >= len(test_tasks) * 0.8,
            f"{pending_count}/{len(test_tasks)} tasks marked as pending"
        )

    def test_bulk_audit_logging(self):
        """Test that bulk operations are properly logged"""
        if not self.token or len(self.created_task_ids) < 5:
            return self.log_test("Bulk audit logging", False, "No token or insufficient test tasks")
        
        # Get initial audit log count
        initial_success, initial_status, initial_logs, _ = self.make_request(
            'GET',
            'admin/audit-logs?limit=10',
            expected_status=200
        )
        
        initial_count = len(initial_logs) if initial_success else 0
        
        # Perform bulk operation
        test_tasks = self.created_task_ids[:5]
        bulk_data = {
            "task_ids": test_tasks,
            "status": "completed"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if not success:
            return self.log_test(
                "Bulk audit logging",
                False,
                f"Bulk operation failed: {status}"
            )
        
        # Wait for logging to complete
        time.sleep(2)
        
        # Get updated audit logs
        final_success, final_status, final_logs, _ = self.make_request(
            'GET',
            'admin/audit-logs?limit=10',
            expected_status=200
        )
        
        if not final_success:
            return self.log_test(
                "Bulk audit logging",
                False,
                f"Failed to retrieve audit logs: {final_status}"
            )
        
        # Check for bulk operation log entry
        bulk_log_found = False
        if final_logs:
            for log in final_logs:
                if (log.get('action') == 'bulk_update_tasks' and 
                    log.get('resource') == 'tasks'):
                    bulk_log_found = True
                    break
        
        return self.log_test(
            "Bulk audit logging",
            bulk_log_found,
            f"Bulk operation audit log found: {bulk_log_found}"
        )

    # ============================================================================
    # ERROR SCENARIOS TESTING
    # ============================================================================

    def test_bulk_with_invalid_task_ids(self):
        """Test bulk operation with invalid task IDs"""
        invalid_ids = ["invalid-id-1", "invalid-id-2", "nonexistent-uuid"]
        
        bulk_data = {
            "task_ids": invalid_ids,
            "status": "completed"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200  # Should still return 200 but with 0 updated
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            return self.log_test(
                "Bulk with invalid task IDs",
                updated_count == 0,
                f"Correctly handled invalid IDs: {updated_count} tasks updated"
            )
        else:
            return self.log_test(
                "Bulk with invalid task IDs",
                False,
                f"Unexpected response: {status}, {data}"
            )

    def test_bulk_with_empty_task_ids(self):
        """Test bulk operation with empty task_ids array"""
        bulk_data = {
            "task_ids": [],
            "status": "completed"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=400  # Should return bad request
        )
        
        return self.log_test(
            "Bulk with empty task IDs",
            success,
            f"Correctly rejected empty task_ids array with status {status}"
        )

    def test_bulk_with_mixed_valid_invalid_ids(self):
        """Test bulk operation with mix of valid and invalid task IDs"""
        if len(self.created_task_ids) < 3:
            return self.log_test("Bulk with mixed valid/invalid IDs", False, "Not enough test tasks")
        
        # Mix valid and invalid IDs
        mixed_ids = self.created_task_ids[:3] + ["invalid-id-1", "nonexistent-uuid"]
        
        bulk_data = {
            "task_ids": mixed_ids,
            "status": "completed"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            # Should update only the valid tasks
            expected_valid = 3
            return self.log_test(
                "Bulk with mixed valid/invalid IDs",
                updated_count == expected_valid,
                f"Updated {updated_count}/{expected_valid} valid tasks, ignored invalid IDs"
            )
        else:
            return self.log_test(
                "Bulk with mixed valid/invalid IDs",
                False,
                f"Operation failed: {status}, {data}"
            )

    def test_bulk_with_invalid_status(self):
        """Test bulk operation with invalid status value"""
        if len(self.created_task_ids) < 3:
            return self.log_test("Bulk with invalid status", False, "Not enough test tasks")
        
        bulk_data = {
            "task_ids": self.created_task_ids[:3],
            "status": "invalid_status"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=422  # Should return validation error
        )
        
        return self.log_test(
            "Bulk with invalid status",
            success,
            f"Correctly rejected invalid status with status {status}"
        )

    # ============================================================================
    # DATA INTEGRITY TESTING
    # ============================================================================

    def test_bulk_operations_atomicity(self):
        """Test that bulk operations are atomic (all succeed or fail together)"""
        # This test is conceptual since MongoDB update_many is atomic by design
        # We'll test that partial failures don't leave the system in inconsistent state
        
        if len(self.created_task_ids) < 10:
            return self.log_test("Bulk operations atomicity", False, "Not enough test tasks")
        
        test_tasks = self.created_task_ids[:10]
        
        # Record initial states
        initial_states = {}
        for task_id in test_tasks:
            success, status, data, _ = self.make_request('GET', f'tasks/{task_id}')
            if success:
                initial_states[task_id] = data.get('status')
        
        # Perform bulk operation
        bulk_data = {
            "task_ids": test_tasks,
            "status": "completed"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        
        if success:
            updated_count = data.get('updated_count', 0)
            
            # Verify final states
            completed_count = 0
            for task_id in test_tasks:
                task_success, task_status, task_data, _ = self.make_request('GET', f'tasks/{task_id}')
                if task_success and task_data.get('status') == 'completed':
                    completed_count += 1
            
            # All tasks should be updated consistently
            consistent_update = completed_count == updated_count
            
            return self.log_test(
                "Bulk operations atomicity",
                consistent_update,
                f"Atomic update: {updated_count} reported, {completed_count} verified"
            )
        else:
            return self.log_test(
                "Bulk operations atomicity",
                False,
                f"Bulk operation failed: {status}"
            )

    def test_bulk_updated_at_timestamps(self):
        """Test that updated_at timestamps are set correctly for bulk operations"""
        if len(self.created_task_ids) < 5:
            return self.log_test("Bulk updated_at timestamps", False, "Not enough test tasks")
        
        test_tasks = self.created_task_ids[:5]
        
        # Perform bulk operation
        before_time = datetime.now(timezone.utc)
        bulk_data = {
            "task_ids": test_tasks,
            "status": "pending"
        }
        
        success, status, data, _ = self.make_request(
            'PUT',
            'tasks/bulk',
            bulk_data,
            expected_status=200
        )
        after_time = datetime.now(timezone.utc)
        
        if not success:
            return self.log_test(
                "Bulk updated_at timestamps",
                False,
                f"Bulk operation failed: {status}"
            )
        
        # Verify updated_at timestamps
        correct_timestamps = 0
        for task_id in test_tasks:
            task_success, task_status, task_data, _ = self.make_request('GET', f'tasks/{task_id}')
            
            if task_success:
                updated_at_str = task_data.get('updated_at')
                if updated_at_str:
                    try:
                        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        if before_time <= updated_at <= after_time:
                            correct_timestamps += 1
                    except:
                        pass
        
        return self.log_test(
            "Bulk updated_at timestamps",
            correct_timestamps >= len(test_tasks) * 0.8,
            f"{correct_timestamps}/{len(test_tasks)} tasks have correct updated_at timestamps"
        )

    # ============================================================================
    # CLEANUP AND REPORTING
    # ============================================================================

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        if not self.token:
            return self.log_test("Cleanup test data", True, "No cleanup needed - no token")
        
        cleanup_success = True
        
        # Delete test employees (this will also delete associated tasks)
        for employee_id in self.created_employee_ids:
            success, status, data, _ = self.make_request(
                'DELETE',
                f'employees/{employee_id}',
                expected_status=200
            )
            if not success:
                cleanup_success = False
        
        return self.log_test(
            "Cleanup test data",
            cleanup_success,
            f"Cleaned up {len(self.created_employee_ids)} employees and their tasks"
        )

    def generate_performance_report(self):
        """Generate performance analysis report"""
        print("\n" + "="*80)
        print("📊 BULK OPERATIONS PERFORMANCE ANALYSIS REPORT")
        print("="*80)
        
        if not self.performance_metrics:
            print("❌ No performance metrics collected")
            return
        
        print("\n🚀 Performance Metrics Summary:")
        
        for test_name, metrics in self.performance_metrics.items():
            print(f"\n📈 {test_name.replace('_', ' ').title()}:")
            
            if 'task_count' in metrics:
                print(f"   • Task Count: {metrics['task_count']}")
            if 'response_time' in metrics:
                print(f"   • Response Time: {metrics['response_time']:.3f}s")
            if 'updated_count' in metrics:
                print(f"   • Updated Count: {metrics['updated_count']}")
            if 'success_rate' in metrics:
                print(f"   • Success Rate: {metrics['success_rate']:.1%}")
            if 'performance_improvement' in metrics:
                print(f"   • Performance Improvement: {metrics['performance_improvement']:.1f}%")
        
        # Performance analysis
        print("\n🎯 Performance Analysis:")
        
        if 'comparison' in self.performance_metrics:
            comp = self.performance_metrics['comparison']
            if comp['performance_improvement'] > 50:
                print("   ✅ Bulk operations show significant performance improvement (>50%)")
            elif comp['performance_improvement'] > 20:
                print("   ⚠️  Bulk operations show moderate performance improvement (20-50%)")
            else:
                print("   ❌ Bulk operations show minimal performance improvement (<20%)")
        
        if 'large_dataset' in self.performance_metrics:
            large = self.performance_metrics['large_dataset']
            if large['response_time'] < 10:
                print("   ✅ Large dataset operations complete quickly (<10s)")
            elif large['response_time'] < 30:
                print("   ⚠️  Large dataset operations have acceptable performance (10-30s)")
            else:
                print("   ❌ Large dataset operations are slow (>30s)")
        
        print("\n🏆 Overall Assessment:")
        if self.tests_passed / self.tests_run >= 0.9:
            print("   ✅ Bulk operations performance is EXCELLENT")
        elif self.tests_passed / self.tests_run >= 0.7:
            print("   ⚠️  Bulk operations performance is GOOD with some issues")
        else:
            print("   ❌ Bulk operations performance needs IMPROVEMENT")

    def run_all_tests(self):
        """Run all bulk operations performance tests"""
        print("🚀 Starting Bulk Operations Performance Testing")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Bulk Task Update Optimizations and Performance")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return 1
        
        # Setup test data
        print("\n🔧 Setting up test data:")
        if not self.create_test_employees(5):
            print("❌ Failed to create test employees - cannot proceed")
            return 1
        
        if not self.create_test_tasks(200):
            print("❌ Failed to create sufficient test tasks - some tests may be skipped")
        
        # Bulk Endpoint Testing
        print("\n🎯 New Bulk Endpoint Testing:")
        self.test_bulk_endpoint_small_dataset()
        self.test_bulk_endpoint_medium_dataset()
        self.test_bulk_endpoint_large_dataset()
        
        # Performance Comparison
        print("\n⚡ Performance Comparison Testing:")
        self.test_bulk_vs_individual_performance()
        self.test_concurrent_bulk_operations()
        
        # Bulk Functionality Testing
        print("\n🔧 Bulk Endpoint Functionality Testing:")
        self.test_bulk_mark_completed_with_dates()
        self.test_bulk_mark_pending()
        self.test_bulk_audit_logging()
        
        # Error Scenarios Testing
        print("\n🚨 Error Scenarios Testing:")
        self.test_bulk_with_invalid_task_ids()
        self.test_bulk_with_empty_task_ids()
        self.test_bulk_with_mixed_valid_invalid_ids()
        self.test_bulk_with_invalid_status()
        
        # Data Integrity Testing
        print("\n🔒 Data Integrity Testing:")
        self.test_bulk_operations_atomicity()
        self.test_bulk_updated_at_timestamps()
        
        # Cleanup
        print("\n🧹 Cleanup:")
        self.cleanup_test_data()
        
        # Generate performance report
        self.generate_performance_report()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Bulk Operations Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All bulk operations tests passed! Performance optimizations are working correctly!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Please review the bulk operations implementation.")
            return 1

def main():
    """Main test runner"""
    tester = BulkOperationsPerformanceTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())