"""
Email Service for HR System
Handles user invitations, password reset, email verification, and security notifications
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content, TemplateId, DynamicTemplateData
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr
import logging
from datetime import datetime, timezone
import secrets
import hashlib

logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    pass

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@brandingpioneers.com')
        
        if not self.api_key or self.api_key == "SG.test-key-for-development":
            logger.warning("SendGrid API key not configured. Email functionality will be simulated.")
            self.simulation_mode = True
        else:
            self.simulation_mode = False
            self.client = SendGridAPIClient(self.api_key)
    
    def _send_email(self, to_email: str, subject: str, html_content: str, plain_content: Optional[str] = None) -> bool:
        """Send email via SendGrid or simulate in development"""
        if self.simulation_mode:
            logger.info(f"SIMULATED EMAIL TO: {to_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info(f"CONTENT: {html_content[:200]}...")
            return True
        
        try:
            message = Mail(
                from_email=From(self.sender_email, "Branding Pioneers HR"),
                to_emails=To(to_email),
                subject=Subject(subject),
                html_content=Content("text/html", html_content)
            )
            
            if plain_content:
                message.plain_text_content = Content("text/plain", plain_content)
            
            response = self.client.send(message)
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"Email delivery failed: {str(e)}")
            raise EmailDeliveryError(f"Failed to send email to {to_email}: {str(e)}")
    
    def send_user_invitation(self, 
                           recipient_email: str, 
                           inviter_name: str, 
                           role: str, 
                           invitation_token: str,
                           invite_url: str) -> bool:
        """Send user invitation email"""
        subject = "Welcome to Branding Pioneers HR - Digital Ninjas Team!"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .btn {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🚀 Welcome to the Digital Ninjas Team!</h1>
                        <p>You've been invited to join Branding Pioneers HR System</p>
                    </div>
                    <div class="content">
                        <h2>Hi there, Future Ninja!</h2>
                        <p><strong>{inviter_name}</strong> has invited you to join the Branding Pioneers HR system as a <strong>{role}</strong>.</p>
                        
                        <p>🥷 <strong>What awaits you:</strong></p>
                        <ul>
                            <li>Employee onboarding & exit management</li>
                            <li>Task automation with AI insights</li>
                            <li>Comprehensive dashboard and analytics</li>
                            <li>Seamless team collaboration tools</li>
                        </ul>
                        
                        <p><strong>Ready to start your ninja journey?</strong></p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{invite_url}" class="btn">Accept Invitation & Setup Account 🎯</a>
                        </p>
                        
                        <p><strong>Security Note:</strong> This invitation link is valid for 48 hours and can only be used once.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="color: #666; font-size: 14px;">
                            If you can't click the button, copy and paste this link into your browser:<br>
                            <a href="{invite_url}">{invite_url}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Building the future, one ninja at a time 🌟</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def send_password_reset(self, 
                          recipient_email: str, 
                          user_name: str, 
                          reset_token: str,
                          reset_url: str) -> bool:
        """Send password reset email"""
        subject = "🔐 Password Reset - Branding Pioneers HR"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #f44336, #e91e63); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .btn {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #f44336, #e91e63); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                    .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🔐 Password Reset Request</h1>
                        <p>Secure your ninja account</p>
                    </div>
                    <div class="content">
                        <h2>Hi {user_name}!</h2>
                        <p>We received a request to reset the password for your Branding Pioneers HR account.</p>
                        
                        <div class="alert">
                            <p><strong>⚠️ Security Alert:</strong> If you didn't request this password reset, please ignore this email and contact your administrator immediately.</p>
                        </div>
                        
                        <p><strong>To reset your password:</strong></p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" class="btn">Reset Password Now 🛡️</a>
                        </p>
                        
                        <p><strong>Important Security Information:</strong></p>
                        <ul>
                            <li>This link is valid for 1 hour only</li>
                            <li>The link can only be used once</li>
                            <li>Your old password remains active until reset</li>
                        </ul>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="color: #666; font-size: 14px;">
                            If you can't click the button, copy and paste this link:<br>
                            <a href="{reset_url}">{reset_url}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Security First, Always 🔒</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def send_email_verification(self, 
                              recipient_email: str, 
                              user_name: str, 
                              verification_token: str,
                              verification_url: str) -> bool:
        """Send email verification"""
        subject = "✅ Verify Your Email - Branding Pioneers HR"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #4caf50, #8bc34a); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .btn {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #4caf50, #8bc34a); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>✅ Verify Your Email Address</h1>
                        <p>One step closer to becoming a digital ninja!</p>
                    </div>
                    <div class="content">
                        <h2>Welcome {user_name}!</h2>
                        <p>Thanks for joining the Branding Pioneers team! To complete your account setup and unlock all ninja features, please verify your email address.</p>
                        
                        <p><strong>Why verify?</strong></p>
                        <ul>
                            <li>🔒 Secure your account</li>
                            <li>📧 Receive important notifications</li>
                            <li>🚀 Access all HR features</li>
                            <li>👥 Enable team collaboration</li>
                        </ul>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" class="btn">Verify Email Address 🎯</a>
                        </p>
                        
                        <p><strong>Security:</strong> This verification link expires in 24 hours.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="color: #666; font-size: 14px;">
                            If you can't click the button, copy and paste this link:<br>
                            <a href="{verification_url}">{verification_url}</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Empowering teams, one verification at a time ⚡</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def send_security_notification(self, 
                                 recipient_email: str, 
                                 user_name: str, 
                                 event_type: str, 
                                 event_details: Dict[str, Any]) -> bool:
        """Send security notification email"""
        event_messages = {
            'login': '🔑 Successful login to your account',
            'password_change': '🔒 Password changed successfully',
            'profile_update': '👤 Profile information updated',
            'role_change': '⚡ Account role modified',
            'suspicious_login': '⚠️ Suspicious login attempt detected',
            'account_locked': '🔒 Account temporarily locked',
            'email_change': '📧 Email address changed'
        }
        
        subject = f"Security Alert - {event_messages.get(event_type, 'Account Activity')}"
        
        # Color scheme based on event type
        is_warning = event_type in ['suspicious_login', 'account_locked']
        header_color = "#f44336, #ff5722" if is_warning else "#2196f3, #3f51b5"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, {header_color}); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .info-box {{ background: white; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; }}
                    .warning-box {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>{event_messages.get(event_type, 'Security Notification')}</h1>
                        <p>Account activity for {user_name}</p>
                    </div>
                    <div class="content">
                        <h2>Hi {user_name},</h2>
                        <p>This is a security notification about activity on your Branding Pioneers HR account.</p>
                        
                        <div class="{'warning-box' if is_warning else 'info-box'}">
                            <h3>Event Details:</h3>
                            <ul>
        """
        
        for key, value in event_details.items():
            html_content += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        
        html_content += f"""
                            </ul>
                        </div>
                        
                        {'''
                        <div class="warning-box">
                            <p><strong>⚠️ Action Required:</strong> If you don't recognize this activity, please contact your administrator immediately and change your password.</p>
                        </div>
                        ''' if is_warning else '''
                        <p>✅ This appears to be legitimate activity. No action is required.</p>
                        '''}
                        
                        <p><strong>Security Tips:</strong></p>
                        <ul>
                            <li>Always use a strong, unique password</li>
                            <li>Enable two-factor authentication when available</li>
                            <li>Never share your login credentials</li>
                            <li>Report suspicious activity immediately</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Your security is our priority 🛡️</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def send_role_change_notification(self, 
                                    recipient_email: str, 
                                    user_name: str, 
                                    old_role: str, 
                                    new_role: str, 
                                    changed_by: str) -> bool:
        """Send role change notification"""
        subject = f"⚡ Role Updated - You're now a {new_role}!"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #ff9800, #f57c00); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .role-box {{ background: white; border: 2px solid #ff9800; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>⚡ Role Update Notification</h1>
                        <p>Your permissions have been updated!</p>
                    </div>
                    <div class="content">
                        <h2>Congratulations {user_name}!</h2>
                        <p>Your role in the Branding Pioneers HR system has been updated.</p>
                        
                        <div class="role-box">
                            <h3>🔄 Role Change</h3>
                            <p><strong>Previous Role:</strong> {old_role}</p>
                            <p><strong>New Role:</strong> {new_role}</p>
                            <p><strong>Updated By:</strong> {changed_by}</p>
                            <p><strong>Effective:</strong> Immediately</p>
                        </div>
                        
                        <p><strong>What this means:</strong></p>
                        <ul>
                            <li>Your access permissions have been updated</li>
                            <li>You may see new features in your dashboard</li>
                            <li>Some previous features may no longer be available</li>
                            <li>Changes take effect on your next login</li>
                        </ul>
                        
                        <p>If you have questions about your new role or permissions, please contact your administrator.</p>
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Empowering every ninja with the right tools 🚀</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def send_bulk_notification(self, 
                             recipients: List[str], 
                             subject: str, 
                             content: str, 
                             sender_name: str = "HR Team") -> Dict[str, Any]:
        """Send bulk notifications to multiple users"""
        results = {"success": 0, "failed": 0, "errors": []}
        
        html_content = f"""
        <html>
            <head>
                <style>
                    .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #f8f9fa; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>📢 Team Notification</h1>
                        <p>Important update from {sender_name}</p>
                    </div>
                    <div class="content">
                        {content}
                    </div>
                    <div class="footer">
                        <p>© {datetime.now().year} Branding Pioneers - Digital Ninjas<br>
                        Keeping our team connected 🌟</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        for recipient in recipients:
            try:
                if self._send_email(recipient, subject, html_content):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to send to {recipient}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error sending to {recipient}: {str(e)}")
        
        return results

# Create global instance
email_service = EmailService()