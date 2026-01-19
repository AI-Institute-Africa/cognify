import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { createZoomMeeting, getZoomMeetings } from '../services/api';
import { 
  Video, 
  Monitor,
  Users,
  Calendar,
  Clock,
  Plus,
  ExternalLink,
  Play,
  Copy,
  RefreshCw,
  AlertCircle
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

export default function VirtualClassroomPage() {
  const { user } = useAuth();
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    platform: 'zoom',
    duration: '60'
  });

  useEffect(() => {
    loadMeetings();
  }, []);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      const data = await getZoomMeetings();
      setMeetings(data || []);
    } catch (error) {
      console.error('Failed to load meetings:', error);
      toast.error('Failed to load meetings');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMeeting = async () => {
    if (!newMeeting.title) {
      toast.error('Please enter a class title');
      return;
    }

    setCreating(true);
    try {
      const result = await createZoomMeeting(
        newMeeting.title,
        parseInt(newMeeting.duration)
      );
      
      toast.success('Meeting created successfully!');
      setShowCreateDialog(false);
      setNewMeeting({ title: '', platform: 'zoom', duration: '60' });
      
      // Reload meetings to show the new one
      loadMeetings();
    } catch (error) {
      console.error('Failed to create meeting:', error);
      toast.error(error.response?.data?.detail || 'Failed to create meeting');
    } finally {
      setCreating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const getMeetingStatus = (meeting) => {
    const startTime = new Date(meeting.start_time || meeting.created_at);
    const endTime = new Date(startTime.getTime() + (meeting.duration || 60) * 60000);
    const now = new Date();
    
    if (now >= startTime && now <= endTime) return 'live';
    if (now < startTime) return 'scheduled';
    return 'completed';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'live':
        return <Badge className="bg-red-500/20 text-red-400 animate-pulse">🔴 Live Now</Badge>;
      case 'scheduled':
        return <Badge className="bg-amber-500/20 text-amber-400">Scheduled</Badge>;
      case 'completed':
        return <Badge className="bg-zinc-500/20 text-zinc-400">Completed</Badge>;
      default:
        return null;
    }
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
        title="Virtual Classroom"
        subtitle="Zoom integration for hybrid learning"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="glass-card p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Video className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold">Zoom</h3>
                  <p className="text-sm text-zinc-500">HD video meetings - Connected ✓</p>
                </div>
              </div>
              <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
            </div>
            
            <div className="glass-card p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-zinc-500/20 flex items-center justify-center">
                  <Monitor className="w-6 h-6 text-zinc-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-400">Google Meet</h3>
                  <p className="text-sm text-zinc-600">Coming soon</p>
                </div>
              </div>
              <Badge className="bg-zinc-500/20 text-zinc-500">Pending</Badge>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between items-center mb-6">
            <Button 
              variant="outline" 
              onClick={loadMeetings}
              className="border-white/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            
            {(user?.role === 'teacher' || user?.role === 'admin' || user?.role === 'org_admin') && (
              <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogTrigger asChild>
                  <Button data-testid="schedule-class-btn" className="bg-violet-500 hover:bg-violet-600">
                    <Plus className="w-4 h-4 mr-2" />
                    Schedule Class
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Schedule Virtual Class</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Create a new Zoom meeting for your class
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Class Title *</Label>
                      <Input
                        placeholder="e.g., Physics 101 - Chapter 5"
                        value={newMeeting.title}
                        onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                        data-testid="meeting-title-input"
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Duration</Label>
                      <Select 
                        value={newMeeting.duration} 
                        onValueChange={(v) => setNewMeeting({...newMeeting, duration: v})}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          <SelectItem value="30">30 minutes</SelectItem>
                          <SelectItem value="45">45 minutes</SelectItem>
                          <SelectItem value="60">1 hour</SelectItem>
                          <SelectItem value="90">1.5 hours</SelectItem>
                          <SelectItem value="120">2 hours</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                      <p className="text-sm text-blue-300 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Meeting will be created via Zoom API and start immediately
                      </p>
                    </div>
                    
                    <Button 
                      onClick={handleCreateMeeting} 
                      disabled={creating}
                      data-testid="create-meeting-btn"
                      className="w-full"
                    >
                      {creating ? 'Creating...' : 'Create Zoom Meeting'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            )}
          </div>

          {/* Meetings List */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-violet-400" />
              Virtual Classes ({meetings.length})
            </h2>
            
            {meetings.length === 0 ? (
              <div className="text-center py-12">
                <Video className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No meetings yet</h3>
                <p className="text-zinc-500">
                  {user?.role === 'teacher' || user?.role === 'admin' 
                    ? 'Schedule your first virtual class to get started'
                    : 'No virtual classes scheduled at the moment'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {meetings.map((meeting) => {
                  const status = getMeetingStatus(meeting);
                  return (
                    <div 
                      key={meeting.id}
                      data-testid={`meeting-card-${meeting.id}`}
                      className={`p-5 rounded-xl border transition-all ${
                        status === 'live' 
                          ? 'bg-red-500/5 border-red-500/30' 
                          : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                            <Video className="w-6 h-6 text-blue-400" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{meeting.topic}</h3>
                            <p className="text-sm text-zinc-500">
                              Platform: {meeting.platform || 'Zoom'}
                            </p>
                          </div>
                        </div>
                        {getStatusBadge(status)}
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-400 mb-4">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {meeting.duration} minutes
                        </span>
                        {meeting.zoom_id && (
                          <span className="flex items-center gap-1">
                            <span className="text-zinc-500">Zoom ID:</span>
                            <code className="font-mono">{meeting.zoom_id}</code>
                          </span>
                        )}
                      </div>
                      
                      {meeting.password && (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-900/50 mb-4">
                          <span className="text-xs text-zinc-500">Password:</span>
                          <code className="text-sm font-mono text-amber-400">{meeting.password}</code>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => copyToClipboard(meeting.password)}
                            className="ml-auto h-7 px-2"
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                      
                      <div className="flex gap-3">
                        <Button 
                          onClick={() => window.open(meeting.join_url, '_blank')}
                          data-testid={`join-meeting-${meeting.id}`}
                          className={`flex-1 ${status === 'live' ? 'bg-red-500 hover:bg-red-600' : ''}`}
                        >
                          {status === 'live' ? (
                            <>
                              <Play className="w-4 h-4 mr-2" />
                              Join Now
                            </>
                          ) : (
                            <>
                              <ExternalLink className="w-4 h-4 mr-2" />
                              Open Meeting
                            </>
                          )}
                        </Button>
                        <Button 
                          variant="outline" 
                          onClick={() => copyToClipboard(meeting.join_url)}
                          className="border-white/10"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
