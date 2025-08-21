import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Calendar } from './components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './components/ui/popover';
import { Checkbox } from './components/ui/checkbox';
import { Toaster, toast } from 'sonner';
import AdminPanel from './components/AdminPanel';
import { ForgotPasswordForm, ChangePasswordForm, AcceptInvitationForm } from './components/AuthForms';
import { 
  Users, 
  UserPlus, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  TrendingUp,
  Calendar as CalendarIcon,
  Settings,
  LogOut,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Download,
  FileText,
  Upload,
  Trophy,
  Star,
  Target,
  Zap,
  Gift,
  PartyPopper,
  Bell,
  Coffee,
  Rocket,
  Brain,
  Sparkles,
  Save,
  X,
  Volume2,
  Shield,
  Key,
  Mail,
  UserCheck,
  Crown,
  Eye,
  EyeOff
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Login Form Component (moved outside App and optimized to prevent re-renders)
const LoginForm = React.memo(({ 
  loginForm, 
  onEmailChange, 
  onPasswordChange, 
  onTogglePasswordVisibility,
  handleLogin, 
  loading, 
  onShowForgotPassword,
  hasError,
  errorMessage
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
    <div className="absolute inset-0 opacity-20 bg-gray-900"></div>
    
    <Card className="w-full max-w-md bg-white/95 backdrop-blur-sm shadow-2xl border-0">
      <CardHeader className="text-center pb-2">
        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
          <Rocket className="w-8 h-8 text-white" />
        </div>
        <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
          Digital Ninjas
        </CardTitle>
        <p className="text-gray-600 text-sm">
          Branding Pioneers - HR Command Center
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium text-gray-700">
              Email Address
            </Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                id="email"
                type="email"
                placeholder="your.email@company.com"
                value={loginForm.email}
                onChange={onEmailChange}
                className={`pl-10 ${hasError 
                  ? 'border-red-300 focus:border-red-500' 
                  : 'border-gray-300 focus:border-purple-500'}`}
                required
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-gray-700">
              Password
            </Label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                id="password"
                type={loginForm.showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={loginForm.password}
                onChange={onPasswordChange}
                className={`pl-10 pr-10 ${hasError 
                  ? 'border-red-300 focus:border-red-500' 
                  : 'border-gray-300 focus:border-purple-500'}`}
                required
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                onClick={onTogglePasswordVisibility}
              >
                {loginForm.showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={onShowForgotPassword}
              className="text-purple-600 hover:text-purple-800 font-medium"
            >
              Forgot Password?
            </button>
          </div>

          {hasError && errorMessage && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mt-2">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 font-medium">
                    {errorMessage}
                  </p>
                </div>
              </div>
            </div>
          )}

          <Button 
            type="submit" 
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-2.5 shadow-lg transform transition hover:scale-[1.02]"
            disabled={loading}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing In...
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <Zap className="w-4 h-4 mr-2" />
                Access Ninja HQ
              </div>
            )}
          </Button>
        </form>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            🥷 Empowering teams with ninja-level efficiency
          </p>
        </div>
      </CardContent>
    </Card>

    <ForgotPasswordForm 
      isOpen={false} 
      onClose={() => {}} 
    />
  </div>
));

const App = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [recentActivities, setRecentActivities] = useState({});
  const [upcomingEvents, setUpcomingEvents] = useState({});
  const [upcomingTasks, setUpcomingTasks] = useState({});
  const [currentView, setCurrentView] = useState('dashboard');
  const [aiInsights, setAiInsights] = useState(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const audioContextRef = useRef(null);

  // Enhanced login form state
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
    showPassword: false
  });
  
  const [loginError, setLoginError] = useState(false);
  const [loginErrorMessage, setLoginErrorMessage] = useState('');

  // Sound effects
  const playSound = (type = 'click') => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const ctx = audioContextRef.current;
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Different sounds for different actions
    switch (type) {
      case 'success':
        oscillator.frequency.setValueAtTime(800, ctx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.3);
        break;
      case 'error':
        oscillator.frequency.setValueAtTime(300, ctx.currentTime);
        gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.5);
        break;
      case 'notification':
        oscillator.frequency.setValueAtTime(600, ctx.currentTime);
        oscillator.frequency.setValueAtTime(800, ctx.currentTime + 0.1);
        oscillator.frequency.setValueAtTime(600, ctx.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.05, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.3);
        break;
      default:
        oscillator.frequency.setValueAtTime(400, ctx.currentTime);
        gainNode.gain.setValueAtTime(0.03, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.1);
    }
  };

  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  const validateToken = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Token validation failed:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const loadData = async () => {
    try {
      const [employeesRes, tasksRes, statsRes, activitiesRes, eventsRes, upcomingTasksRes] = await Promise.all([
        axios.get(`${API}/employees`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/tasks`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/dashboard/recent-activities`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/dashboard/upcoming-events`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/dashboard/upcoming-tasks`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setEmployees(employeesRes.data);
      setTasks(tasksRes.data);
      setDashboardStats(statsRes.data);
      setRecentActivities(activitiesRes.data);
      setUpcomingEvents(eventsRes.data);
      setUpcomingTasks(upcomingTasksRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    }
  };

  const handleLogin = useCallback(async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setLoginError(false); // Clear any previous errors
      
      const response = await axios.post(`${API}/auth/login`, {
        email: loginForm.email,
        password: loginForm.password
      });
      
      const { access_token, user: userData } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      playSound('success');
      toast.success(`Welcome back, ${userData.name}! 🎉`);
    } catch (error) {
      playSound('error');
      setLoginError(true); // Set error state for visual feedback
      
      // Enhanced error handling for better user experience
      let errorMessage = 'Login failed';
      
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail;
        
        if (status === 401) {
          if (detail === 'Invalid credentials') {
            errorMessage = '🔒 Invalid email or password. Please check your credentials and try again.';
          } else if (detail === 'Token expired') {
            errorMessage = '⏰ Your session has expired. Please login again.';
          } else if (detail === 'User not found') {
            errorMessage = '👤 No account found with this email address.';
          } else {
            errorMessage = '🚫 Authentication failed. Please check your login details.';
          }
        } else if (status === 422) {
          errorMessage = '📝 Please check that your email and password are filled in correctly.';
        } else if (status === 429) {
          errorMessage = '⏳ Too many login attempts. Please wait a moment before trying again.';
        } else if (status >= 500) {
          errorMessage = '🔧 Server error. Please try again in a few moments.';
        } else {
          errorMessage = detail || 'Login failed. Please try again.';
        }
      } else if (error.request) {
        errorMessage = '🌐 Cannot connect to server. Please check your internet connection.';
      } else {
        errorMessage = 'An unexpected error occurred. Please try again.';
      }
      
      toast.error(errorMessage, {
        duration: 5000, // Show error toast longer
        style: {
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          color: '#dc2626'
        }
      });
    } finally {
      setLoading(false);
    }
  }, [loginForm.email, loginForm.password]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setEmployees([]);
    setTasks([]);
    setDashboardStats({});
    setRecentActivities({});
    setCurrentView('dashboard');
    toast.success('Logged out successfully');
  };

  // Optimized handlers to prevent unnecessary re-renders
  const handleEmailChange = useCallback((e) => {
    setLoginForm(prev => ({ ...prev, email: e.target.value }));
    if (loginError) setLoginError(false); // Clear error when user starts typing
  }, [loginError]);

  const handlePasswordChange = useCallback((e) => {
    setLoginForm(prev => ({ ...prev, password: e.target.value }));
    if (loginError) setLoginError(false); // Clear error when user starts typing
  }, [loginError]);

  const handleTogglePasswordVisibility = useCallback(() => {
    setLoginForm(prev => ({ ...prev, showPassword: !prev.showPassword }));
  }, []);

  const handleShowForgotPassword = useCallback(() => {
    setShowForgotPassword(true);
  }, []);

  const getUserRoleColor = (role) => {
    const colors = {
      super_admin: 'bg-purple-100 text-purple-800 border-purple-200',
      admin: 'bg-red-100 text-red-800 border-red-200',
      hr_manager: 'bg-blue-100 text-blue-800 border-blue-200',
      manager: 'bg-green-100 text-green-800 border-green-200',
      employee: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[role] || colors.employee;
  };

  const getUserRoleIcon = (role) => {
    const icons = {
      super_admin: Crown,
      admin: Shield,
      hr_manager: Users,
      manager: Settings,
      employee: UserCheck
    };
    const IconComponent = icons[role] || UserCheck;
    return <IconComponent className="w-3 h-3" />;
  };

  const canAccessAdminPanel = (userRole) => {
    return ['super_admin', 'admin', 'hr_manager'].includes(userRole);
  };

  // Employee management functions
  const createEmployee = async (employeeData) => {
    try {
      await axios.post(`${API}/employees`, employeeData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound('success');
      toast.success('🚀 New ninja added to the team!');
      loadData();
    } catch (error) {
      playSound('error');
      toast.error('Failed to create employee: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to create employee');
    }
  };

  const updateEmployee = async (employeeId, updateData) => {
    try {
      const response = await axios.put(`${API}/employees/${employeeId}/profile`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound('success');
      toast.success('✨ Employee profile updated successfully!');
      loadData();
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('Failed to update employee: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to update employee');
    }
  };

  const updateEmployeeStatus = async (employeeId, status, exitDate = null) => {
    try {
      const updateData = { status };
      if (exitDate) updateData.exit_date = exitDate;
      
      await axios.put(`${API}/employees/${employeeId}`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound('success');
      toast.success(`🎯 Employee status updated to ${status}!`);
      loadData();
    } catch (error) {
      playSound('error');
      toast.error('Failed to update employee status: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to update status');
    }
  };

  const deleteEmployee = async (employeeId) => {
    try {
      await axios.delete(`${API}/employees/${employeeId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound('success');
      toast.success('Employee removed from team');
      loadData();
    } catch (error) {
      playSound('error');
      toast.error('Failed to delete employee: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to delete employee');
    }
  };

  const importFromExcel = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/employees/import-excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
      });
      
      playSound('success');
      toast.success(`📊 Successfully imported ${response.data.created_count} employees!`);
      loadData();
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('Import failed: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Import failed');
    }
  };

  const analyzeEmployee = async (employeeId) => {
    try {
      const response = await axios.post(`${API}/ai/analyze-employee`, {
        employee_id: employeeId
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound('notification');
      toast.success('🧠 AI analysis completed!');
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('AI analysis failed: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'AI analysis failed');
    }
  };

  const updateTaskStatus = async (taskId, status) => {
    try {
      await axios.put(`${API}/tasks/${taskId}`, { status }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      playSound(status === 'completed' ? 'success' : 'click');
      toast.success(status === 'completed' ? '🏆 Task completed! Great job!' : '📝 Task updated');
      loadData();
    } catch (error) {
      playSound('error');
      toast.error('Failed to update task');
      console.error('Error updating task:', error);
    }
  };

  const downloadReport = async (type) => {
    try {
      const response = await axios.get(`${API}/reports/${type}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${type}-report-${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      playSound('success');
      toast.success('📄 Report downloaded successfully!');
    } catch (error) {
      playSound('error');
      toast.error('Failed to download report: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Add Employee Form Component
  const AddEmployeeForm = ({ onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
      name: '',
      email: '',
      employee_id: '',
      department: '',
      position: '',
      manager: '',
      start_date: new Date().toISOString().split('T')[0],
      birthday: '',
      phone: '',
      status: 'onboarding'
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        // Convert start_date and birthday to datetime format
        const submitData = {
          ...formData,
          start_date: new Date(formData.start_date).toISOString(),
          birthday: formData.birthday ? new Date(formData.birthday).toISOString() : null
        };
        await onSubmit(submitData);
        playSound('success');
      } catch (error) {
        playSound('error');
      } finally {
        setLoading(false);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="John Doe"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="employee_id">Employee ID *</Label>
            <Input
              id="employee_id"
              value={formData.employee_id}
              onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
              placeholder="EMP001"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email Address *</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            placeholder="john.doe@company.com"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="department">Department *</Label>
            <Input
              id="department"
              value={formData.department}
              onChange={(e) => setFormData({...formData, department: e.target.value})}
              placeholder="Engineering"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="position">Position *</Label>
            <Input
              id="position"
              value={formData.position}
              onChange={(e) => setFormData({...formData, position: e.target.value})}
              placeholder="Software Developer"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="manager">Manager *</Label>
            <Input
              id="manager"
              value={formData.manager}
              onChange={(e) => setFormData({...formData, manager: e.target.value})}
              placeholder="Jane Smith"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="start_date">Start Date *</Label>
            <Input
              id="start_date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="birthday">Birthday</Label>
            <Input
              id="birthday"
              type="date"
              value={formData.birthday}
              onChange={(e) => setFormData({...formData, birthday: e.target.value})}
              placeholder="Optional"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <Input
              id="phone"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              placeholder="+1 (555) 123-4567"
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading} className="bg-gradient-to-r from-purple-600 to-pink-600">
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Adding Ninja...
              </div>
            ) : (
              <div className="flex items-center">
                <UserPlus className="w-4 h-4 mr-2" />
                Add Ninja
              </div>
            )}
          </Button>
        </div>
      </form>
    );
  };

  // Excel Import Form Component
  const ExcelImportForm = ({ onSubmit, onCancel }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!file) return;
      
      setLoading(true);
      try {
        await onSubmit(file);
        playSound('success');
      } catch (error) {
        playSound('error');
      } finally {
        setLoading(false);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="excel-file">Select Excel File</Label>
          <Input
            id="excel-file"
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
          <p className="text-sm text-gray-500">
            Supports .xlsx, .xls, and .csv files. Make sure your file has columns: name, email, employee_id, department, position
          </p>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !file} className="bg-gradient-to-r from-green-600 to-blue-600">
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Importing...
              </div>
            ) : (
              <div className="flex items-center">
                <Upload className="w-4 h-4 mr-2" />
                Import Ninjas
              </div>
            )}
          </Button>
        </div>
      </form>
    );
  };

  // Edit Employee Form Component  
  const EditEmployeeForm = ({ employee, onSubmit, onCancel, onUpdateStatus, onDelete }) => {
    const [formData, setFormData] = useState({
      name: employee.name || '',
      email: employee.email || '',
      employee_id: employee.employee_id || '',
      department: employee.department || '',
      position: employee.position || '',
      phone: employee.phone || '',
      birthday: employee.birthday ? new Date(employee.birthday).toISOString().split('T')[0] : ''
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      try {
        const submitData = {
          ...formData,
          birthday: formData.birthday ? new Date(formData.birthday).toISOString() : null
        };
        await onSubmit(submitData);
        playSound('success');
      } catch (error) {
        playSound('error');
      } finally {
        setLoading(false);
      }
    };

    const handleStatusChange = async (newStatus) => {
      try {
        await onUpdateStatus(employee.id, newStatus);
        playSound('success');
      } catch (error) {
        playSound('error');
      }
    };

    const handleDelete = async () => {
      if (window.confirm('Are you sure you want to remove this ninja from the team? This action cannot be undone.')) {
        try {
          await onDelete(employee.id);
          playSound('success');
        } catch (error) {
          playSound('error');
        }
      }
    };

    return (
      <div className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Full Name *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-employee_id">Employee ID *</Label>
              <Input
                id="edit-employee_id"
                value={formData.employee_id}
                onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-email">Email Address *</Label>
            <Input
              id="edit-email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-department">Department *</Label>
              <Input
                id="edit-department"
                value={formData.department}
                onChange={(e) => setFormData({...formData, department: e.target.value})}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-position">Position *</Label>
              <Input
                id="edit-position"
                value={formData.position}
                onChange={(e) => setFormData({...formData, position: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-phone">Phone Number</Label>
              <Input
                id="edit-phone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-birthday">Birthday</Label>
              <Input
                id="edit-birthday"
                type="date"
                value={formData.birthday}
                onChange={(e) => setFormData({...formData, birthday: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div className="space-y-2">
              <Label>Current Status</Label>
              <Badge className={`${
                employee.status === 'active' ? 'bg-green-100 text-green-800' :
                employee.status === 'onboarding' ? 'bg-blue-100 text-blue-800' :
                employee.status === 'exiting' ? 'bg-yellow-100 text-yellow-800' :
                employee.status === 'inactive' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {employee.status === 'onboarding' && '🚀'}
                {employee.status === 'active' && '✅'}
                {employee.status === 'exiting' && '👋'}
                {employee.status === 'exited' && '💼'}
                {employee.status === 'inactive' && '⏸️'}
                {' '}{employee.status}
              </Badge>
            </div>
          </div>

          <div className="flex justify-between pt-4">
            <div className="space-x-2">
              <Button type="button" variant="outline" size="sm" 
                onClick={() => handleStatusChange('onboarding')}
                disabled={employee.status === 'onboarding'}
              >
                🚀 Onboarding
              </Button>
              <Button type="button" variant="outline" size="sm"
                onClick={() => handleStatusChange('active')}
                disabled={employee.status === 'active'}
              >
                ✅ Active
              </Button>
              <Button type="button" variant="outline" size="sm"
                onClick={() => handleStatusChange('exiting')}
                disabled={employee.status === 'exiting'}
              >
                👋 Exiting
              </Button>
              <Button type="button" variant="outline" size="sm"
                onClick={() => handleStatusChange('inactive')}
                disabled={employee.status === 'inactive'}
              >
                ⏸️ Inactive
              </Button>
            </div>
            <Button type="button" variant="destructive" size="sm" onClick={handleDelete}>
              <Trash2 className="w-4 h-4 mr-1" />
              Delete
            </Button>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Updating...
                </div>
              ) : (
                <div className="flex items-center">
                  <Save className="w-4 h-4 mr-2" />
                  Update Ninja
                </div>
              )}
            </Button>
          </div>
        </form>
      </div>
    );
  };

  // Employee Management Component
  const EmployeeManagement = ({ employees, onCreateEmployee, onUpdateEmployee, onUpdateEmployeeStatus, onDeleteEmployee, onImportFromExcel, onAnalyzeEmployee, tasks, onDownloadReport, playSound, token }) => {
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
    const [isExcelDialogOpen, setIsExcelDialogOpen] = useState(false);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editingEmployee, setEditingEmployee] = useState(null);
    const [aiAnalysis, setAiAnalysis] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    const filteredEmployees = employees.filter(emp => {
      const matchesSearch = emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           emp.employee_id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || emp.status === statusFilter;
      return matchesSearch && matchesStatus;
    });

    const getProgressPercentage = (employeeId, taskType) => {
      const employeeTasks = tasks.filter(t => t.employee_id === employeeId && t.task_type === taskType);
      if (employeeTasks.length === 0) return 0;
      const completed = employeeTasks.filter(t => t.status === 'completed').length;
      return Math.round((completed / employeeTasks.length) * 100);
    };

    const handleEditEmployee = (employee) => {
      setEditingEmployee(employee);
      setIsEditDialogOpen(true);
      playSound('click');
    };

    const handleAnalyzeEmployee = async (employeeId) => {
      try {
        playSound('click');
        const analysis = await onAnalyzeEmployee(employeeId);
        setAiAnalysis(analysis);
      } catch (error) {
        console.error('AI analysis failed:', error);
      }
    };

    const downloadTemplate = async () => {
      try {
        playSound('click');
        const response = await axios.get(`${API}/employees/download-template`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });
        
        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        
        // Generate filename with current date
        const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
        link.setAttribute('download', `employee_import_template_${today}.xlsx`);
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        link.remove();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        
        toast.success('Template downloaded successfully!');
      } catch (error) {
        console.error('Template download failed:', error);
        toast.error('Failed to download template. Please try again.');
      }
    };

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Team Ninja Management 🥷
            </h2>
            <p className="text-gray-600 mt-1">Manage your digital warriors</p>
          </div>
          <div className="flex space-x-3">
            <Button variant="outline" onClick={() => onDownloadReport('employees')} className="hover:bg-purple-50">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
            <Button onClick={() => setIsExcelDialogOpen(true)} variant="outline" className="hover:bg-green-50">
              <Upload className="h-4 w-4 mr-2" />
              Import Excel
            </Button>
            <Button 
              onClick={() => downloadTemplate()} 
              variant="outline" 
              className="hover:bg-blue-50"
            >
              <FileText className="h-4 w-4 mr-2" />
              Download Template
            </Button>
            <Button onClick={() => setIsAddDialogOpen(true)} className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
              <UserPlus className="h-4 w-4 mr-2" />
              Add Ninja
            </Button>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="flex space-x-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search ninjas by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="onboarding">🚀 Onboarding</SelectItem>
              <SelectItem value="active">✅ Active</SelectItem>
              <SelectItem value="exiting">👋 Exiting</SelectItem>
              <SelectItem value="exited">💼 Exited</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Employee Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEmployees.map((employee) => (
            <Card key={employee.id} className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-purple-500">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-lg">
                        {employee.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{employee.name}</h3>
                      <p className="text-gray-600 text-sm">{employee.employee_id}</p>
                    </div>
                  </div>
                  <Badge className={`${
                    employee.status === 'active' ? 'bg-green-100 text-green-800' :
                    employee.status === 'onboarding' ? 'bg-blue-100 text-blue-800' :
                    employee.status === 'exiting' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {employee.status === 'onboarding' && '🚀'}
                    {employee.status === 'active' && '✅'}
                    {employee.status === 'exiting' && '👋'}
                    {employee.status === 'exited' && '💼'}
                    {' '}{employee.status}
                  </Badge>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Department:</span>
                    <span className="font-medium">{employee.department}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Position:</span>
                    <span className="font-medium">{employee.position}</span>
                  </div>
                  
                  {employee.status === 'onboarding' && (
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Onboarding Progress:</span>
                        <span className="font-medium">{getProgressPercentage(employee.id, 'onboarding')}%</span>
                      </div>
                      <Progress value={getProgressPercentage(employee.id, 'onboarding')} className="h-2" />
                    </div>
                  )}
                  
                  {employee.status === 'exiting' && (
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Exit Progress:</span>
                        <span className="font-medium">{getProgressPercentage(employee.id, 'exit')}%</span>
                      </div>
                      <Progress value={getProgressPercentage(employee.id, 'exit')} className="h-2" />
                    </div>
                  )}
                </div>
                
                <div className="flex space-x-2 mt-4">
                  <Button size="sm" variant="outline" onClick={() => handleEditEmployee(employee)}>
                    <Edit className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleAnalyzeEmployee(employee.id)}>
                    <Brain className="h-3 w-3 mr-1" />
                    AI Analyze
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredEmployees.length === 0 && (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">No ninjas found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        )}

        {/* Add Employee Dialog */}
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-purple-600" />
                Add New Ninja to the Team
              </DialogTitle>
            </DialogHeader>
            <AddEmployeeForm 
              onSubmit={async (data) => {
                try {
                  await onCreateEmployee(data);
                  setIsAddDialogOpen(false);
                } catch (error) {
                  // Error is already handled in the onCreateEmployee function
                }
              }}
              onCancel={() => setIsAddDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Excel Import Dialog */}
        <Dialog open={isExcelDialogOpen} onOpenChange={setIsExcelDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-green-600" />
                Import Ninjas from Excel
              </DialogTitle>
            </DialogHeader>
            <ExcelImportForm 
              onSubmit={async (file) => {
                try {
                  await onImportFromExcel(file);
                  setIsExcelDialogOpen(false);
                } catch (error) {
                  // Error is already handled in the onImportFromExcel function
                }
              }}
              onCancel={() => setIsExcelDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Edit Employee Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit className="w-5 h-5 text-blue-600" />
                Edit Ninja Profile
              </DialogTitle>
            </DialogHeader>
            {editingEmployee && (
              <EditEmployeeForm 
                employee={editingEmployee}
                onSubmit={async (data) => {
                  try {
                    await onUpdateEmployee(editingEmployee.id, data);
                    setIsEditDialogOpen(false);
                    setEditingEmployee(null);
                  } catch (error) {
                    // Error is already handled in the onUpdateEmployee function
                  }
                }}
                onCancel={() => {
                  setIsEditDialogOpen(false);
                  setEditingEmployee(null);
                }}
                onUpdateStatus={onUpdateEmployeeStatus}
                onDelete={onDeleteEmployee}
              />
            )}
          </DialogContent>
        </Dialog>

        {/* AI Analysis Dialog */}
        {aiAnalysis && (
          <Dialog open={!!aiAnalysis} onOpenChange={() => setAiAnalysis(null)}>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  AI Ninja Analysis
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-purple-900 mb-2">Analysis Results</h4>
                  <pre className="text-sm text-purple-800 whitespace-pre-wrap">{aiAnalysis.analysis}</pre>
                </div>
                {aiAnalysis.suggestions && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Suggestions</h4>
                    <ul className="text-sm text-blue-800 space-y-1">
                      {aiAnalysis.suggestions.map((suggestion, index) => (
                        <li key={index}>• {suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex justify-end">
                  <Button onClick={() => setAiAnalysis(null)}>Close</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
  };

  // Task Management Component  
  const TaskManagement = ({ tasks, employees, onUpdateTask, onDownloadReport }) => {
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    const filteredTasks = tasks.filter(task => {
      const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filter === 'all' || task.status === filter || task.task_type === filter;
      return matchesSearch && matchesFilter;
    });

    const getEmployeeName = (employeeId) => {
      const employee = employees.find(emp => emp.id === employeeId);
      return employee ? employee.name : 'Unknown';
    };

    const groupedTasks = filteredTasks.reduce((acc, task) => {
      const key = task.task_type;
      if (!acc[key]) acc[key] = [];
      acc[key].push(task);
      return acc;
    }, {});

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Mission Control 🎯
            </h2>
            <p className="text-gray-600 mt-1">Track and manage ninja missions</p>
          </div>
          <Button variant="outline" onClick={() => onDownloadReport('tasks')} className="hover:bg-purple-50">
            <Download className="h-4 w-4 mr-2" />
            Export Tasks
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex space-x-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search missions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter tasks" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tasks</SelectItem>
              <SelectItem value="pending">📋 Pending</SelectItem>
              <SelectItem value="in_progress">⏳ In Progress</SelectItem>
              <SelectItem value="completed">✅ Completed</SelectItem>
              <SelectItem value="onboarding">🚀 Onboarding</SelectItem>
              <SelectItem value="exit">👋 Exit</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Tasks by Type */}
        {Object.keys(groupedTasks).map((taskType) => (
          <Card key={taskType} className="overflow-hidden">
            <CardHeader className={`pb-3 ${taskType === 'onboarding' ? 'bg-blue-50' : 'bg-yellow-50'}`}>
              <CardTitle className="text-xl flex items-center gap-2">
                {taskType === 'onboarding' ? '🚀' : '👋'}
                {taskType === 'onboarding' ? 'Onboarding Missions' : 'Exit Missions'}
                <Badge variant="secondary" className="ml-2">
                  {groupedTasks[taskType].length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-100">
                {groupedTasks[taskType].map((task) => (
                  <div key={task.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <Checkbox 
                            checked={task.status === 'completed'}
                            onCheckedChange={(checked) => 
                              onUpdateTask(task.id, checked ? 'completed' : 'pending')
                            }
                          />
                          <div>
                            <h4 className={`font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : ''}`}>
                              {task.title}
                            </h4>
                            <p className="text-sm text-gray-600">
                              Assigned to: {getEmployeeName(task.employee_id)}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge className={`${
                          task.status === 'completed' ? 'bg-green-100 text-green-800' :
                          task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {task.status === 'completed' && '✅'}
                          {task.status === 'in_progress' && '⏳'}
                          {task.status === 'pending' && '📋'}
                          {' '}{task.status}
                        </Badge>
                        {task.due_date && (
                          <span className="text-sm text-gray-500">
                            Due: {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}

        {filteredTasks.length === 0 && (
          <div className="text-center py-12">
            <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">No missions found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    );
  };

  // Navigation Component
  const Navigation = () => (
    <div className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                <Rocket className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Digital Ninjas</h1>
                <p className="text-xs text-gray-500">HR Command Center</p>
              </div>
            </div>
            
            <nav className="flex space-x-1">
              {['dashboard', 'employees', 'tasks'].map((view) => (
                <button
                  key={view}
                  onClick={() => {
                    setCurrentView(view);
                    playSound('click');
                  }}
                  className={`px-3 py-2 rounded-md text-sm font-medium capitalize transition-colors ${
                    currentView === view
                      ? 'bg-purple-100 text-purple-700'
                      : 'text-gray-600 hover:text-purple-600'
                  }`}
                >
                  {view}
                </button>
              ))}
              
              {canAccessAdminPanel(user?.role) && (
                <button
                  onClick={() => {
                    setCurrentView('admin');
                    playSound('click');
                  }}
                  className={`px-3 py-2 rounded-md text-sm font-medium flex items-center gap-1 transition-colors ${
                    currentView === 'admin'
                      ? 'bg-red-100 text-red-700'
                      : 'text-gray-600 hover:text-red-600'
                  }`}
                >
                  <Shield className="w-4 h-4" />
                  Admin
                </button>
              )}
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <Badge className={`${getUserRoleColor(user?.role)} border font-medium`}>
              {getUserRoleIcon(user?.role)}
              <span className="ml-1 capitalize">{user?.role?.replace('_', ' ')}</span>
            </Badge>
            
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700 font-medium">{user?.name}</span>
              <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-blue-400 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                {user?.name?.charAt(0)?.toUpperCase()}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowChangePassword(true)}
                className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                title="Change Password"
              >
                <Key className="w-4 h-4" />
              </button>
              
              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Enhanced Dashboard with role-based features
  const Dashboard = () => (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Welcome back, {user?.name}! 🥷
            </h1>
            <p className="text-purple-100 text-lg">
              {user?.role === 'super_admin' && "You have supreme command over the ninja dojo"}
              {user?.role === 'admin' && "Command your ninja squad with wisdom"}
              {user?.role === 'hr_manager' && "Guide your ninjas through their journey"}
              {user?.role === 'manager' && "Lead your team to victory"}
              {user?.role === 'employee' && "Ready for your next ninja mission"}
            </p>
            {!user?.email_verified && (
              <div className="mt-4 p-3 bg-yellow-100 text-yellow-800 rounded-lg flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm">Please verify your email address to unlock all features</span>
              </div>
            )}
          </div>
          <div className="hidden md:block">
            <div className="w-32 h-32 bg-white/10 rounded-full flex items-center justify-center">
              <Trophy className="w-16 h-16 text-yellow-300" />
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card 
          className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200 shadow-lg cursor-pointer hover:shadow-xl transition-all duration-200 hover:scale-105"
          onClick={() => {
            setCurrentView('employees');
            playSound('click');
          }}
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 text-sm font-medium">Total Ninjas</p>
                <p className="text-3xl font-bold text-blue-900">
                  {Object.values(dashboardStats.employee_stats || {}).reduce((a, b) => a + b, 0)}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-green-50 to-green-100 border-green-200 shadow-lg cursor-pointer hover:shadow-xl transition-all duration-200 hover:scale-105"
          onClick={() => {
            setCurrentView('tasks');
            playSound('click');
            // You can add additional logic here to filter completed tasks if needed
          }}
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-600 text-sm font-medium">Completed Missions</p>
                <p className="text-3xl font-bold text-green-900">
                  {dashboardStats.task_stats?.completed || 0}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 shadow-lg cursor-pointer hover:shadow-xl transition-all duration-200 hover:scale-105"
          onClick={() => {
            setCurrentView('tasks');
            playSound('click');
            // You can add additional logic here to filter active/pending tasks if needed
          }}
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-600 text-sm font-medium">Active Missions</p>
                <p className="text-3xl font-bold text-orange-900">
                  {dashboardStats.task_stats?.pending || 0}
                </p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card 
          className="bg-gradient-to-br from-red-50 to-red-100 border-red-200 shadow-lg cursor-pointer hover:shadow-xl transition-all duration-200 hover:scale-105"
          onClick={() => {
            setCurrentView('tasks');
            playSound('click');
            // You can add additional logic here to filter urgent/overdue tasks if needed
          }}
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-600 text-sm font-medium">Urgent Missions</p>
                <p className="text-3xl font-bold text-red-900">
                  {dashboardStats.task_stats?.overdue || 0}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Events & Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5 text-blue-500" />
              Upcoming Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingEvents.upcoming_events?.slice(0, 5).length > 0 ? (
                upcomingEvents.upcoming_events.slice(0, 5).map((event, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm ${
                      event.type === 'birthday' ? 'bg-gradient-to-br from-pink-400 to-purple-400' : 
                      'bg-gradient-to-br from-green-400 to-blue-400'
                    }`}>
                      {event.type === 'birthday' ? '🎂' : '🎉'}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{event.employee?.name}</p>
                      <p className="text-sm text-gray-600">
                        {event.type === 'birthday' 
                          ? 'Birthday' 
                          : event.years_of_service === 0 
                            ? 'Joining Date Anniversary' 
                            : `${event.years_of_service} Year Anniversary`
                        }
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {event.days_until === 0 ? 'Today!' : 
                         event.days_until === 1 ? 'Tomorrow' : 
                         `${event.days_until} days`}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(event.date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <CalendarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No upcoming events</p>
                  <p className="text-sm">All celebrations up to date!</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-500" />
              Upcoming Tasks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingTasks.upcoming_tasks?.slice(0, 5).length > 0 ? (
                upcomingTasks.upcoming_tasks.slice(0, 5).map((taskItem) => (
                  <div key={taskItem.task?.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-3 h-3 rounded-full ${
                      taskItem.is_overdue ? 'bg-red-500' :
                      taskItem.priority === 'high' ? 'bg-orange-500' :
                      taskItem.priority === 'medium' ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900 text-sm">{taskItem.task?.title}</p>
                      <p className="text-xs text-gray-600">
                        {taskItem.employee?.name || 'Unknown Employee'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${
                        taskItem.is_overdue ? 'text-red-600' : 'text-gray-900'
                      }`}>
                        {taskItem.is_overdue ? `${Math.abs(taskItem.days_until)} days overdue` :
                         taskItem.days_until === 0 ? 'Due today!' :
                         taskItem.days_until === 1 ? 'Due tomorrow' :
                         `Due in ${taskItem.days_until} days`}
                      </p>
                      <Badge className={`text-xs ${
                        taskItem.task?.task_type === 'onboarding' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {taskItem.task?.task_type === 'onboarding' ? '🚀' : '👋'}
                      </Badge>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No upcoming tasks</p>
                  <p className="text-sm">All missions on track!</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // Main render with route handling for invitation acceptance
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing Ninja Command Center...</p>
        </div>
      </div>
    );
  }

  // Handle invitation acceptance route
  if (window.location.pathname === '/accept-invite' || window.location.search.includes('token=')) {
    return <AcceptInvitationForm />;
  }

  if (!user) {
    return <LoginForm 
      loginForm={loginForm}
      onEmailChange={handleEmailChange}
      onPasswordChange={handlePasswordChange}
      onTogglePasswordVisibility={handleTogglePasswordVisibility}
      handleLogin={handleLogin}
      loading={loading}
      onShowForgotPassword={handleShowForgotPassword}
      hasError={loginError}
    />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'employees' && (
          <EmployeeManagement 
            employees={employees}
            onCreateEmployee={createEmployee}
            onUpdateEmployee={updateEmployee}
            onUpdateEmployeeStatus={updateEmployeeStatus}
            onDeleteEmployee={deleteEmployee}
            onImportFromExcel={importFromExcel}
            onAnalyzeEmployee={analyzeEmployee}
            tasks={tasks}
            onDownloadReport={downloadReport}
            playSound={playSound}
            token={token}
          />
        )}
        {currentView === 'tasks' && (
          <TaskManagement 
            tasks={tasks}
            employees={employees}
            onUpdateTask={updateTaskStatus}
            onDownloadReport={downloadReport}
          />
        )}
        {currentView === 'admin' && canAccessAdminPanel(user?.role) && (
          <AdminPanel user={user} token={token} />
        )}
      </main>

      <ChangePasswordForm 
        user={user}
        token={token}
        isOpen={showChangePassword} 
        onClose={() => setShowChangePassword(false)} 
      />

      <Toaster 
        position="top-right" 
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: '8px',
            fontWeight: '500',
          },
          error: {
            duration: 6000,
            style: {
              backgroundColor: '#fee2e2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              fontWeight: '600'
            }
          },
          success: {
            style: {
              backgroundColor: '#ecfdf5',
              border: '1px solid #bbf7d0',
              color: '#059669'
            }
          }
        }}
      />
    </div>
  );
};

export default App;