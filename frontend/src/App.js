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

const App = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [recentActivities, setRecentActivities] = useState({});
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
      const [employeesRes, tasksRes, statsRes, activitiesRes] = await Promise.all([
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
        })
      ]);

      setEmployees(employeesRes.data);
      setTasks(tasksRes.data);
      setDashboardStats(statsRes.data);
      setRecentActivities(activitiesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
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
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

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

  // Login Component
  const LoginForm = () => (
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
                  onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                  className="pl-10 border-gray-300 focus:border-purple-500"
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
                  onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                  className="pl-10 pr-10 border-gray-300 focus:border-purple-500"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  onClick={() => setLoginForm({...loginForm, showPassword: !loginForm.showPassword})}
                >
                  {loginForm.showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <button
                type="button"
                onClick={() => setShowForgotPassword(true)}
                className="text-purple-600 hover:text-purple-800 font-medium"
              >
                Forgot Password?
              </button>
            </div>

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
        isOpen={showForgotPassword} 
        onClose={() => setShowForgotPassword(false)} 
      />
    </div>
  );

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
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200 shadow-lg">
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

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200 shadow-lg">
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

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 shadow-lg">
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

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200 shadow-lg">
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

      {/* Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-blue-500" />
              New Ninjas Joining
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.recent_employees?.slice(0, 5).map((employee) => (
                <div key={employee.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-blue-400 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                    {employee.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{employee.name}</p>
                    <p className="text-sm text-gray-600">{employee.department}</p>
                  </div>
                  <Badge className={`${
                    employee.status === 'active' ? 'bg-green-100 text-green-800' :
                    employee.status === 'onboarding' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {employee.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-500" />
              Latest Mission Updates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.recent_tasks?.slice(0, 5).map((task) => (
                <div key={task.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-3 h-3 rounded-full ${
                    task.status === 'completed' ? 'bg-green-500' :
                    task.status === 'pending' ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}></div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 text-sm">{task.title}</p>
                    <p className="text-xs text-gray-600">
                      {employees.find(e => e.id === task.employee_id)?.name || 'Unknown Ninja'}
                    </p>
                  </div>
                  <Badge className={`text-xs ${
                    task.task_type === 'onboarding' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                  }`}>
                    {task.task_type === 'onboarding' ? '🚀' : '👋'}
                  </Badge>
                </div>
              ))}
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
    return <LoginForm />;
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

      <Toaster position="top-right" />
    </div>
  );
};

export default App;