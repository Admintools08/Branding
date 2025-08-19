import React, { useState, useEffect, useRef } from 'react';
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
  Volume2
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [recentActivities, setRecentActivities] = useState({});
  const [currentView, setCurrentView] = useState('dashboard');
  const [aiInsights, setAiInsights] = useState(null);
  const audioContextRef = useRef(null);

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
        gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.3);
        break;
      default: // click
        oscillator.frequency.setValueAtTime(1000, ctx.currentTime);
        gainNode.gain.setValueAtTime(0.05, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.1);
    }
  };

  // Authentication
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      checkAuth();
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      loadDashboardData();
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardData = async () => {
    try {
      const [statsRes, activitiesRes, employeesRes, tasksRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/recent-activities`),
        axios.get(`${API}/employees`),
        axios.get(`${API}/tasks`)
      ]);
      
      setDashboardStats(statsRes.data);
      setRecentActivities(activitiesRes.data);
      setEmployees(employeesRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      playSound('success');
      toast.success('🥷 Welcome back, Digital Ninja!');
      loadDashboardData();
    } catch (error) {
      playSound('error');
      toast.error('Login failed: ' + (error.response?.data?.detail || 'Invalid credentials'));
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    playSound('notification');
    toast.success('👋 See you later, ninja!');
  };

  const createEmployee = async (employeeData) => {
    try {
      await axios.post(`${API}/employees`, employeeData);
      playSound('success');
      toast.success('🚀 New ninja added to the team!');
      loadDashboardData();
    } catch (error) {
      playSound('error');
      toast.error('Failed to create employee: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to create employee');
    }
  };

  const updateEmployee = async (employeeId, updateData) => {
    try {
      const response = await axios.put(`${API}/employees/${employeeId}/profile`, updateData);
      playSound('success');
      toast.success('✨ Employee profile updated successfully!');
      loadDashboardData();
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('Update failed: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'Failed to update employee');
    }
  };

  const analyzeEmployeeWithAI = async (employeeId) => {
    try {
      const response = await axios.post(`${API}/ai/analyze-employee?employee_id=${employeeId}`);
      playSound('notification');
      toast.success('🧠 AI analysis completed!');
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('AI analysis failed: ' + (error.response?.data?.detail || error.message));
      throw new Error(error.response?.data?.detail || 'AI analysis failed');
    }
  };

  const getAITaskSuggestions = async () => {
    try {
      const response = await axios.get(`${API}/ai/task-suggestions`);
      playSound('notification');
      toast.success('🎯 AI suggestions loaded!');
      return response.data;
    } catch (error) {
      playSound('error');
      toast.error('Failed to get AI suggestions');
      throw new Error(error.response?.data?.detail || 'Failed to get suggestions');
    }
  };

  const updateTaskStatus = async (taskId, status) => {
    try {
      await axios.put(`${API}/tasks/${taskId}`, { status });
      loadDashboardData();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const updateEmployeeStatus = async (employeeId, status, exitDate = null) => {
    try {
      const updateData = { status };
      if (exitDate) updateData.exit_date = exitDate;
      
      await axios.put(`${API}/employees/${employeeId}`, updateData);
      loadDashboardData();
    } catch (error) {
      console.error('Error updating employee:', error);
    }
  };

  const downloadReport = async (reportType) => {
    try {
      const response = await axios.get(`${API}/reports/${reportType}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const importFromExcel = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/employees/import-excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      loadDashboardData();
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to import from Excel');
    }
  };

  const deleteEmployee = async (employeeId) => {
    try {
      await axios.delete(`${API}/employees/${employeeId}`);
      loadDashboardData();
    } catch (error) {
      console.error('Error deleting employee:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-purple-600 font-medium">Loading your workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={login} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Header user={user} onLogout={logout} />
      <div className="flex">
        <Sidebar currentView={currentView} onViewChange={setCurrentView} />
        <main className="flex-1 p-6">
          {currentView === 'dashboard' && (
            <Dashboard 
              stats={dashboardStats} 
              activities={recentActivities}
              employees={employees}
              tasks={tasks}
              onUpdateTask={updateTaskStatus}
            />
          )}
          {currentView === 'employees' && (
            <EmployeeManagement 
              employees={employees}
              onCreateEmployee={createEmployee}
              onUpdateEmployee={updateEmployeeStatus}
              onDeleteEmployee={deleteEmployee}
              onImportFromExcel={importFromExcel}
              tasks={tasks}
              onDownloadReport={downloadReport}
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
        </main>
      </div>
    </div>
  );
};

const LoginForm = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await onLogin(email, password);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-100 via-pink-100 to-orange-100">
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <Card className="w-full max-w-md shadow-2xl border-0 backdrop-blur-sm bg-white/80">
        <CardHeader className="text-center pb-2">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
              <Rocket className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Branding Pioneers
          </CardTitle>
          <p className="text-gray-600 font-medium">Digital Ninjas - HR Portal</p>
          <p className="text-sm text-gray-500 mt-1">Employee Onboarding & Exit Management</p>
        </CardHeader>
        <CardContent className="pt-2">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="h-11 border-gray-200 focus:border-purple-400 focus:ring-purple-400"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="h-11 border-gray-200 focus:border-purple-400 focus:ring-purple-400"
                required
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md border border-red-200">
                {error}
              </div>
            )}
            <Button 
              type="submit" 
              className="w-full h-11 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-lg shadow-lg transform transition hover:scale-[1.02]" 
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Signing in...
                </div>
              ) : (
                <div className="flex items-center">
                  <Zap className="w-4 h-4 mr-2" />
                  Sign In
                </div>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

const Header = ({ user, onLogout }) => (
  <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-purple-100 sticky top-0 z-50">
    <div className="px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
            <Rocket className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Branding Pioneers
            </h1>
            <p className="text-xs text-gray-500">Digital Ninjas</p>
          </div>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-purple-50 to-pink-50 rounded-full">
          <Trophy className="h-4 w-4 text-purple-500" />
          <span className="text-sm font-medium text-purple-600">Level 5 HR Ninja</span>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-gray-900">{user.name}</p>
          <p className="text-xs text-purple-600 capitalize font-medium">{user.role}</p>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onLogout}
          className="hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </div>
  </header>
);

const Sidebar = ({ currentView, onViewChange }) => (
  <aside className="w-64 bg-white/60 backdrop-blur-md shadow-sm h-screen sticky top-0 border-r border-purple-100">
    <nav className="p-4 space-y-2">
      <Button
        variant={currentView === 'dashboard' ? 'default' : 'ghost'}
        className={`w-full justify-start transition-all duration-200 ${
          currentView === 'dashboard' 
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
            : 'hover:bg-purple-50 hover:text-purple-600'
        }`}
        onClick={() => onViewChange('dashboard')}
      >
        <TrendingUp className="h-4 w-4 mr-3" />
        Dashboard
      </Button>
      <Button
        variant={currentView === 'employees' ? 'default' : 'ghost'}
        className={`w-full justify-start transition-all duration-200 ${
          currentView === 'employees' 
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
            : 'hover:bg-purple-50 hover:text-purple-600'
        }`}
        onClick={() => onViewChange('employees')}
      >
        <Users className="h-4 w-4 mr-3" />
        Team Members
      </Button>
      <Button
        variant={currentView === 'tasks' ? 'default' : 'ghost'}
        className={`w-full justify-start transition-all duration-200 ${
          currentView === 'tasks' 
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
            : 'hover:bg-purple-50 hover:text-purple-600'
        }`}
        onClick={() => onViewChange('tasks')}
      >
        <CheckCircle className="h-4 w-4 mr-3" />
        Mission Control
      </Button>
    </nav>
  </aside>
);

const Dashboard = ({ stats, activities, employees, tasks, onUpdateTask }) => {
  const getProgressPercentage = (employeeId, taskType) => {
    const employeeTasks = tasks.filter(t => t.employee_id === employeeId && t.task_type === taskType);
    if (employeeTasks.length === 0) return 0;
    const completed = employeeTasks.filter(t => t.status === 'completed').length;
    return Math.round((completed / employeeTasks.length) * 100);
  };

  const getUpcomingReminders = () => {
    const now = new Date();
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    
    return tasks
      .filter(task => {
        if (!task.due_date || task.status === 'completed') return false;
        const dueDate = new Date(task.due_date);
        return dueDate >= now && dueDate <= nextWeek;
      })
      .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
      .slice(0, 5);
  };

  const activeOnboarding = employees.filter(emp => emp.status === 'onboarding');
  const activeExiting = employees.filter(emp => emp.status === 'exiting');
  const upcomingReminders = getUpcomingReminders();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Mission Control 🚀
          </h2>
          <p className="text-gray-600 mt-1">Your HR command center awaits!</p>
        </div>
        <div className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-orange-100 to-yellow-100 rounded-full">
          <Coffee className="h-5 w-5 text-orange-500" />
          <span className="text-sm font-medium text-orange-700">Ready to ninja some HR tasks?</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white shadow-xl border-0 transform hover:scale-105 transition-transform">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm font-medium">Total Ninjas</p>
                <p className="text-3xl font-bold">
                  {Object.values(stats.employee_stats || {}).reduce((a, b) => a + b, 0)}
                </p>
                <p className="text-purple-200 text-xs mt-1">Digital warriors strong</p>
              </div>
              <Users className="h-12 w-12 text-purple-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-500 to-pink-600 text-white shadow-xl border-0 transform hover:scale-105 transition-transform">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-pink-100 text-sm font-medium">New Recruits</p>
                <p className="text-3xl font-bold">
                  {stats.employee_stats?.onboarding || 0}
                </p>
                <p className="text-pink-200 text-xs mt-1">Future legends</p>
              </div>
              <UserPlus className="h-12 w-12 text-pink-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white shadow-xl border-0 transform hover:scale-105 transition-transform">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm font-medium">Active Missions</p>
                <p className="text-3xl font-bold">
                  {stats.task_stats?.pending || 0}
                </p>
                <p className="text-orange-200 text-xs mt-1">Tasks to conquer</p>
              </div>
              <Target className="h-12 w-12 text-orange-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white shadow-xl border-0 transform hover:scale-105 transition-transform">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm font-medium">Victories</p>
                <p className="text-3xl font-bold">
                  {stats.task_stats?.completed || 0}
                </p>
                <p className="text-green-200 text-xs mt-1">Goals achieved</p>
              </div>
              <Trophy className="h-12 w-12 text-green-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Onboarding */}
        <Card className="shadow-lg border-0 bg-gradient-to-br from-blue-50 to-indigo-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-blue-700">
              <Rocket className="h-5 w-5 mr-2 text-blue-500" />
              New Ninja Training 🥷
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeOnboarding.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <UserPlus className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No new ninjas in training</p>
                  <p className="text-sm">Add some future legends!</p>
                </div>
              ) : (
                activeOnboarding.map(employee => (
                  <div key={employee.id} className="flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-blue-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full">
                        <Users className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{employee.name}</p>
                        <p className="text-sm text-gray-600">{employee.department}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-2 mb-1">
                        <Star className="h-4 w-4 text-yellow-500" />
                        <p className="text-sm font-bold text-blue-600">
                          {getProgressPercentage(employee.id, 'onboarding')}%
                        </p>
                      </div>
                      <Progress 
                        value={getProgressPercentage(employee.id, 'onboarding')} 
                        className="w-24 h-3"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Active Exits */}
        <Card className="shadow-lg border-0 bg-gradient-to-br from-amber-50 to-orange-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-amber-700">
              <Gift className="h-5 w-5 mr-2 text-amber-500" />
              Farewell Journey 👋
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeExiting.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Coffee className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No farewells in progress</p>
                  <p className="text-sm">All ninjas staying strong!</p>
                </div>
              ) : (
                activeExiting.map(employee => (
                  <div key={employee.id} className="flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm rounded-xl shadow-sm border border-amber-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full">
                        <Users className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{employee.name}</p>
                        <p className="text-sm text-gray-600">{employee.department}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-2 mb-1">
                        <Trophy className="h-4 w-4 text-amber-500" />
                        <p className="text-sm font-bold text-amber-600">
                          {getProgressPercentage(employee.id, 'exit')}%
                        </p>
                      </div>
                      <Progress 
                        value={getProgressPercentage(employee.id, 'exit')} 
                        className="w-24 h-3"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Reminders */}
      <Card className="shadow-lg border-0 bg-gradient-to-br from-green-50 to-emerald-50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center text-green-700">
            <Bell className="h-5 w-5 mr-2 text-green-500" />
            Mission Alerts 🔔
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {upcomingReminders.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <PartyPopper className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>All caught up!</p>
                <p className="text-sm">No urgent missions ahead</p>
              </div>
            ) : (
              upcomingReminders.map(task => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-white/80 backdrop-blur-sm rounded-lg border border-green-100">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 text-sm">{task.title}</p>
                    <p className="text-xs text-gray-600">
                      {employees.find(e => e.id === task.employee_id)?.name || 'Unknown Ninja'} • 
                      Due: {new Date(task.due_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant={task.task_type === 'onboarding' ? 'secondary' : 'outline'}
                      className="text-xs"
                    >
                      {task.task_type}
                    </Badge>
                    <Clock className="h-4 w-4 text-orange-500" />
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const EmployeeManagement = ({ employees, onCreateEmployee, onUpdateEmployee, onDeleteEmployee, onImportFromExcel, tasks, onDownloadReport }) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isExcelDialogOpen, setIsExcelDialogOpen] = useState(false);
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
            Export PDF
          </Button>
          <Dialog open={isExcelDialogOpen} onOpenChange={setIsExcelDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="hover:bg-green-50">
                <Upload className="h-4 w-4 mr-2" />
                Import Excel
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import Team Members from Excel</DialogTitle>
              </DialogHeader>
              <ExcelImportForm 
                onSubmit={(file) => {
                  onImportFromExcel(file);
                  setIsExcelDialogOpen(false);
                }}
              />
            </DialogContent>
          </Dialog>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg">
                <Plus className="h-4 w-4 mr-2" />
                Add Ninja
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Welcome a New Digital Ninja!</DialogTitle>
              </DialogHeader>
              <AddEmployeeForm 
                onSubmit={(data) => {
                  onCreateEmployee(data);
                  setIsAddDialogOpen(false);
                }}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search ninjas by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 border-purple-200 focus:border-purple-400 focus:ring-purple-400"
            />
          </div>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48 border-purple-200">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Ninjas</SelectItem>
            <SelectItem value="onboarding">New Recruits</SelectItem>
            <SelectItem value="active">Active Warriors</SelectItem>
            <SelectItem value="exiting">Farewell Journey</SelectItem>
            <SelectItem value="exited">Alumni</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Employee List */}
      <div className="grid gap-4">
        {filteredEmployees.map(employee => (
          <Card key={employee.id} className="shadow-lg border-0 bg-gradient-to-r from-white to-purple-50/30 hover:shadow-xl transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
                      <Users className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{employee.name}</h3>
                      <p className="text-sm text-gray-600">Ninja ID: {employee.employee_id}</p>
                    </div>
                    <Badge 
                      variant={employee.status === 'active' ? 'default' : 'secondary'}
                      className={`capitalize font-semibold ${
                        employee.status === 'active' ? 'bg-green-500' :
                        employee.status === 'onboarding' ? 'bg-blue-500' :
                        employee.status === 'exiting' ? 'bg-orange-500' : 'bg-gray-500'
                      } text-white`}
                    >
                      {employee.status === 'onboarding' ? '🚀 Training' :
                       employee.status === 'active' ? '⚡ Active' :
                       employee.status === 'exiting' ? '👋 Farewell' : '🎓 Alumni'}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Department</p>
                      <p className="text-sm font-semibold text-gray-900">{employee.department}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Squad Leader</p>
                      <p className="text-sm font-semibold text-gray-900">{employee.manager}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Join Date</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {new Date(employee.start_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-medium">Mission Progress</p>
                      <div className="flex items-center space-x-2">
                        <Progress 
                          value={getProgressPercentage(employee.id, employee.status === 'onboarding' ? 'onboarding' : 'exit')} 
                          className="flex-1 h-3"
                        />
                        <span className="text-sm font-bold text-purple-600">
                          {getProgressPercentage(employee.id, employee.status === 'onboarding' ? 'onboarding' : 'exit')}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col space-y-2">
                  <EmployeeActions 
                    employee={employee} 
                    onUpdateStatus={onUpdateEmployee}
                    onDelete={onDeleteEmployee}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

const ExcelImportForm = ({ onSubmit }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setLoading(true);
    try {
      const importResult = await onSubmit(file);
      setResult(importResult);
      if (importResult.errors.length === 0) {
        setTimeout(() => {
          // Close dialog after showing success
          setFile(null);
          setResult(null);
        }, 3000);
      }
    } catch (error) {
      setResult({
        message: error.message,
        imported_count: 0,
        total_rows: 0,
        errors: [error.message]
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {!result && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="border-2 border-dashed border-purple-300 rounded-lg p-6 text-center hover:border-purple-400 transition-colors">
            <Upload className="h-12 w-12 mx-auto text-purple-400 mb-3" />
            <Label htmlFor="excel-file" className="cursor-pointer">
              <span className="text-purple-600 font-semibold">Click to upload</span> or drag and drop
            </Label>
            <Input
              id="excel-file"
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <p className="text-xs text-gray-500 mt-2">Excel (.xlsx, .xls) or CSV files only</p>
            {file && (
              <div className="mt-3 p-2 bg-green-50 rounded-md">
                <p className="text-sm text-green-600 font-medium">✓ {file.name} selected</p>
                <p className="text-xs text-green-500">Ready to import ninja data!</p>
              </div>
            )}
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2 flex items-center">
              <FileText className="h-4 w-4 mr-2" />
              Expected Excel Format:
            </h4>
            <div className="text-sm text-blue-800">
              <p className="font-mono bg-white/50 p-2 rounded text-xs">
                Name | Employee ID | Email | Department | Manager | Start Date
              </p>
              <p className="text-xs mt-2 text-blue-600">
                📋 Example: John Doe | NIN001 | john@brandingpioneers.com | Engineering | Jane Smith | 2024-01-15
              </p>
            </div>
          </div>

          <Button type="submit" className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600" disabled={!file || loading}>
            {loading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Processing Excel Magic...
              </div>
            ) : (
              <div className="flex items-center">
                <Upload className="w-4 h-4 mr-2" />
                Import Digital Ninjas 🥷
              </div>
            )}
          </Button>
        </form>
      )}

      {result && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg ${result.errors.length === 0 ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'} border`}>
            <div className="flex items-center mb-2">
              {result.errors.length === 0 ? (
                <Trophy className="h-5 w-5 text-green-500 mr-2" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
              )}
              <h4 className={`font-semibold ${result.errors.length === 0 ? 'text-green-900' : 'text-yellow-900'}`}>
                Import Results
              </h4>
            </div>
            <p className={`text-sm ${result.errors.length === 0 ? 'text-green-800' : 'text-yellow-800'}`}>
              {result.message}
            </p>
            <div className="mt-2 text-xs">
              <span className="inline-block bg-white/50 px-2 py-1 rounded mr-2">
                ✅ Imported: {result.imported_count}
              </span>
              <span className="inline-block bg-white/50 px-2 py-1 rounded">
                📊 Total: {result.total_rows}
              </span>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h5 className="font-semibold text-red-900 mb-2 flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Issues Found:
              </h5>
              <div className="max-h-32 overflow-y-auto">
                {result.errors.map((error, index) => (
                  <p key={index} className="text-xs text-red-700 mb-1">• {error}</p>
                ))}
              </div>
            </div>
          )}

          <Button 
            onClick={() => {
              setResult(null);
              setFile(null);
            }}
            className="w-full"
            variant="outline"
          >
            Import More Ninjas
          </Button>
        </div>
      )}
    </div>
  );
};

const AddEmployeeForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    employee_id: '',
    email: '',
    department: '',
    manager: '',
    start_date: new Date(),
    status: 'onboarding'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Ninja Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g., Alex the Code Warrior"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
        <div>
          <Label htmlFor="employee_id">Ninja ID *</Label>
          <Input
            id="employee_id"
            value={formData.employee_id}
            onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
            placeholder="e.g., NIN001"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>
      
      <div>
        <Label htmlFor="email">Email Address *</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          placeholder="ninja@brandingpioneers.com"
          className="border-purple-200 focus:border-purple-400"
          required
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="department">Department *</Label>
          <Select value={formData.department} onValueChange={(value) => setFormData({...formData, department: value})}>
            <SelectTrigger className="border-purple-200">
              <SelectValue placeholder="Choose squad" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Engineering">🔧 Engineering</SelectItem>
              <SelectItem value="Design">🎨 Design</SelectItem>
              <SelectItem value="Marketing">📢 Marketing</SelectItem>
              <SelectItem value="Sales">💼 Sales</SelectItem>
              <SelectItem value="HR">👥 HR</SelectItem>
              <SelectItem value="Finance">💰 Finance</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="manager">Squad Leader *</Label>
          <Input
            id="manager"
            value={formData.manager}
            onChange={(e) => setFormData({...formData, manager: e.target.value})}
            placeholder="e.g., Senior Ninja Master"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>

      <Button type="submit" className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600">
        <UserPlus className="w-4 h-4 mr-2" />
        Welcome New Ninja!
      </Button>
    </form>
  );
};

const EmployeeActions = ({ employee, onUpdateStatus, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = () => {
    onDelete(employee.id);
    setShowDeleteConfirm(false);
  };

  return (
    <div className="flex flex-col space-y-2">
      {employee.status === 'onboarding' && (
        <Button
          size="sm"
          onClick={() => onUpdateStatus(employee.id, 'active')}
          className="bg-green-500 hover:bg-green-600 text-white"
        >
          <Zap className="h-3 w-3 mr-1" />
          Activate
        </Button>
      )}
      {employee.status === 'active' && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onUpdateStatus(employee.id, 'exiting', new Date())}
          className="border-orange-300 text-orange-600 hover:bg-orange-50"
        >
          <Gift className="h-3 w-3 mr-1" />
          Start Farewell
        </Button>
      )}
      {employee.status === 'exiting' && (
        <Button
          size="sm"
          onClick={() => onUpdateStatus(employee.id, 'exited')}
          className="bg-gray-500 hover:bg-gray-600 text-white"
        >
          <Trophy className="h-3 w-3 mr-1" />
          Complete Exit
        </Button>
      )}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogTrigger asChild>
          <Button size="sm" variant="outline" className="border-red-300 text-red-600 hover:bg-red-50">
            <Trash2 className="h-3 w-3 mr-1" />
            Remove
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Ninja?</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>Are you sure you want to remove <strong>{employee.name}</strong> from the team?</p>
            <div className="flex space-x-2">
              <Button variant="outline" onClick={() => setShowDeleteConfirm(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleDelete} className="flex-1 bg-red-500 hover:bg-red-600">
                Remove
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const TaskManagement = ({ tasks, employees, onUpdateTask, onDownloadReport }) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || task.status === filter || task.task_type === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Mission Control Center 🎯
          </h2>
          <p className="text-gray-600 mt-1">Track all ninja missions and quests</p>
        </div>
        <Button variant="outline" onClick={() => onDownloadReport('tasks')} className="hover:bg-purple-50">
          <FileText className="h-4 w-4 mr-2" />
          Export Missions PDF
        </Button>
      </div>

      {/* Search and Filter */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search missions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 border-purple-200 focus:border-purple-400 focus:ring-purple-400"
            />
          </div>
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-48 border-purple-200">
            <SelectValue placeholder="Filter missions" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Missions</SelectItem>
            <SelectItem value="pending">🎯 Active</SelectItem>
            <SelectItem value="completed">✅ Completed</SelectItem>
            <SelectItem value="onboarding">🚀 Training</SelectItem>
            <SelectItem value="exit">👋 Farewell</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Task List */}
      <div className="space-y-4">
        {filteredTasks.map(task => (
          <Card key={task.id} className="shadow-lg border-0 bg-gradient-to-r from-white to-purple-50/20 hover:shadow-xl transition-all duration-300">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <Checkbox
                      checked={task.status === 'completed'}
                      onCheckedChange={(checked) => 
                        onUpdateTask(task.id, checked ? 'completed' : 'pending')
                      }
                      className="w-5 h-5 border-2 border-purple-300 text-purple-600"
                    />
                    {task.status === 'completed' && (
                      <div className="absolute -top-1 -right-1">
                        <Star className="h-3 w-3 text-yellow-500 fill-current" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className={`font-semibold ${task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                      {task.title}
                    </h4>
                    <p className="text-sm text-gray-600">{task.description}</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <div className="flex items-center space-x-1">
                        <Users className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {employees.find(e => e.id === task.employee_id)?.name || 'Unknown Ninja'}
                        </span>
                      </div>
                      <Badge 
                        variant={task.task_type === 'onboarding' ? 'secondary' : 'outline'}
                        className={`text-xs ${
                          task.task_type === 'onboarding' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                        }`}
                      >
                        {task.task_type === 'onboarding' ? '🚀 Training' : '👋 Farewell'}
                      </Badge>
                      {task.due_date && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-3 w-3 text-gray-400" />
                          <span className="text-xs text-gray-500">
                            Due: {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge 
                    variant={task.status === 'completed' ? 'default' : 'secondary'}
                    className={`capitalize font-semibold ${
                      task.status === 'completed' 
                        ? 'bg-green-500 text-white' 
                        : 'bg-orange-100 text-orange-700'
                    }`}
                  >
                    {task.status === 'completed' ? '🏆 Done' : '⚡ Active'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default App;