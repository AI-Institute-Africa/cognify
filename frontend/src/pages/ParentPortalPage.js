import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Users, 
  UserPlus, 
  BookOpen, 
  TrendingUp,
  Bell,
  CreditCard,
  Eye,
  Calendar,
  GraduationCap,
  Search,
  Mail
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
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
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('eduos_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function ParentPortalPage() {
  const { user } = useAuth();
  const [children, setChildren] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedChild, setSelectedChild] = useState(null);
  const [childDetails, setChildDetails] = useState(null);
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [linkEmail, setLinkEmail] = useState('');
  const [linking, setLinking] = useState(false);

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      const response = await axios.get(`${API}/parents/children`, { headers: getAuthHeaders() });
      setChildren(response.data);
      if (response.data.length > 0 && !selectedChild) {
        setSelectedChild(response.data[0]);
        loadChildDetails(response.data[0].id);
      }
    } catch (error) {
      // If no children linked yet, just show empty state
      setChildren([]);
    } finally {
      setLoading(false);
    }
  };

  const loadChildDetails = async (childId) => {
    try {
      const response = await axios.get(`${API}/parents/children/${childId}/details`, { headers: getAuthHeaders() });
      setChildDetails(response.data);
    } catch (error) {
      console.error('Failed to load child details:', error);
    }
  };

  const handleLinkChild = async () => {
    if (!linkEmail.trim()) {
      toast.error('Please enter child\'s email');
      return;
    }
    
    setLinking(true);
    try {
      await axios.post(`${API}/parents/link-child`, { child_email: linkEmail }, { headers: getAuthHeaders() });
      toast.success('Link request sent! Child will need to approve.');
      setShowLinkDialog(false);
      setLinkEmail('');
      loadChildren();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to link child');
    } finally {
      setLinking(false);
    }
  };

  const handleSelectChild = (child) => {
    setSelectedChild(child);
    loadChildDetails(child.id);
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
        title="Parent Portal"
        subtitle="Monitor your children's academic progress"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Children Selector */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {children.map(child => (
                <button
                  key={child.id}
                  onClick={() => handleSelectChild(child)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    selectedChild?.id === child.id
                      ? 'bg-blue-500/20 border-2 border-blue-500'
                      : 'bg-zinc-800/50 border-2 border-transparent hover:border-white/10'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-semibold">
                    {child.full_name?.charAt(0) || 'S'}
                  </div>
                  <div className="text-left">
                    <p className="font-medium">{child.full_name}</p>
                    <p className="text-xs text-zinc-500">{child.grade_level}</p>
                  </div>
                </button>
              ))}
              
              {children.length === 0 && (
                <div className="text-zinc-500">No children linked yet</div>
              )}
            </div>
            
            <Dialog open={showLinkDialog} onOpenChange={setShowLinkDialog}>
              <DialogTrigger asChild>
                <Button className="bg-blue-500 hover:bg-blue-600">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Link Child
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10">
                <DialogHeader>
                  <DialogTitle>Link Child Account</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Enter your child's email to send a link request
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Child's Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                      <Input
                        type="email"
                        placeholder="child@school.edu"
                        value={linkEmail}
                        onChange={(e) => setLinkEmail(e.target.value)}
                        className="pl-11 bg-zinc-800 border-white/10"
                      />
                    </div>
                  </div>
                  <Button onClick={handleLinkChild} disabled={linking} className="w-full">
                    {linking ? 'Sending Request...' : 'Send Link Request'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Child Dashboard */}
          {selectedChild && childDetails ? (
            <div className="space-y-6">
              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-zinc-500">Current GPA</p>
                      <p className="text-2xl font-bold text-emerald-400">{childDetails.gpa?.toFixed(2) || '0.00'}</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-emerald-400" />
                  </div>
                </div>
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-zinc-500">Attendance</p>
                      <p className="text-2xl font-bold">{childDetails.attendance_rate || 0}%</p>
                    </div>
                    <Calendar className="w-8 h-8 text-blue-400" />
                  </div>
                </div>
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-zinc-500">Enrolled Courses</p>
                      <p className="text-2xl font-bold">{childDetails.courses?.length || 0}</p>
                    </div>
                    <BookOpen className="w-8 h-8 text-violet-400" />
                  </div>
                </div>
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-zinc-500">Pending Fees</p>
                      <p className="text-2xl font-bold text-amber-400">${childDetails.pending_fees || 0}</p>
                    </div>
                    <CreditCard className="w-8 h-8 text-amber-400" />
                  </div>
                </div>
              </div>

              {/* Course Progress */}
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <GraduationCap className="w-5 h-5 text-blue-400" />
                  Course Progress
                </h2>
                
                {childDetails.courses?.length > 0 ? (
                  <div className="space-y-4">
                    {childDetails.courses.map(course => (
                      <div key={course.id} className="p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <h3 className="font-medium">{course.name}</h3>
                            <p className="text-sm text-zinc-500">{course.code}</p>
                          </div>
                          <Badge className={`${
                            course.grade >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                            course.grade >= 60 ? 'bg-blue-500/20 text-blue-400' :
                            'bg-amber-500/20 text-amber-400'
                          }`}>
                            {course.grade || 0}%
                          </Badge>
                        </div>
                        <Progress value={course.grade || 0} className="h-2 bg-zinc-700" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-center py-8">No courses enrolled</p>
                )}
              </div>

              {/* Recent Activity */}
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Bell className="w-5 h-5 text-violet-400" />
                  Recent Activity
                </h2>
                
                {childDetails.recent_activity?.length > 0 ? (
                  <div className="space-y-3">
                    {childDetails.recent_activity.map((activity, index) => (
                      <div key={index} className="flex items-center gap-4 p-3 rounded-lg bg-zinc-800/30">
                        <div className={`p-2 rounded-lg ${
                          activity.type === 'grade' ? 'bg-emerald-500/20' :
                          activity.type === 'attendance' ? 'bg-blue-500/20' :
                          'bg-amber-500/20'
                        }`}>
                          {activity.type === 'grade' && <TrendingUp className="w-4 h-4 text-emerald-400" />}
                          {activity.type === 'attendance' && <Calendar className="w-4 h-4 text-blue-400" />}
                          {activity.type === 'fee' && <CreditCard className="w-4 h-4 text-amber-400" />}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm">{activity.message}</p>
                          <p className="text-xs text-zinc-500">{activity.date}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-center py-8">No recent activity</p>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <Users className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No Children Linked</h3>
              <p className="text-zinc-500 mb-6">
                Link your child's account to monitor their academic progress
              </p>
              <Button onClick={() => setShowLinkDialog(true)} className="bg-blue-500 hover:bg-blue-600">
                <UserPlus className="w-4 h-4 mr-2" />
                Link Child Account
              </Button>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
