#!/usr/bin/env python3

import requests
import sys
import json
import tempfile
import os
import pandas as pd
from datetime import datetime, timezone
import time
import io

class ExcelImportTester:
    def __init__(self, base_url="https://perf-boost-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

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
                # Remove Content-Type for file uploads
                headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def login_admin(self):
        """Login with admin credentials"""
        # Try admin@brandingpioneers.com first (from init_admin.py)
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@brandingpioneers.com", "password": "SuperAdmin2024!"},
            expected_status=200
        )
        
        # If that fails, try admin@test.com (from test_result.md)
        if not success:
            success, status, data = self.make_request(
                'POST',
                'auth/login',
                {"email": "admin@test.com", "password": "admin123"},
                expected_status=200
            )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            return self.log_test(
                "Admin Login",
                True,
                f"Logged in as {data.get('user', {}).get('name', 'Admin')}"
            )
        else:
            return self.log_test(
                "Admin Login",
                False,
                f"Status: {status}, Data: {data}"
            )

    def create_test_excel_file(self, filename, data_rows):
        """Create a test Excel file with employee data"""
        df = pd.DataFrame(data_rows)
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix=filename, delete=False)
        
        if filename.endswith('.xlsx'):
            df.to_excel(temp_file.name, index=False, engine='openpyxl')
        elif filename.endswith('.csv'):
            df.to_csv(temp_file.name, index=False)
        
        return temp_file.name

    def create_test_csv_file(self, filename, data_rows):
        """Create a test CSV file with employee data"""
        df = pd.DataFrame(data_rows)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=filename, delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        return temp_file.name

    def test_excel_import_valid_file(self):
        """Test importing a valid Excel file with proper employee data"""
        if not self.token:
            return self.log_test("Excel Import - Valid File", False, "No token available")

        # Create test data with proper column headers
        test_data = [
            {
                'Name': 'John Excel Smith',
                'Employee ID': f'EXL{int(time.time())}001',
                'Email': f'john.excel.{int(time.time())}@test.com',
                'Department': 'Engineering',
                'Manager': 'Tech Lead',
                'Start Date': '2024-01-15'
            },
            {
                'Name': 'Jane Excel Doe',
                'Employee ID': f'EXL{int(time.time())}002',
                'Email': f'jane.excel.{int(time.time())}@test.com',
                'Department': 'Marketing',
                'Manager': 'Marketing Head',
                'Start Date': '2024-02-01'
            }
        ]

        try:
            # Create Excel file
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            # Check for openpyxl error specifically
            error_message = str(data)
            has_openpyxl_error = "Missing optional dependency 'openpyxl'" in error_message
            
            if has_openpyxl_error:
                return self.log_test(
                    "Excel Import - Valid File",
                    False,
                    f"OPENPYXL ERROR DETECTED: {error_message}"
                )
            
            import_successful = success and data.get('imported_count', 0) >= 1
            
            return self.log_test(
                "Excel Import - Valid File",
                import_successful,
                f"Status: {status}, Imported: {data.get('imported_count', 0)} employees, Errors: {len(data.get('errors', []))}"
            )
            
        except Exception as e:
            error_str = str(e)
            has_openpyxl_error = "Missing optional dependency 'openpyxl'" in error_str
            
            return self.log_test(
                "Excel Import - Valid File",
                False,
                f"Exception: {error_str}, OPENPYXL_ERROR: {has_openpyxl_error}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_csv_import_valid_file(self):
        """Test importing a valid CSV file with proper employee data"""
        if not self.token:
            return self.log_test("CSV Import - Valid File", False, "No token available")

        # Create test data with proper column headers
        test_data = [
            {
                'Name': 'Bob CSV Johnson',
                'Employee ID': f'CSV{int(time.time())}001',
                'Email': f'bob.csv.{int(time.time())}@test.com',
                'Department': 'Sales',
                'Manager': 'Sales Director',
                'Start Date': '2024-01-20'
            }
        ]

        try:
            # Create CSV file
            temp_file_path = self.create_test_csv_file('.csv', test_data)
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_employees.csv', f, 'text/csv')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            import_successful = success and data.get('imported_count', 0) >= 1
            
            return self.log_test(
                "CSV Import - Valid File",
                import_successful,
                f"Status: {status}, Imported: {data.get('imported_count', 0)} employees"
            )
            
        except Exception as e:
            return self.log_test(
                "CSV Import - Valid File",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_excel_import_missing_columns(self):
        """Test Excel import with missing required columns"""
        if not self.token:
            return self.log_test("Excel Import - Missing Columns", False, "No token available")

        # Create test data missing required columns
        test_data = [
            {
                'Name': 'Incomplete User',
                'Email': f'incomplete.{int(time.time())}@test.com',
                # Missing: Employee ID, Department, Manager, Start Date
            }
        ]

        try:
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('incomplete_employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=400  # Should return error for missing columns
                )
            
            # Should fail with proper error message about missing columns
            error_message = data.get('detail', '')
            has_missing_columns_error = 'Missing required columns' in error_message
            
            return self.log_test(
                "Excel Import - Missing Columns",
                success and has_missing_columns_error,
                f"Status: {status}, Error: {error_message}"
            )
            
        except Exception as e:
            return self.log_test(
                "Excel Import - Missing Columns",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_excel_import_duplicate_employee_ids(self):
        """Test Excel import with duplicate Employee IDs"""
        if not self.token:
            return self.log_test("Excel Import - Duplicate IDs", False, "No token available")

        duplicate_id = f'DUP{int(time.time())}'
        test_data = [
            {
                'Name': 'First Duplicate',
                'Employee ID': duplicate_id,
                'Email': f'first.dup.{int(time.time())}@test.com',
                'Department': 'HR',
                'Manager': 'HR Head',
                'Start Date': '2024-01-15'
            },
            {
                'Name': 'Second Duplicate',
                'Employee ID': duplicate_id,  # Same ID
                'Email': f'second.dup.{int(time.time())}@test.com',
                'Department': 'Finance',
                'Manager': 'Finance Head',
                'Start Date': '2024-01-16'
            }
        ]

        try:
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('duplicate_employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200  # Should succeed but with errors
                )
            
            # Should import first employee but reject second due to duplicate ID
            imported_count = data.get('imported_count', 0)
            errors = data.get('errors', [])
            has_duplicate_error = any('already exists' in error for error in errors)
            
            return self.log_test(
                "Excel Import - Duplicate IDs",
                success and imported_count == 1 and has_duplicate_error,
                f"Imported: {imported_count}, Errors: {len(errors)}, Has duplicate error: {has_duplicate_error}"
            )
            
        except Exception as e:
            return self.log_test(
                "Excel Import - Duplicate IDs",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_pandas_read_excel_functionality(self):
        """Test that pandas can read Excel files without openpyxl errors"""
        try:
            # Create a simple Excel file
            test_data = [{'Name': 'Test User', 'ID': '123'}]
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            # Try to read with pandas directly
            df = pd.read_excel(temp_file_path, engine='openpyxl')
            
            read_successful = len(df) > 0 and 'Name' in df.columns
            
            return self.log_test(
                "Pandas Read Excel Functionality",
                read_successful,
                f"Successfully read Excel file with {len(df)} rows"
            )
            
        except Exception as e:
            error_str = str(e)
            has_openpyxl_error = "Missing optional dependency 'openpyxl'" in error_str
            
            return self.log_test(
                "Pandas Read Excel Functionality",
                False,
                f"Exception: {error_str}, OPENPYXL_ERROR: {has_openpyxl_error}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_ai_analysis_component(self):
        """Test AI analysis component during import (should not break import if it fails)"""
        if not self.token:
            return self.log_test("AI Analysis Component", False, "No token available")

        test_data = [
            {
                'Name': 'AI Test User',
                'Employee ID': f'AI{int(time.time())}',
                'Email': f'ai.test.{int(time.time())}@test.com',
                'Department': 'AI Testing',
                'Manager': 'AI Manager',
                'Start Date': '2024-01-15'
            }
        ]

        try:
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('ai_test_employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            # Import should succeed even if AI analysis fails
            import_successful = success and data.get('imported_count', 0) >= 1
            has_ai_analysis = 'ai_analysis' in data
            
            return self.log_test(
                "AI Analysis Component",
                import_successful,
                f"Import successful: {import_successful}, Has AI analysis: {has_ai_analysis}"
            )
            
        except Exception as e:
            return self.log_test(
                "AI Analysis Component",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_file_cleanup(self):
        """Test that temporary files are cleaned up properly"""
        if not self.token:
            return self.log_test("File Cleanup", False, "No token available")

        test_data = [
            {
                'Name': 'Cleanup Test User',
                'Employee ID': f'CLN{int(time.time())}',
                'Email': f'cleanup.test.{int(time.time())}@test.com',
                'Department': 'Cleanup',
                'Manager': 'Cleanup Manager',
                'Start Date': '2024-01-15'
            }
        ]

        try:
            temp_file_path = self.create_test_excel_file('.xlsx', test_data)
            
            # Get initial temp directory file count
            temp_dir = tempfile.gettempdir()
            initial_files = len([f for f in os.listdir(temp_dir) if f.startswith('tmp')])
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('cleanup_test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            # Wait a moment for cleanup
            time.sleep(2)
            
            # Check if temp files were cleaned up
            final_files = len([f for f in os.listdir(temp_dir) if f.startswith('tmp')])
            files_cleaned = final_files <= initial_files
            
            return self.log_test(
                "File Cleanup",
                success and files_cleaned,
                f"Import success: {success}, Temp files cleaned: {files_cleaned}"
            )
            
        except Exception as e:
            return self.log_test(
                "File Cleanup",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_invalid_file_format(self):
        """Test uploading invalid file format"""
        if not self.token:
            return self.log_test("Invalid File Format", False, "No token available")

        try:
            # Create a text file instead of Excel/CSV
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write("This is not an Excel or CSV file")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('invalid.txt', f, 'text/plain')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=400  # Should reject invalid format
                )
            
            # Should fail with proper error message
            error_message = data.get('detail', '')
            has_format_error = 'Excel' in error_message or 'CSV' in error_message
            
            return self.log_test(
                "Invalid File Format",
                success and has_format_error,
                f"Status: {status}, Error: {error_message}"
            )
            
        except Exception as e:
            return self.log_test(
                "Invalid File Format",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file.name)
            except:
                pass

    def run_excel_import_tests(self):
        """Run all Excel import tests"""
        print("🚀 Starting Excel Import Functionality Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("🎯 Focus: Excel Import with openpyxl dependency verification")
        print("=" * 80)
        
        # Login first
        if not self.login_admin():
            print("❌ Cannot proceed without admin login")
            return 1
        
        print("\n📊 Excel Import Tests:")
        print("-" * 40)
        
        # Core Excel import tests
        self.test_excel_import_valid_file()
        self.test_csv_import_valid_file()
        self.test_excel_import_missing_columns()
        self.test_excel_import_duplicate_employee_ids()
        
        # Technical verification tests
        print("\n🔧 Technical Verification Tests:")
        print("-" * 40)
        self.test_pandas_read_excel_functionality()
        self.test_ai_analysis_component()
        self.test_file_cleanup()
        self.test_invalid_file_format()
        
        # Final results
        print("\n" + "=" * 80)
        print(f"📈 Excel Import Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Excel import tests passed! openpyxl dependency issue resolved!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Excel import functionality needs attention.")
            return 1

def main():
    """Main test runner"""
    tester = ExcelImportTester()
    return tester.run_excel_import_tests()

if __name__ == "__main__":
    sys.exit(main())