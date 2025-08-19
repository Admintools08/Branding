import React, { useState, useEffect } from 'react';
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
  FileText
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
      loadDashboardData();
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const createEmployee = async (employeeData) => {
    try {
      await axios.post(`${API}/employees`, employeeData);
      loadDashboardData();
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create employee');
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={login} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
              tasks={tasks}
            />
          )}
          {currentView === 'tasks' && (
            <TaskManagement 
              tasks={tasks}
              employees={employees}
              onUpdateTask={updateTaskStatus}
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-teal-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">HR Portal</CardTitle>
          <p className="text-gray-600">Employee Onboarding & Exit Management</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@company.com"
                required
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Demo Account:</strong><br />
              Email: admin@company.com<br />
              Password: admin123
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const Header = ({ user, onLogout }) => (
  <header className="bg-white shadow-sm border-b">
    <div className="px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Users className="h-8 w-8 text-emerald-600" />
          <h1 className="text-2xl font-bold text-gray-900">HR Portal</h1>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{user.name}</p>
          <p className="text-xs text-gray-500 capitalize">{user.role}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onLogout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </div>
  </header>
);

const Sidebar = ({ currentView, onViewChange }) => (
  <aside className="w-64 bg-white shadow-sm h-screen sticky top-0">
    <nav className="p-4 space-y-2">
      <Button
        variant={currentView === 'dashboard' ? 'default' : 'ghost'}
        className="w-full justify-start"
        onClick={() => onViewChange('dashboard')}
      >
        <TrendingUp className="h-4 w-4 mr-2" />
        Dashboard
      </Button>
      <Button
        variant={currentView === 'employees' ? 'default' : 'ghost'}
        className="w-full justify-start"
        onClick={() => onViewChange('employees')}
      >
        <Users className="h-4 w-4 mr-2" />
        Employees
      </Button>
      <Button
        variant={currentView === 'tasks' ? 'default' : 'ghost'}
        className="w-full justify-start"
        onClick={() => onViewChange('tasks')}
      >
        <CheckCircle className="h-4 w-4 mr-2" />
        Tasks
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Object.values(stats.employee_stats || {}).reduce((a, b) => a + b, 0)}
                </p>
              </div>
              <Users className="h-8 w-8 text-emerald-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Onboarding</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.employee_stats?.onboarding || 0}
                </p>
              </div>
              <UserPlus className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Tasks</p>
                <p className="text-2xl font-bold text-orange-600">
                  {stats.task_stats?.pending || 0}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overdue Tasks</p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.task_stats?.overdue || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Onboarding</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {employees
                .filter(emp => emp.status === 'onboarding')
                .slice(0, 5)
                .map(employee => (
                  <div key={employee.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{employee.name}</p>
                      <p className="text-sm text-gray-600">{employee.department}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {getProgressPercentage(employee.id, 'onboarding')}%
                      </p>
                      <Progress 
                        value={getProgressPercentage(employee.id, 'onboarding')} 
                        className="w-24 h-2 mt-1"
                      />
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {tasks
                .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
                .slice(0, 5)
                .map(task => (
                  <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 text-sm">{task.title}</p>
                      <p className="text-xs text-gray-600">
                        {employees.find(e => e.id === task.employee_id)?.name || 'Unknown'}
                      </p>
                    </div>
                    <Badge 
                      variant={task.status === 'completed' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {task.status}
                    </Badge>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const EmployeeManagement = ({ employees, onCreateEmployee, onUpdateEmployee, tasks }) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
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
        <h2 className="text-3xl font-bold text-gray-900">Employee Management</h2>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Employee
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Employee</DialogTitle>
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

      {/* Search and Filter */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search employees..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="onboarding">Onboarding</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="exiting">Exiting</SelectItem>
            <SelectItem value="exited">Exited</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Employee List */}
      <div className="grid gap-4">
        {filteredEmployees.map(employee => (
          <Card key={employee.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{employee.name}</h3>
                      <p className="text-sm text-gray-600">ID: {employee.employee_id}</p>
                    </div>
                    <Badge 
                      variant={employee.status === 'active' ? 'default' : 'secondary'}
                      className="capitalize"
                    >
                      {employee.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-xs text-gray-500">Department</p>
                      <p className="text-sm font-medium text-gray-900">{employee.department}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Manager</p>
                      <p className="text-sm font-medium text-gray-900">{employee.manager}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Start Date</p>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(employee.start_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Progress</p>
                      <div className="flex items-center space-x-2">
                        <Progress 
                          value={getProgressPercentage(employee.id, employee.status === 'onboarding' ? 'onboarding' : 'exit')} 
                          className="flex-1 h-2"
                        />
                        <span className="text-xs font-medium">
                          {getProgressPercentage(employee.id, employee.status === 'onboarding' ? 'onboarding' : 'exit')}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <EmployeeActions 
                  employee={employee} 
                  onUpdateStatus={onUpdateEmployee}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
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
          <Label htmlFor="name">Full Name</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
        </div>
        <div>
          <Label htmlFor="employee_id">Employee ID</Label>
          <Input
            id="employee_id"
            value={formData.employee_id}
            onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
            required
          />
        </div>
      </div>
      
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="department">Department</Label>
          <Input
            id="department"
            value={formData.department}
            onChange={(e) => setFormData({...formData, department: e.target.value})}
            required
          />
        </div>
        <div>
          <Label htmlFor="manager">Manager</Label>
          <Input
            id="manager"
            value={formData.manager}
            onChange={(e) => setFormData({...formData, manager: e.target.value})}
            required
          />
        </div>
      </div>

      <Button type="submit" className="w-full">Add Employee</Button>
    </form>
  );
};

const EmployeeActions = ({ employee, onUpdateStatus }) => (
  <div className="flex space-x-2">
    {employee.status === 'onboarding' && (
      <Button
        size="sm"
        onClick={() => onUpdateStatus(employee.id, 'active')}
      >
        Mark Active
      </Button>
    )}
    {employee.status === 'active' && (
      <Button
        size="sm"
        variant="outline"
        onClick={() => onUpdateStatus(employee.id, 'exiting', new Date())}
      >
        Start Exit
      </Button>
    )}
    {employee.status === 'exiting' && (
      <Button
        size="sm"
        onClick={() => onUpdateStatus(employee.id, 'exited')}
      >
        Mark Exited
      </Button>
    )}
  </div>
);

const TaskManagement = ({ tasks, employees, onUpdateTask }) => {
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
        <h2 className="text-3xl font-bold text-gray-900">Task Management</h2>
      </div>

      {/* Search and Filter */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter tasks" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tasks</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="onboarding">Onboarding</SelectItem>
            <SelectItem value="exit">Exit</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Task List */}
      <div className="space-y-4">
        {filteredTasks.map(task => (
          <Card key={task.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Checkbox
                    checked={task.status === 'completed'}
                    onCheckedChange={(checked) => 
                      onUpdateTask(task.id, checked ? 'completed' : 'pending')
                    }
                  />
                  <div>
                    <h4 className="font-medium text-gray-900">{task.title}</h4>
                    <p className="text-sm text-gray-600">{task.description}</p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-500">
                        {employees.find(e => e.id === task.employee_id)?.name || 'Unknown'}
                      </span>
                      <Badge 
                        variant={task.task_type === 'onboarding' ? 'secondary' : 'outline'}
                        className="text-xs"
                      >
                        {task.task_type}
                      </Badge>
                      {task.due_date && (
                        <span className="text-xs text-gray-500">
                          Due: {new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <Badge 
                  variant={task.status === 'completed' ? 'default' : 'secondary'}
                  className="capitalize"
                >
                  {task.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default App;