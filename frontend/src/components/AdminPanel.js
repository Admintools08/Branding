import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import { 
  Users, 
  UserPlus, 
  Shield, 
  Settings, 
  Activity, 
  Mail, 
  Eye, 
  Edit, 
  Trash2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Crown,
  Key
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = ({ user, token }) => {
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showBulkNotificationDialog, setShowBulkNotificationDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'employee',
    message: ''
  });

  const [bulkNotificationForm, setBulkNotificationForm] = useState({
    recipient_emails: [],
    subject: '',
    message: ''
  });

  const roleColors = {
    super_admin: 'bg-purple-100 text-purple-800 border-purple-200',
    admin: 'bg-red-100 text-red-800 border-red-200',
    hr_manager: 'bg-blue-100 text-blue-800 border-blue-200',
    manager: 'bg-green-100 text-green-800 border-green-200',
    employee: 'bg-gray-100 text-gray-800 border-gray-200'
  };

  const roleIcons = {
    super_admin: Crown,
    admin: Shield,
    hr_manager: Users,
    manager: Settings,
    employee: Users
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const [usersRes, auditRes] = await Promise.all([
        axios.get(`${API}/admin/users`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/audit-logs?limit=20`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setUsers(usersRes.data);
      setAuditLogs(auditRes.data);
    } catch (error) {
      console.error('Error loading admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/auth/invite-user`, inviteForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('User invitation sent successfully!');
      setShowInviteDialog(false);
      setInviteForm({ email: '', role: 'employee', message: '' });
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send invitation');
    }
  };

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/role`, newRole, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      toast.success('User role updated successfully!');
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update user role');
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to delete user "${userName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('User deleted successfully!');
      loadAdminData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleBulkNotification = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/bulk-notification`, bulkNotificationForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Bulk notification sent successfully!');
      setShowBulkNotificationDialog(false);
      setBulkNotificationForm({ recipient_emails: [], subject: '', message: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send bulk notification');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'login': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'invite_user': return <UserPlus className="w-4 h-4 text-blue-500" />;
      case 'update_user_role': return <Shield className="w-4 h-4 text-purple-500" />;
      case 'delete_user': return <Trash2 className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-600 mt-2">Manage users, permissions, and system settings</p>
        </div>
        <div className="flex gap-3">
          <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                <UserPlus className="w-4 h-4 mr-2" />
                Invite User
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Invite New User</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleInviteUser} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="user@company.com"
                    value={inviteForm.email}
                    onChange={(e) => setInviteForm({...inviteForm, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Select value={inviteForm.role} onValueChange={(value) => setInviteForm({...inviteForm, role: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="employee">Employee</SelectItem>
                      <SelectItem value="manager">Manager</SelectItem>
                      <SelectItem value="hr_manager">HR Manager</SelectItem>
                      {user?.role === 'super_admin' && (
                        <SelectItem value="admin">Admin</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="message">Personal Message (Optional)</Label>
                  <Textarea
                    id="message"
                    placeholder="Welcome to the team!"
                    value={inviteForm.message}
                    onChange={(e) => setInviteForm({...inviteForm, message: e.target.value})}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">Send Invitation</Button>
                  <Button type="button" variant="outline" onClick={() => setShowInviteDialog(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={showBulkNotificationDialog} onOpenChange={setShowBulkNotificationDialog}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Mail className="w-4 h-4 mr-2" />
                Bulk Notify
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Send Bulk Notification</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleBulkNotification} className="space-y-4">
                <div>
                  <Label htmlFor="emails">Recipient Emails (comma-separated)</Label>
                  <Textarea
                    id="emails"
                    placeholder="user1@company.com, user2@company.com"
                    value={bulkNotificationForm.recipient_emails.join(', ')}
                    onChange={(e) => setBulkNotificationForm({
                      ...bulkNotificationForm, 
                      recipient_emails: e.target.value.split(',').map(email => email.trim()).filter(Boolean)
                    })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="subject">Subject</Label>
                  <Input
                    id="subject"
                    placeholder="Important Team Update"
                    value={bulkNotificationForm.subject}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, subject: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="message">Message</Label>
                  <Textarea
                    id="message"
                    placeholder="Your message here..."
                    value={bulkNotificationForm.message}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, message: e.target.value})}
                    required
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">Send Notification</Button>
                  <Button type="button" variant="outline" onClick={() => setShowBulkNotificationDialog(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="users" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
          <TabsTrigger value="system">System Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                System Users ({users.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {users.map((userData) => {
                  const RoleIcon = roleIcons[userData.role] || Users;
                  return (
                    <div key={userData.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-400 to-blue-400 flex items-center justify-center text-white font-semibold">
                          {userData.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold">{userData.name}</div>
                          <div className="text-sm text-gray-600">{userData.email}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={roleColors[userData.role]}>
                              <RoleIcon className="w-3 h-3 mr-1" />
                              {userData.role.replace('_', ' ').toUpperCase()}
                            </Badge>
                            {userData.email_verified ? (
                              <Badge variant="outline" className="text-green-600 border-green-200">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Verified
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-yellow-600 border-yellow-200">
                                <Clock className="w-3 h-3 mr-1" />
                                Pending
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {userData.id !== user.id && (
                          <>
                            <Select 
                              value={userData.role} 
                              onValueChange={(newRole) => handleUpdateUserRole(userData.id, newRole)}
                            >
                              <SelectTrigger className="w-32">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="employee">Employee</SelectItem>
                                <SelectItem value="manager">Manager</SelectItem>
                                <SelectItem value="hr_manager">HR Manager</SelectItem>
                                {user?.role === 'super_admin' && (
                                  <>
                                    <SelectItem value="admin">Admin</SelectItem>
                                    <SelectItem value="super_admin">Super Admin</SelectItem>
                                  </>
                                )}
                              </SelectContent>
                            </Select>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteUser(userData.id, userData.name)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {auditLogs.map((log, index) => (
                  <div key={index} className="flex items-center gap-4 p-3 border rounded-lg">
                    {getActionIcon(log.action)}
                    <div className="flex-1">
                      <div className="font-medium capitalize">
                        {log.action.replace('_', ' ')} on {log.resource}
                      </div>
                      <div className="text-sm text-gray-600">
                        User: {log.user_id} • {formatDate(log.timestamp)}
                      </div>
                      {log.details && (
                        <div className="text-xs text-gray-500 mt-1">
                          {JSON.stringify(log.details)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                System Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Email Settings</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Configure email notifications and delivery settings
                  </p>
                  <Button variant="outline" className="mr-2">
                    <Settings className="w-4 h-4 mr-2" />
                    Configure SMTP
                  </Button>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Security Settings</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Manage password policies and authentication settings
                  </p>
                  <Button variant="outline" className="mr-2">
                    <Key className="w-4 h-4 mr-2" />
                    Security Policy
                  </Button>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Data Export</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Export system data for backup or analysis
                  </p>
                  <Button variant="outline" className="mr-2">
                    <Activity className="w-4 h-4 mr-2" />
                    Export Audit Logs
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminPanel;