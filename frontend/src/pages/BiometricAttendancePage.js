import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Fingerprint, 
  ScanFace,
  Camera,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  Shield,
  RefreshCw,
  UserCheck,
  AlertTriangle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('cognify_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function BiometricAttendancePage() {
  const { user } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanType, setScanType] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResult, setScanResult] = useState(null);
  const [showEnrollDialog, setShowEnrollDialog] = useState(false);
  const [enrollType, setEnrollType] = useState(null);
  const [enrollProgress, setEnrollProgress] = useState(0);
  const videoRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);

  // Mock attendance records
  React.useEffect(() => {
    setRecords([
      { id: '1', student_name: 'Tendai Moyo', method: 'face', time: '08:15 AM', status: 'present', confidence: 98 },
      { id: '2', student_name: 'Chipo Ndlovu', method: 'fingerprint', time: '08:22 AM', status: 'present', confidence: 99 },
      { id: '3', student_name: 'Tapiwa Zimba', method: 'face', time: '08:45 AM', status: 'late', confidence: 95 },
    ]);
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      toast.error('Camera access denied');
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      setCameraActive(false);
    }
  };

  const handleScan = async (type) => {
    setScanType(type);
    setScanning(true);
    setScanProgress(0);
    setScanResult(null);

    // Simulate scanning progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(r => setTimeout(r, 200));
      setScanProgress(i);
    }

    // Simulate result
    const success = Math.random() > 0.2;
    setScanResult({
      success,
      student: success ? {
        name: 'Demo Student',
        id: 'STU001',
        confidence: Math.floor(Math.random() * 10 + 90)
      } : null,
      message: success ? 'Attendance recorded successfully' : 'Biometric not recognized'
    });

    if (success) {
      toast.success('Attendance recorded!');
      // Add to records
      setRecords(prev => [{
        id: Date.now().toString(),
        student_name: 'Demo Student',
        method: type,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'present',
        confidence: Math.floor(Math.random() * 10 + 90)
      }, ...prev]);
    }

    setTimeout(() => {
      setScanning(false);
      setScanType(null);
    }, 2000);
  };

  const handleEnroll = async (type) => {
    setEnrollType(type);
    setEnrollProgress(0);
    
    if (type === 'face') {
      await startCamera();
    }

    // Simulate enrollment
    for (let i = 0; i <= 100; i += 5) {
      await new Promise(r => setTimeout(r, 100));
      setEnrollProgress(i);
    }

    stopCamera();
    toast.success(`${type === 'face' ? 'Face' : 'Fingerprint'} enrolled successfully!`);
    setShowEnrollDialog(false);
    setEnrollType(null);
  };

  const stats = {
    present: records.filter(r => r.status === 'present').length,
    late: records.filter(r => r.status === 'late').length,
    total: records.length
  };

  return (
    <DashboardLayout>
      <Header 
        title="Biometric Attendance"
        subtitle="Fingerprint and facial recognition attendance system"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-emerald-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Secure Biometric Verification</h3>
                <p className="text-zinc-400 text-sm">
                  Use fingerprint or facial recognition for secure, contactless attendance. 
                  Biometric data is encrypted and stored securely on-device.
                </p>
              </div>
            </div>
          </div>

          {/* Scan Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Fingerprint Scanner */}
            <div className="glass-card p-8 text-center">
              <div className={`w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center transition-all ${
                scanning && scanType === 'fingerprint' 
                  ? 'bg-blue-500/30 animate-pulse' 
                  : 'bg-zinc-800'
              }`}>
                <Fingerprint className={`w-12 h-12 ${
                  scanning && scanType === 'fingerprint' ? 'text-blue-400' : 'text-zinc-500'
                }`} />
              </div>
              
              <h3 className="text-lg font-semibold mb-2">Fingerprint Scanner</h3>
              <p className="text-sm text-zinc-500 mb-6">Place finger on the scanner</p>
              
              {scanning && scanType === 'fingerprint' ? (
                <div className="space-y-3">
                  <Progress value={scanProgress} className="h-2 bg-zinc-700" />
                  <p className="text-sm text-blue-400">Scanning... {scanProgress}%</p>
                </div>
              ) : (
                <Button 
                  onClick={() => handleScan('fingerprint')}
                  className="bg-blue-500 hover:bg-blue-600"
                  disabled={scanning}
                >
                  <Fingerprint className="w-4 h-4 mr-2" />
                  Scan Fingerprint
                </Button>
              )}
            </div>

            {/* Face Scanner */}
            <div className="glass-card p-8 text-center">
              <div className={`w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center transition-all ${
                scanning && scanType === 'face' 
                  ? 'bg-violet-500/30 animate-pulse' 
                  : 'bg-zinc-800'
              }`}>
                <ScanFace className={`w-12 h-12 ${
                  scanning && scanType === 'face' ? 'text-violet-400' : 'text-zinc-500'
                }`} />
              </div>
              
              <h3 className="text-lg font-semibold mb-2">Facial Recognition</h3>
              <p className="text-sm text-zinc-500 mb-6">Look at the camera</p>
              
              {scanning && scanType === 'face' ? (
                <div className="space-y-3">
                  <Progress value={scanProgress} className="h-2 bg-zinc-700" />
                  <p className="text-sm text-violet-400">Scanning... {scanProgress}%</p>
                </div>
              ) : (
                <Button 
                  onClick={() => handleScan('face')}
                  className="bg-violet-500 hover:bg-violet-600"
                  disabled={scanning}
                >
                  <ScanFace className="w-4 h-4 mr-2" />
                  Scan Face
                </Button>
              )}
            </div>
          </div>

          {/* Scan Result */}
          {scanResult && (
            <div className={`glass-card p-6 mb-8 animate-fadeIn ${
              scanResult.success ? 'border-emerald-500/30' : 'border-red-500/30'
            }`}>
              <div className="flex items-center gap-4">
                {scanResult.success ? (
                  <>
                    <CheckCircle className="w-12 h-12 text-emerald-400" />
                    <div>
                      <h3 className="font-semibold text-lg">{scanResult.student.name}</h3>
                      <p className="text-sm text-zinc-400">ID: {scanResult.student.id}</p>
                      <Badge className="mt-2 bg-emerald-500/20 text-emerald-400">
                        {scanResult.student.confidence}% confidence
                      </Badge>
                    </div>
                  </>
                ) : (
                  <>
                    <XCircle className="w-12 h-12 text-red-400" />
                    <div>
                      <h3 className="font-semibold text-lg text-red-400">Not Recognized</h3>
                      <p className="text-sm text-zinc-400">{scanResult.message}</p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Stats & Enroll */}
          <div className="flex flex-col md:flex-row gap-6 mb-8">
            <div className="flex-1 grid grid-cols-3 gap-4">
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-emerald-400">{stats.present}</div>
                <p className="text-sm text-zinc-500">Present</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-amber-400">{stats.late}</div>
                <p className="text-sm text-zinc-500">Late</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{stats.total}</div>
                <p className="text-sm text-zinc-500">Total</p>
              </div>
            </div>
            
            <Dialog open={showEnrollDialog} onOpenChange={setShowEnrollDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-white/10 h-auto py-4">
                  <Camera className="w-4 h-4 mr-2" />
                  Enroll Biometrics
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10">
                <DialogHeader>
                  <DialogTitle>Enroll Biometrics</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Register fingerprint or face for attendance
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  {enrollType ? (
                    <div className="text-center py-8">
                      {enrollType === 'face' && (
                        <div className="mb-4 rounded-xl overflow-hidden bg-zinc-800 aspect-video">
                          <video ref={videoRef} autoPlay className="w-full h-full object-cover" />
                        </div>
                      )}
                      <Progress value={enrollProgress} className="h-2 bg-zinc-700 mb-4" />
                      <p className="text-sm text-zinc-400">
                        {enrollType === 'face' ? 'Capturing face data...' : 'Place finger on scanner...'}
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      <Button 
                        onClick={() => handleEnroll('fingerprint')}
                        variant="outline" 
                        className="h-32 flex-col border-white/10"
                      >
                        <Fingerprint className="w-8 h-8 mb-2" />
                        Fingerprint
                      </Button>
                      <Button 
                        onClick={() => handleEnroll('face')}
                        variant="outline" 
                        className="h-32 flex-col border-white/10"
                      >
                        <ScanFace className="w-8 h-8 mb-2" />
                        Face ID
                      </Button>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Today's Records */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-emerald-400" />
              Today's Biometric Attendance
            </h2>
            
            <div className="space-y-3">
              {records.map((record) => (
                <div 
                  key={record.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-zinc-800/50 border border-white/5"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      record.method === 'face' ? 'bg-violet-500/20' : 'bg-blue-500/20'
                    }`}>
                      {record.method === 'face' ? (
                        <ScanFace className="w-5 h-5 text-violet-400" />
                      ) : (
                        <Fingerprint className="w-5 h-5 text-blue-400" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{record.student_name}</p>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Clock className="w-3 h-3" />
                        {record.time}
                        <span className="text-zinc-600">•</span>
                        {record.confidence}% match
                      </div>
                    </div>
                  </div>
                  <Badge className={
                    record.status === 'present' 
                      ? 'bg-emerald-500/20 text-emerald-400' 
                      : 'bg-amber-500/20 text-amber-400'
                  }>
                    {record.status === 'present' ? 'Present' : 'Late'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
