import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Wifi, 
  UserCheck, 
  Clock,
  MapPin,
  Search,
  Plus,
  CheckCircle,
  XCircle,
  RefreshCw,
  CreditCard,
  Users
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('eduos_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function RFIDAttendancePage() {
  const { user } = useAuth();
  const [records, setRecords] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [showScanDialog, setShowScanDialog] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState('');
  const [rfidTag, setRfidTag] = useState('');
  const [scanTag, setScanTag] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [registering, setRegistering] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [recordsRes, studentsRes] = await Promise.all([
        axios.get(`${API}/rfid/attendance/today`, { headers: getAuthHeaders() }),
        axios.get(`${API}/students`, { headers: getAuthHeaders() })
      ]);
      setRecords(recordsRes.data);
      setStudents(studentsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterRFID = async () => {
    if (!selectedStudent || !rfidTag.trim()) {
      toast.error('Please select a student and enter RFID tag');
      return;
    }
    
    setRegistering(true);
    try {
      await axios.post(`${API}/rfid/register`, {
        student_id: selectedStudent,
        rfid_tag: rfidTag.trim()
      }, { headers: getAuthHeaders() });
      
      toast.success('RFID card registered successfully!');
      setShowRegisterDialog(false);
      setSelectedStudent('');
      setRfidTag('');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to register RFID');
    } finally {
      setRegistering(false);
    }
  };

  const handleSimulateScan = async () => {
    if (!scanTag.trim()) {
      toast.error('Please enter an RFID tag to scan');
      return;
    }
    
    try {
      const response = await axios.post(`${API}/rfid/scan`, {
        rfid_tag: scanTag.trim(),
        device_id: 'DEMO-SCANNER-001',
        location: 'Main Entrance'
      });
      
      setScanResult(response.data);
      if (response.data.success) {
        toast.success(`${response.data.student?.name} ${response.data.action === 'checked_in' ? 'checked in' : 'checked out'}!`);
        loadData();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('Scan failed');
    }
  };

  const stats = {
    checkedIn: records.filter(r => r.check_in && !r.check_out).length,
    checkedOut: records.filter(r => r.check_out).length,
    total: records.length
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="RFID Attendance"
        subtitle="Smart campus attendance tracking via NFC/RFID"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Wifi className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Smart Campus Attendance</h3>
                <p className="text-zinc-400 text-sm">
                  Students can tap their RFID/NFC cards at entry points to automatically record attendance. 
                  Register cards below or simulate a scan for testing.
                </p>
              </div>
            </div>
          </div>

          {/* Stats & Actions */}
          <div className="flex flex-col md:flex-row gap-6 mb-8">
            {/* Stats */}
            <div className="flex-1 grid grid-cols-3 gap-4">
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-emerald-400">{stats.checkedIn}</div>
                <p className="text-sm text-zinc-500">Checked In</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-amber-400">{stats.checkedOut}</div>
                <p className="text-sm text-zinc-500">Checked Out</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{stats.total}</div>
                <p className="text-sm text-zinc-500">Total Today</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
                <DialogTrigger asChild>
                  <Button className="bg-blue-500 hover:bg-blue-600">
                    <Plus className="w-4 h-4 mr-2" />
                    Register Card
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Register RFID Card</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Link an RFID/NFC card to a student
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Student</Label>
                      <Select value={selectedStudent} onValueChange={setSelectedStudent}>
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue placeholder="Select a student..." />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10 max-h-[200px]">
                          {students.map(student => (
                            <SelectItem key={student.id} value={student.id}>
                              {student.user?.full_name || student.id}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>RFID Tag ID</Label>
                      <div className="relative">
                        <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                        <Input
                          placeholder="e.g., RFID-001-2026"
                          value={rfidTag}
                          onChange={(e) => setRfidTag(e.target.value)}
                          className="pl-11 bg-zinc-800 border-white/10"
                        />
                      </div>
                    </div>
                    <Button onClick={handleRegisterRFID} disabled={registering} className="w-full">
                      {registering ? 'Registering...' : 'Register Card'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Dialog open={showScanDialog} onOpenChange={setShowScanDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="border-white/10">
                    <Wifi className="w-4 h-4 mr-2" />
                    Simulate Scan
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Simulate RFID Scan</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Test the RFID attendance system
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>RFID Tag</Label>
                      <Input
                        placeholder="Enter registered RFID tag..."
                        value={scanTag}
                        onChange={(e) => setScanTag(e.target.value)}
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                    
                    {scanResult && (
                      <div className={`p-4 rounded-xl ${
                        scanResult.success ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'
                      }`}>
                        {scanResult.success ? (
                          <div className="flex items-center gap-3">
                            <CheckCircle className="w-8 h-8 text-emerald-400" />
                            <div>
                              <p className="font-semibold">{scanResult.student?.name}</p>
                              <p className="text-sm text-zinc-400">
                                {scanResult.action === 'checked_in' ? 'Checked In' : 'Checked Out'} at {scanResult.location}
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-3">
                            <XCircle className="w-8 h-8 text-red-400" />
                            <p className="text-red-400">{scanResult.message}</p>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <Button onClick={handleSimulateScan} className="w-full bg-violet-500 hover:bg-violet-600">
                      <Wifi className="w-4 h-4 mr-2" />
                      Scan Card
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Button variant="outline" onClick={loadData} className="border-white/10">
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Attendance Records */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-emerald-400" />
              Today's Attendance
            </h2>
            
            {records.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                <p className="text-zinc-500">No attendance records today</p>
                <p className="text-zinc-600 text-sm mt-1">Students will appear here after scanning their cards</p>
              </div>
            ) : (
              <div className="space-y-3">
                {records.map((record, index) => (
                  <div 
                    key={record.id}
                    className="flex items-center justify-between p-4 rounded-xl bg-zinc-800/50 border border-white/5 hover:border-white/10 transition-all animate-fadeIn"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        record.check_out ? 'bg-zinc-700' : 'bg-emerald-500/20'
                      }`}>
                        <UserCheck className={`w-5 h-5 ${record.check_out ? 'text-zinc-400' : 'text-emerald-400'}`} />
                      </div>
                      <div>
                        <p className="font-medium">{record.student_name}</p>
                        <div className="flex items-center gap-3 text-xs text-zinc-500">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {record.location}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="w-4 h-4 text-emerald-400" />
                          <span>In: {new Date(record.check_in).toLocaleTimeString()}</span>
                        </div>
                        {record.check_out && (
                          <div className="flex items-center gap-2 text-sm text-zinc-500">
                            <Clock className="w-4 h-4" />
                            <span>Out: {new Date(record.check_out).toLocaleTimeString()}</span>
                          </div>
                        )}
                      </div>
                      <Badge className={record.check_out ? 'bg-zinc-500/20 text-zinc-400' : 'bg-emerald-500/20 text-emerald-400'}>
                        {record.check_out ? 'Left' : 'Present'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
