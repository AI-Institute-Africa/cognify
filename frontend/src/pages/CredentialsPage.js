import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Award, 
  FileCheck, 
  Shield,
  Plus,
  Search,
  ExternalLink,
  CheckCircle,
  XCircle,
  Copy,
  Download,
  Users
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
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
  const token = localStorage.getItem('cognify_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const credentialTypes = [
  { value: 'diploma', label: 'Diploma', icon: '🎓' },
  { value: 'certificate', label: 'Certificate', icon: '📜' },
  { value: 'transcript', label: 'Transcript', icon: '📄' },
  { value: 'badge', label: 'Achievement Badge', icon: '🏅' },
];

export default function CredentialsPage() {
  const { user } = useAuth();
  const [credentials, setCredentials] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  const [showVerifyDialog, setShowVerifyDialog] = useState(false);
  const [verifyHash, setVerifyHash] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);
  const [issuing, setIssuing] = useState(false);
  const [newCredential, setNewCredential] = useState({
    student_id: '',
    credential_type: '',
    title: '',
    description: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const studentsRes = await axios.get(`${API}/students`, { headers: getAuthHeaders() });
      setStudents(studentsRes.data);
      
      // Load recent credentials (admin view)
      // For now, we'll show a sample - in production you'd have a dedicated endpoint
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleIssueCredential = async () => {
    if (!newCredential.student_id || !newCredential.credential_type || !newCredential.title) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setIssuing(true);
    try {
      const response = await axios.post(`${API}/credentials/issue`, newCredential, { headers: getAuthHeaders() });
      
      // Get the issued credential data
      const issuedCredential = {
        ...newCredential,
        credential_id: response.data.credential_id,
        hash: response.data.hash,
        verification_url: response.data.verification_url,
        issued_at: new Date().toISOString(),
        // Get student name from students list
        student_name: students.find(s => s.id === newCredential.student_id)?.user?.full_name || 'Student'
      };
      
      toast.success('Credential issued successfully!');
      setCredentials(prev => [...prev, issuedCredential]);
      setShowIssueDialog(false);
      setNewCredential({ student_id: '', credential_type: '', title: '', description: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to issue credential');
    } finally {
      setIssuing(false);
    }
  };

  const handleVerifyCredential = async () => {
    if (!verifyHash.trim()) {
      toast.error('Please enter a credential hash to verify');
      return;
    }
    
    try {
      const response = await axios.get(`${API}/credentials/verify/${verifyHash.trim()}`);
      setVerifyResult(response.data);
    } catch (error) {
      setVerifyResult({ verified: false, message: 'Verification failed' });
    }
  };

  const copyToClipboard = (text) => {
    if (!text) {
      toast.error('Nothing to copy');
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      toast.success('Copied to clipboard!');
    }).catch(() => {
      toast.error('Failed to copy to clipboard');
    });
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
        title="Blockchain Credentials"
        subtitle="Issue and verify tamper-proof academic credentials"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-violet-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-violet-500/20">
                <Shield className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">Tamper-Proof Credentials</h3>
                <p className="text-zinc-400 text-sm">
                  Issue verifiable digital credentials secured by cryptographic hashing. 
                  Anyone can verify the authenticity of a credential using its unique hash.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 mb-8">
            <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
              <DialogTrigger asChild>
                <Button className="bg-violet-500 hover:bg-violet-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Issue Credential
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
                <DialogHeader>
                  <DialogTitle>Issue New Credential</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Create a verifiable digital credential for a student
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Student</Label>
                    <Select 
                      value={newCredential.student_id} 
                      onValueChange={(v) => setNewCredential({...newCredential, student_id: v})}
                    >
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
                    <Label>Credential Type</Label>
                    <Select 
                      value={newCredential.credential_type} 
                      onValueChange={(v) => setNewCredential({...newCredential, credential_type: v})}
                    >
                      <SelectTrigger className="bg-zinc-800 border-white/10">
                        <SelectValue placeholder="Select type..." />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-white/10">
                        {credentialTypes.map(type => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input
                      placeholder="e.g., Bachelor of Science in Computer Science"
                      value={newCredential.title}
                      onChange={(e) => setNewCredential({...newCredential, title: e.target.value})}
                      className="bg-zinc-800 border-white/10"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      placeholder="Additional details about the credential..."
                      value={newCredential.description}
                      onChange={(e) => setNewCredential({...newCredential, description: e.target.value})}
                      className="bg-zinc-800 border-white/10 min-h-[100px]"
                    />
                  </div>
                  
                  <Button onClick={handleIssueCredential} disabled={issuing} className="w-full">
                    {issuing ? 'Issuing...' : 'Issue Credential'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={showVerifyDialog} onOpenChange={setShowVerifyDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-white/10">
                  <Search className="w-4 h-4 mr-2" />
                  Verify Credential
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
                <DialogHeader>
                  <DialogTitle>Verify Credential</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Enter a credential hash to verify its authenticity
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Credential Hash</Label>
                    <Input
                      placeholder="Enter SHA-256 hash..."
                      value={verifyHash}
                      onChange={(e) => setVerifyHash(e.target.value)}
                      className="bg-zinc-800 border-white/10 font-mono text-sm"
                    />
                  </div>
                  
                  {verifyResult && (
                    <div className={`p-4 rounded-xl ${
                      verifyResult.verified 
                        ? 'bg-emerald-500/10 border border-emerald-500/20' 
                        : 'bg-red-500/10 border border-red-500/20'
                    }`}>
                      {verifyResult.verified ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2">
                            <CheckCircle className="w-6 h-6 text-emerald-400" />
                            <span className="font-semibold text-emerald-400">Credential Verified!</span>
                          </div>
                          <div className="space-y-2 text-sm">
                            <p><span className="text-zinc-500">Student:</span> {verifyResult.credential.student_name}</p>
                            <p><span className="text-zinc-500">Type:</span> {verifyResult.credential.credential_type}</p>
                            <p><span className="text-zinc-500">Title:</span> {verifyResult.credential.title}</p>
                            <p><span className="text-zinc-500">Issued:</span> {new Date(verifyResult.credential.issued_at).toLocaleDateString()}</p>
                            <p><span className="text-zinc-500">Issuer:</span> {verifyResult.credential.issuer_name}</p>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <XCircle className="w-6 h-6 text-red-400" />
                          <span className="text-red-400">{verifyResult.message}</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <Button onClick={handleVerifyCredential} className="w-full">
                    Verify
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Recent Issued Credentials */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-400" />
              Issued Credentials
            </h2>
            
            {credentials.length === 0 ? (
              <div className="text-center py-12">
                <FileCheck className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                <p className="text-zinc-500">No credentials issued yet</p>
                <p className="text-zinc-600 text-sm mt-1">Issue your first credential to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {credentials.map((credential, index) => (
                  <div 
                    key={credential.credential_id || index}
                    className="p-4 rounded-xl bg-zinc-800/50 border border-white/5 hover:border-white/10 transition-all animate-fadeIn"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="p-3 rounded-xl bg-violet-500/20">
                          <Award className="w-6 h-6 text-violet-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold">Credential Issued</h3>
                          <p className="text-sm text-zinc-400 mt-1">
                            Hash: <code className="text-xs bg-zinc-900 px-2 py-0.5 rounded">{credential.hash?.slice(0, 16)}...</code>
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => copyToClipboard(credential.hash)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Badge className="bg-emerald-500/20 text-emerald-400">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Valid
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* How It Works */}
          <div className="glass-card p-6 mt-8">
            <h2 className="text-lg font-semibold mb-4">How It Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4">
                <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl font-bold text-blue-400">1</span>
                </div>
                <h3 className="font-medium mb-2">Issue</h3>
                <p className="text-sm text-zinc-500">
                  Create a credential with student details. A unique SHA-256 hash is generated.
                </p>
              </div>
              <div className="text-center p-4">
                <div className="w-12 h-12 rounded-full bg-violet-500/20 flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl font-bold text-violet-400">2</span>
                </div>
                <h3 className="font-medium mb-2">Share</h3>
                <p className="text-sm text-zinc-500">
                  Student receives the hash. They can share it with employers or institutions.
                </p>
              </div>
              <div className="text-center p-4">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl font-bold text-emerald-400">3</span>
                </div>
                <h3 className="font-medium mb-2">Verify</h3>
                <p className="text-sm text-zinc-500">
                  Anyone can verify the credential's authenticity using the hash.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
