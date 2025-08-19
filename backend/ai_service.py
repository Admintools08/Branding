"""
AI Service for HR System using Google Gemini
Handles Excel analysis, employee insights, and smart recommendations
"""
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import json
import logging
import uuid

load_dotenv()

logger = logging.getLogger(__name__)

class HRAIService:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
    async def analyze_excel_file(self, file_path: str, file_type: str = "excel") -> Dict[str, Any]:
        """
        Analyze uploaded Excel/CSV file and provide intelligent insights
        """
        try:
            session_id = f"excel_analysis_{uuid.uuid4()}"
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="""You are an AI HR analyst expert. When analyzing employee data files, provide:
                
                1. DATA QUALITY ANALYSIS:
                   - Missing or incomplete data
                   - Inconsistencies in formatting
                   - Duplicate entries
                   - Data validation issues
                
                2. EMPLOYEE INSIGHTS:
                   - Departmental distribution
                   - Manager workload analysis
                   - Start date patterns and hiring trends
                   - Employee ID patterns and suggestions
                
                3. SMART RECOMMENDATIONS:
                   - Data cleanup suggestions
                   - Onboarding process improvements
                   - Manager assignment optimization
                   - Department balancing recommendations
                
                4. RISK ANALYSIS:
                   - Potential issues with current data
                   - Missing mandatory information
                   - Compliance concerns
                
                Provide responses in JSON format with clear, actionable insights."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Determine MIME type based on file extension
            mime_type = "text/csv" if file_path.endswith('.csv') else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            file_content = FileContentWithMimeType(
                file_path=file_path,
                mime_type=mime_type
            )
            
            user_message = UserMessage(
                text="""Analyze this employee data file and provide comprehensive insights. Focus on:
                
                1. Data quality assessment
                2. Employee distribution analysis  
                3. Smart recommendations for HR processes
                4. Potential issues and risks
                
                Return your analysis in JSON format with structured sections.""",
                file_contents=[file_content]
            )
            
            response = await chat.send_message(user_message)
            
            # Try to parse as JSON, fallback to structured text if needed
            try:
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # Structure the response if it's not valid JSON
                analysis_result = {
                    "analysis": response,
                    "data_quality": {"status": "analyzed", "details": "See full analysis"},
                    "insights": {"summary": "Comprehensive analysis completed"},
                    "recommendations": {"actions": "See full analysis for recommendations"},
                    "risks": {"assessment": "Review full analysis for potential issues"}
                }
            
            return {
                "success": True,
                "analysis": analysis_result,
                "file_analyzed": file_path,
                "analysis_type": "comprehensive_hr_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_analyzed": file_path
            }
    
    async def generate_employee_insights(self, employee_data: Dict[str, Any], task_data: List[Dict]) -> Dict[str, Any]:
        """
        Generate AI-powered insights for individual employees
        """
        try:
            session_id = f"employee_insights_{uuid.uuid4()}"
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="""You are an HR AI advisor. Analyze individual employee data and provide:
                
                1. ONBOARDING PROGRESS: Assessment of current progress and bottlenecks
                2. TASK PERFORMANCE: Analysis of task completion patterns
                3. PERSONALIZED RECOMMENDATIONS: Specific suggestions for this employee
                4. RISK INDICATORS: Early warning signs or concerns
                5. SUCCESS METRICS: Key indicators of successful integration
                
                Provide actionable, empathetic, and professional insights."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            employee_summary = f"""
            Employee Profile:
            - Name: {employee_data.get('name', 'Unknown')}
            - Department: {employee_data.get('department', 'Unknown')}
            - Status: {employee_data.get('status', 'Unknown')}
            - Start Date: {employee_data.get('start_date', 'Unknown')}
            - Manager: {employee_data.get('manager', 'Unknown')}
            
            Associated Tasks: {len(task_data)} total tasks
            Task Details: {json.dumps(task_data, default=str, indent=2)}
            """
            
            user_message = UserMessage(
                text=f"""Analyze this employee's profile and task performance. Provide insights in JSON format:
                
                {employee_summary}
                
                Focus on:
                1. Current onboarding/exit progress
                2. Task completion patterns
                3. Potential concerns or risks
                4. Personalized recommendations
                5. Success indicators
                
                Return structured JSON with actionable insights."""
            )
            
            response = await chat.send_message(user_message)
            
            try:
                insights = json.loads(response)
            except json.JSONDecodeError:
                insights = {
                    "progress_assessment": "Analysis completed",
                    "task_performance": "Review provided",
                    "recommendations": response,
                    "risk_indicators": "Assessment completed",
                    "success_metrics": "Analyzed"
                }
            
            return {
                "success": True,
                "employee_id": employee_data.get('id'),
                "insights": insights,
                "generated_at": "now"
            }
            
        except Exception as e:
            logger.error(f"Error generating employee insights: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "employee_id": employee_data.get('id')
            }
    
    async def suggest_task_improvements(self, task_data: List[Dict], employee_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze tasks and suggest improvements for HR workflows
        """
        try:
            session_id = f"task_analysis_{uuid.uuid4()}"
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="""You are an HR process optimization expert. Analyze task data to provide:
                
                1. WORKFLOW EFFICIENCY: Identify bottlenecks and delays
                2. TASK OPTIMIZATION: Suggest improvements for task sequences
                3. AUTOMATION OPPORTUNITIES: Tasks that could be automated
                4. MANAGER WORKLOAD: Analysis of task distribution across managers
                5. COMPLIANCE GAPS: Missing or delayed critical tasks
                
                Provide practical, implementable recommendations."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            analysis_data = {
                "total_tasks": len(task_data),
                "total_employees": len(employee_data),
                "task_summary": task_data[:10],  # Sample for analysis
                "employee_summary": employee_data[:5]  # Sample for context
            }
            
            user_message = UserMessage(
                text=f"""Analyze this HR task and employee data to suggest workflow improvements:
                
                Data Summary: {json.dumps(analysis_data, default=str, indent=2)}
                
                Provide recommendations for:
                1. Process optimization
                2. Task automation opportunities  
                3. Manager workload distribution
                4. Compliance improvements
                5. Efficiency enhancements
                
                Return structured JSON with actionable recommendations."""
            )
            
            response = await chat.send_message(user_message)
            
            try:
                suggestions = json.loads(response)
            except json.JSONDecodeError:
                suggestions = {
                    "workflow_efficiency": "Analysis completed",
                    "optimization_opportunities": response,
                    "automation_suggestions": "Review provided",
                    "workload_distribution": "Analyzed",
                    "compliance_improvements": "Recommendations generated"
                }
            
            return {
                "success": True,
                "suggestions": suggestions,
                "analysis_scope": f"{len(task_data)} tasks, {len(employee_data)} employees",
                "generated_at": "now"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing tasks: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_employee_data(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered validation of employee data for completeness and consistency
        """
        try:
            session_id = f"data_validation_{uuid.uuid4()}"
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message="""You are a data quality expert for HR systems. Validate employee data and provide:
                
                1. COMPLETENESS CHECK: Missing required fields
                2. CONSISTENCY VALIDATION: Data format and logic consistency  
                3. COMPLIANCE REVIEW: Ensure data meets HR standards
                4. SUGGESTIONS: Recommendations for data improvement
                
                Be thorough but practical in your recommendations."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            user_message = UserMessage(
                text=f"""Validate this employee data for completeness, consistency, and compliance:
                
                Employee Data: {json.dumps(employee_data, default=str, indent=2)}
                
                Check for:
                1. Missing mandatory fields
                2. Data format consistency
                3. Logical consistency (dates, roles, etc.)
                4. Compliance with HR standards
                
                Return validation results in JSON format with specific issues and suggestions."""
            )
            
            response = await chat.send_message(user_message)
            
            try:
                validation = json.loads(response)
            except json.JSONDecodeError:
                validation = {
                    "validation_status": "completed",
                    "issues_found": "See detailed response",
                    "recommendations": response,
                    "compliance_status": "reviewed"
                }
            
            return {
                "success": True,
                "validation": validation,
                "employee_id": employee_data.get('id'),
                "validated_at": "now"
            }
            
        except Exception as e:
            logger.error(f"Error validating employee data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "employee_id": employee_data.get('id')
            }