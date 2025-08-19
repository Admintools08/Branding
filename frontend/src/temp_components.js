const EmployeeManagement = ({ employees, onCreateEmployee, onUpdateEmployee, onUpdateEmployeeStatus, onDeleteEmployee, onImportFromExcel, onAnalyzeEmployee, tasks, onDownloadReport, playSound }) => {
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
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleEditEmployee(employee)}
                    className="border-blue-300 text-blue-600 hover:bg-blue-50"
                  >
                    <Edit className="h-3 w-3 mr-1" />
                    Edit Profile
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleAnalyzeEmployee(employee.id)}
                    className="border-purple-300 text-purple-600 hover:bg-purple-50"
                  >
                    <Brain className="h-3 w-3 mr-1" />
                    AI Insights
                  </Button>
                  <EmployeeActions 
                    employee={employee} 
                    onUpdateStatus={onUpdateEmployeeStatus}
                    onDelete={onDeleteEmployee}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Employee Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Employee Profile ✏️</DialogTitle>
          </DialogHeader>
          {editingEmployee && (
            <EmployeeEditForm 
              employee={editingEmployee}
              onSubmit={async (data) => {
                try {
                  await onUpdateEmployee(editingEmployee.id, data);
                  setIsEditDialogOpen(false);
                  setEditingEmployee(null);
                } catch (error) {
                  console.error('Update failed:', error);
                }
              }}
              onCancel={() => {
                setIsEditDialogOpen(false);
                setEditingEmployee(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* AI Analysis Results */}
      {aiAnalysis && aiAnalysis.success && (
        <Card className="mt-6 shadow-lg border-0 bg-gradient-to-br from-purple-50 to-blue-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-purple-700">
              <Brain className="h-5 w-5 mr-2" />
              AI Employee Analysis 🧠
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setAiAnalysis(null)}
                className="ml-auto hover:bg-purple-100"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {aiAnalysis.insights && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(aiAnalysis.insights).map(([key, value]) => (
                    <div key={key} className="p-4 bg-white/80 backdrop-blur-sm rounded-xl shadow-sm">
                      <h4 className="font-semibold text-purple-700 mb-2 capitalize">
                        {key.replace(/_/g, ' ')}
                      </h4>
                      <p className="text-sm text-gray-700">
                        {typeof value === 'string' ? value : JSON.stringify(value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
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

const EmployeeEditForm = ({ employee, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: employee.name || '',
    employee_id: employee.employee_id || '',
    email: employee.email || '',
    department: employee.department || '',
    manager: employee.manager || '',
    start_date: employee.start_date ? new Date(employee.start_date) : new Date(),
    status: employee.status || 'active'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="edit-name">Ninja Name *</Label>
          <Input
            id="edit-name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g., Alex the Code Warrior"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
        <div>
          <Label htmlFor="edit-employee_id">Ninja ID *</Label>
          <Input
            id="edit-employee_id"
            value={formData.employee_id}
            onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
            placeholder="e.g., NIN001"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>
      
      <div>
        <Label htmlFor="edit-email">Email Address *</Label>
        <Input
          id="edit-email"
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
          <Label htmlFor="edit-department">Department *</Label>
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
          <Label htmlFor="edit-manager">Squad Leader *</Label>
          <Input
            id="edit-manager"
            value={formData.manager}
            onChange={(e) => setFormData({...formData, manager: e.target.value})}
            placeholder="e.g., Senior Ninja Master"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>

      <div>
        <Label htmlFor="edit-status">Current Status</Label>
        <Select value={formData.status} onValueChange={(value) => setFormData({...formData, status: value})}>
          <SelectTrigger className="border-purple-200">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="onboarding">🚀 Onboarding</SelectItem>
            <SelectItem value="active">⚡ Active</SelectItem>
            <SelectItem value="exiting">👋 Exiting</SelectItem>
            <SelectItem value="exited">🎓 Exited</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex space-x-3">
        <Button 
          type="button" 
          variant="outline" 
          onClick={onCancel}
          className="flex-1 border-gray-300 hover:bg-gray-50"
        >
          Cancel
        </Button>
        <Button 
          type="submit" 
          className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
        >
          <Save className="w-4 h-4 mr-2" />
          Update Profile
        </Button>
      </div>
    </form>
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

const EmployeeEditForm = ({ employee, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: employee.name || '',
    employee_id: employee.employee_id || '',
    email: employee.email || '',
    department: employee.department || '',
    manager: employee.manager || '',
    start_date: employee.start_date ? new Date(employee.start_date) : new Date(),
    status: employee.status || 'active'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="edit-name">Ninja Name *</Label>
          <Input
            id="edit-name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g., Alex the Code Warrior"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
        <div>
          <Label htmlFor="edit-employee_id">Ninja ID *</Label>
          <Input
            id="edit-employee_id"
            value={formData.employee_id}
            onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
            placeholder="e.g., NIN001"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>
      
      <div>
        <Label htmlFor="edit-email">Email Address *</Label>
        <Input
          id="edit-email"
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
          <Label htmlFor="edit-department">Department *</Label>
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
          <Label htmlFor="edit-manager">Squad Leader *</Label>
          <Input
            id="edit-manager"
            value={formData.manager}
            onChange={(e) => setFormData({...formData, manager: e.target.value})}
            placeholder="e.g., Senior Ninja Master"
            className="border-purple-200 focus:border-purple-400"
            required
          />
        </div>
      </div>

      <div>
        <Label htmlFor="edit-status">Current Status</Label>
        <Select value={formData.status} onValueChange={(value) => setFormData({...formData, status: value})}>
          <SelectTrigger className="border-purple-200">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="onboarding">🚀 Onboarding</SelectItem>
            <SelectItem value="active">⚡ Active</SelectItem>
            <SelectItem value="exiting">👋 Exiting</SelectItem>
            <SelectItem value="exited">🎓 Exited</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex space-x-3">
        <Button 
          type="button" 
          variant="outline" 
          onClick={onCancel}
          className="flex-1 border-gray-300 hover:bg-gray-50"
        >
          Cancel
        </Button>
        <Button 
          type="submit" 
          className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
        >
          <Save className="w-4 h-4 mr-2" />
          Update Profile
        </Button>
      </div>
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
