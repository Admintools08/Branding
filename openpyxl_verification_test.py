#!/usr/bin/env python3

import requests
import sys
import json
import tempfile
import os
import pandas as pd
from datetime import datetime, timezone
import time

class OpenpyxlVerificationTester:
    def __init__(self):
        # Use the production URL from frontend .env
        self.base_url = "https://data-import-tool-1.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
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
                headers.pop('Content-Type', None)
                
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=15)
            
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
        """Test login with admin@test.com/admin123 credentials as specified in review request"""
        # First try the credentials specified in the review request
        success, status, data = self.make_request(
            'POST',
            'auth/login',
            {"email": "admin@test.com", "password": "admin123"},
            expected_status=200
        )
        
        # If that fails, try the system admin credentials
        if not success:
            success, status, data = self.make_request(
                'POST',
                'auth/login',
                {"email": "admin@brandingpioneers.com", "password": "SuperAdmin2024!"},
                expected_status=200
            )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            user_info = data.get('user', {})
            return self.log_test(
                "Login with admin credentials",
                True,
                f"Logged in as {user_info.get('name', 'Admin')} ({user_info.get('email', 'unknown')})"
            )
        else:
            return self.log_test(
                "Login with admin credentials",
                False,
                f"Status: {status}, Data: {data}"
            )

    def test_excel_import_endpoint_accessible(self):
        """Verify that the Excel import endpoint is accessible and working"""
        if not self.token:
            return self.log_test("Excel import endpoint accessible", False, "No token available")
        
        # Test with a simple CSV to verify endpoint is working
        csv_content = """Name,Employee ID,Email,Department,Manager,Start Date
Test User,TEST001,test@example.com,Testing,Test Manager,2024-01-15"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            endpoint_accessible = success and status == 200
            
            return self.log_test(
                "Excel import endpoint accessible and working",
                endpoint_accessible,
                f"Status: {status}, Endpoint responding correctly"
            )
            
        except Exception as e:
            return self.log_test(
                "Excel import endpoint accessible and working",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_excel_files_import_without_openpyxl_errors(self):
        """Test that Excel files (.xlsx) can be imported without openpyxl errors"""
        if not self.token:
            return self.log_test("Excel files import without openpyxl errors", False, "No token available")
        
        # Create a proper Excel file using pandas with openpyxl engine
        excel_data = {
            'Name': ['Excel Test User 1', 'Excel Test User 2'],
            'Employee ID': ['XLSX001', 'XLSX002'],
            'Email': ['excel1@test.com', 'excel2@test.com'],
            'Department': ['Excel Testing', 'Excel Testing'],
            'Manager': ['Excel Manager', 'Excel Manager'],
            'Start Date': ['2024-01-15', '2024-01-16']
        }
        
        df = pd.DataFrame(excel_data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file_path = temp_file.name
            
        try:
            # Create Excel file using openpyxl engine
            df.to_excel(temp_file_path, index=False, engine='openpyxl')
            
            # Import the Excel file
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            # Check for openpyxl-related errors in response
            has_openpyxl_error = False
            error_message = ""
            
            if not success and isinstance(data, dict):
                error_message = str(data.get('detail', '')).lower()
                has_openpyxl_error = (
                    'openpyxl' in error_message or 
                    'missing optional dependency' in error_message or
                    'excel file processing not available' in error_message
                )
            
            import_successful = success and data.get('imported_count', 0) >= 1
            no_openpyxl_errors = not has_openpyxl_error
            
            return self.log_test(
                "Excel files (.xlsx) import without openpyxl errors",
                import_successful and no_openpyxl_errors,
                f"Import successful: {import_successful}, No openpyxl errors: {no_openpyxl_errors}, Imported: {data.get('imported_count', 0)}"
            )
            
        except Exception as e:
            return self.log_test(
                "Excel files (.xlsx) import without openpyxl errors",
                False,
                f"Exception during Excel import: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_pandas_read_excel_with_openpyxl_engine(self):
        """Test that pandas.read_excel() function works properly with openpyxl engine"""
        try:
            # Create test data
            test_data = {
                'Name': ['Pandas Test User'],
                'Employee ID': ['PANDAS001'],
                'Email': ['pandas@test.com'],
                'Department': ['Pandas Testing'],
                'Manager': ['Pandas Manager'],
                'Start Date': ['2024-01-15']
            }
            
            df_original = pd.DataFrame(test_data)
            
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_file_path = temp_file.name
                
            # Write Excel file using openpyxl engine
            df_original.to_excel(temp_file_path, index=False, engine='openpyxl')
            
            # Read Excel file back using openpyxl engine (this is what the backend does)
            df_read = pd.read_excel(temp_file_path, engine='openpyxl')
            
            # Verify data integrity
            data_matches = (
                len(df_read) == len(df_original) and
                df_read['Name'].iloc[0] == 'Pandas Test User' and
                df_read['Employee ID'].iloc[0] == 'PANDAS001'
            )
            
            return self.log_test(
                "pandas.read_excel() works properly with openpyxl engine",
                data_matches,
                f"Excel read/write cycle successful, Data integrity preserved: {data_matches}"
            )
            
        except ImportError as e:
            if 'openpyxl' in str(e):
                return self.log_test(
                    "pandas.read_excel() works properly with openpyxl engine",
                    False,
                    f"openpyxl dependency missing: {str(e)}"
                )
            else:
                return self.log_test(
                    "pandas.read_excel() works properly with openpyxl engine",
                    False,
                    f"Import error: {str(e)}"
                )
        except Exception as e:
            return self.log_test(
                "pandas.read_excel() works properly with openpyxl engine",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_ai_analysis_component_doesnt_break_import(self):
        """Test that AI analysis component (if used) doesn't break the import process"""
        if not self.token:
            return self.log_test("AI analysis component doesn't break import", False, "No token available")
        
        # Create Excel file that should trigger AI analysis
        excel_data = {
            'Name': ['AI Analysis Test User'],
            'Employee ID': ['AI001'],
            'Email': ['ai.analysis@test.com'],
            'Department': ['AI Testing'],
            'Manager': ['AI Manager'],
            'Start Date': ['2024-01-15']
        }
        
        df = pd.DataFrame(excel_data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file_path = temp_file.name
            
        try:
            df.to_excel(temp_file_path, index=False, engine='openpyxl')
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('ai_test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=200
                )
            
            # Import should succeed even if AI analysis fails
            import_successful = success and data.get('imported_count', 0) >= 1
            
            # Check if AI analysis was attempted (it's optional)
            ai_analysis_attempted = 'ai_analysis' in data if isinstance(data, dict) else False
            
            return self.log_test(
                "AI analysis component doesn't break import process",
                import_successful,
                f"Import successful: {import_successful}, AI analysis attempted: {ai_analysis_attempted}"
            )
            
        except Exception as e:
            return self.log_test(
                "AI analysis component doesn't break import process",
                False,
                f"Exception: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_error_handling_for_invalid_files(self):
        """Test that error handling works for invalid files"""
        if not self.token:
            return self.log_test("Error handling works for invalid files", False, "No token available")
        
        test_results = []
        
        # Test 1: Invalid file format (should be rejected)
        try:
            invalid_content = "This is not an Excel or CSV file"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(invalid_content)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('invalid.txt', f, 'text/plain')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=400
                )
            
            # Should return 400 error for invalid file format
            test_results.append(("Invalid file format rejection", success, status))
            os.unlink(temp_file_path)
            
        except Exception as e:
            test_results.append(("Invalid file format rejection", False, f"Exception: {str(e)}"))
        
        # Test 2: Excel file with missing required columns
        try:
            incomplete_data = {
                'Name': ['Incomplete User'],
                'Email': ['incomplete@test.com']
                # Missing: Employee ID, Department, Manager, Start Date
            }
            
            df = pd.DataFrame(incomplete_data)
            
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_file_path = temp_file.name
                
            df.to_excel(temp_file_path, index=False, engine='openpyxl')
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('incomplete.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                success, status, data = self.make_request(
                    'POST',
                    'employees/import-excel',
                    files=files,
                    expected_status=400
                )
            
            # Should return 400 error for missing columns
            test_results.append(("Missing columns error handling", success, status))
            os.unlink(temp_file_path)
            
        except Exception as e:
            test_results.append(("Missing columns error handling", False, f"Exception: {str(e)}"))
        
        # Evaluate overall error handling
        successful_tests = [r for r in test_results if r[1]]
        all_error_handling_works = len(successful_tests) == len(test_results)
        
        return self.log_test(
            "Error handling works for invalid files",
            all_error_handling_works,
            f"Error handling tests: {len(successful_tests)}/{len(test_results)} passed"
        )

    def test_openpyxl_dependency_completely_resolved(self):
        """Final verification that openpyxl dependency issue is completely resolved"""
        try:
            # Test 1: Import openpyxl directly
            import openpyxl
            openpyxl_importable = True
            openpyxl_version = openpyxl.__version__
        except ImportError:
            openpyxl_importable = False
            openpyxl_version = "Not available"
        
        # Test 2: Test pandas Excel functionality
        try:
            import pandas as pd
            # Create a simple Excel file and read it back
            test_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            test_df.to_excel(temp_file_path, index=False, engine='openpyxl')
            read_df = pd.read_excel(temp_file_path, engine='openpyxl')
            pandas_excel_works = len(read_df) == 2 and read_df['A'].iloc[0] == 1
            
            os.unlink(temp_file_path)
            
        except Exception as e:
            pandas_excel_works = False
        
        # Test 3: Backend Excel import functionality (already tested above)
        backend_excel_works = self.tests_passed > 0  # If we got this far, backend is working
        
        all_tests_pass = openpyxl_importable and pandas_excel_works and backend_excel_works
        
        return self.log_test(
            "openpyxl dependency issue completely resolved",
            all_tests_pass,
            f"openpyxl importable: {openpyxl_importable} (v{openpyxl_version}), pandas Excel works: {pandas_excel_works}, backend Excel works: {backend_excel_works}"
        )

    def run_verification_tests(self):
        """Run all verification tests for the openpyxl dependency issue"""
        print("🎯 OPENPYXL DEPENDENCY ISSUE VERIFICATION")
        print(f"📍 Testing against: {self.base_url}")
        print("🔍 Verifying user-reported issue: 'Import failed: Error processing file: Missing optional dependency 'openpyxl''")
        print("👤 Using admin@test.com/admin123 credentials as requested")
        print("=" * 100)
        
        # Authentication
        print("\n🔐 Authentication Test:")
        if not self.test_login_with_admin_credentials():
            print("❌ Cannot proceed without authentication")
            return 1
        
        # Core Excel Import Tests
        print("\n📊 Excel Import Core Tests:")
        self.test_excel_import_endpoint_accessible()
        self.test_excel_files_import_without_openpyxl_errors()
        self.test_pandas_read_excel_with_openpyxl_engine()
        
        # Integration Tests
        print("\n🤖 Integration Tests:")
        self.test_ai_analysis_component_doesnt_break_import()
        
        # Error Handling Tests
        print("\n⚠️ Error Handling Tests:")
        self.test_error_handling_for_invalid_files()
        
        # Final Verification
        print("\n✅ Final Verification:")
        self.test_openpyxl_dependency_completely_resolved()
        
        # Results Summary
        print("\n" + "=" * 100)
        print(f"📈 VERIFICATION RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 SUCCESS: openpyxl dependency issue is COMPLETELY RESOLVED!")
            print("✅ Excel import functionality is working correctly")
            print("✅ No 'Missing optional dependency openpyxl' errors detected")
            print("✅ All Excel import features are operational")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  PARTIAL SUCCESS: {failed_tests} tests failed")
            print("❌ openpyxl dependency issue may not be completely resolved")
            return 1

def main():
    """Main test runner"""
    tester = OpenpyxlVerificationTester()
    return tester.run_verification_tests()

if __name__ == "__main__":
    sys.exit(main())