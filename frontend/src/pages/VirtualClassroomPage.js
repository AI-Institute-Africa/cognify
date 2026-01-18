import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Video, 
  VideoOff,
  Mic,
  MicOff,
  Monitor,
  Users,
  Calendar,
  Clock,
  Plus,
  ExternalLink,
  Play,
  Copy,
  CheckCircle
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
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    platform: 'zoom',
    date: '',
    time: '',
    duration: '60'
  });

  useEffect(() => {
    // Mock meetings data
    setMeetings([
      {
        id: '1',
        title: 'Physics 101 - Quantum Mechanics',
        platform: 'zoom',
        date: '2026-01-20',
        time: '09:00',
        duration: 60,
        status: 'scheduled',
        participants: 28,
        host: 'Dr. Sarah Williams',
        meeting_url: 'https://zoom.us/j/123456789',
        meeting_id: '123 456 789',
        passcode: 'PHY101'
      },
      {
        id: '2',
        title: 'Mathematics - Calculus Review',
        platform: 'meet',
        date: '2026-01-19',
        time: '14:00',
        duration: 45,
        status: 'live',
        participants: 32,
        host: 'Prof. John Moyo',
        meeting_url: 'https://meet.google.com/abc-defg-hij',
        meeting_id: 'abc-defg-hij'
      },
      {
        id: '3',
        title: 'Computer Science - Python Workshop',
        platform: 'zoom',
        date: '2026-01-18',
        time: '11:00',
        duration: 90,
        status: 'completed',
        participants: 45,
        host: 'Ms. Chipo Ndlovu',
        recording_url: 'https://zoom.us/rec/123',
        meeting_id: '987 654 321'
      }
    ]);
    setLoading(false);
  }, []);

  const handleCreateMeeting = async () => {
    if (!newMeeting.title || !newMeeting.date || !newMeeting.time) {
      toast.error('Please fill in all required fields');
      return;
    }

    const meeting = {
      id: Date.now().toString(),
      ...newMeeting,
      duration: parseInt(newMeeting.duration),
      status: 'scheduled',
      participants: 0,
      host: user?.full_name || 'You',
      meeting_url: newMeeting.platform === 'zoom' 
        ? `https://zoom.us/j/${Math.floor(Math.random() * 1000000000)}`
        : `https://meet.google.com/${Math.random().toString(36).substring(7)}`,
      meeting_id: newMeeting.platform === 'zoom'
        ? `${Math.floor(Math.random() * 1000)} ${Math.floor(Math.random() * 1000)} ${Math.floor(Math.random() * 1000)}`
        : Math.random().toString(36).substring(2, 14)
    };

    setMeetings([meeting, ...meetings]);
    toast.success('Meeting created successfully!');
    setShowCreateDialog(false);
    setNewMeeting({ title: '', platform: 'zoom', date: '', time: '', duration: '60' });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const getPlatformColor = (platform) => {
    return platform === 'zoom' ? 'bg-blue-500/20 text-blue-400' : 'bg-emerald-500/20 text-emerald-400';
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
        subtitle="Zoom & Google Meet integration for hybrid learning"
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
                  <p className="text-sm text-zinc-500">Host HD video meetings</p>
                </div>
              </div>
              <Button 
                onClick={() => window.open('https://zoom.us', '_blank')}
                variant="outline" 
                className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Zoom
              </Button>
            </div>
            
            <div className="glass-card p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                  <Monitor className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold">Google Meet</h3>
                  <p className="text-sm text-zinc-500">Secure video conferencing</p>
                </div>
              </div>
              <Button 
                onClick={() => window.open('https://meet.google.com', '_blank')}
                variant="outline" 
                className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Meet
              </Button>
            </div>
          </div>

          {/* Create Meeting Button */}
          {(user?.role === 'teacher' || user?.role === 'admin') && (
            <div className="flex justify-end mb-6">
              <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogTrigger asChild>
                  <Button className="bg-violet-500 hover:bg-violet-600">
                    <Plus className="w-4 h-4 mr-2" />
                    Schedule Class
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Schedule Virtual Class</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Create a new video meeting for your class
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Class Title</Label>
                      <Input
                        placeholder="e.g., Physics 101 - Chapter 5"
                        value={newMeeting.title}
                        onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Platform</Label>
                      <Select 
                        value={newMeeting.platform} 
                        onValueChange={(v) => setNewMeeting({...newMeeting, platform: v})}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          <SelectItem value="zoom">Zoom</SelectItem>
                          <SelectItem value="meet">Google Meet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Date</Label>
                        <Input
                          type="date"
                          value={newMeeting.date}
                          onChange={(e) => setNewMeeting({...newMeeting, date: e.target.value})}
                          className="bg-zinc-800 border-white/10"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Time</Label>
                        <Input
                          type="time"
                          value={newMeeting.time}
                          onChange={(e) => setNewMeeting({...newMeeting, time: e.target.value})}
                          className="bg-zinc-800 border-white/10"
                        />
                      </div>
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
                    
                    <Button onClick={handleCreateMeeting} className="w-full">
                      Create Meeting
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          )}

          {/* Meetings List */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-violet-400" />
              Virtual Classes
            </h2>
            
            <div className="space-y-4">
              {meetings.map((meeting) => (
                <div 
                  key={meeting.id}
                  className={`p-5 rounded-xl border transition-all ${
                    meeting.status === 'live' 
                      ? 'bg-red-500/5 border-red-500/30' 
                      : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${getPlatformColor(meeting.platform)}`}>
                        {meeting.platform === 'zoom' ? (
                          <Video className="w-6 h-6" />
                        ) : (
                          <Monitor className="w-6 h-6" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold">{meeting.title}</h3>
                        <p className="text-sm text-zinc-500">Hosted by {meeting.host}</p>
                      </div>
                    </div>
                    {getStatusBadge(meeting.status)}
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-400 mb-4">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(meeting.date).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {meeting.time} ({meeting.duration} min)
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {meeting.participants} participants
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-900/50 mb-4">
                    <span className="text-xs text-zinc-500">Meeting ID:</span>
                    <code className="text-sm font-mono">{meeting.meeting_id}</code>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => copyToClipboard(meeting.meeting_id)}
                      className="ml-auto h-7 px-2"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                  
                  <div className="flex gap-3">
                    {meeting.status === 'live' ? (
                      <Button 
                        onClick={() => window.open(meeting.meeting_url, '_blank')}
                        className="flex-1 bg-red-500 hover:bg-red-600"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Join Now
                      </Button>
                    ) : meeting.status === 'scheduled' ? (
                      <Button 
                        onClick={() => window.open(meeting.meeting_url, '_blank')}
                        className="flex-1"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Open Meeting Link
                      </Button>
                    ) : (
                      <Button 
                        onClick={() => window.open(meeting.recording_url, '_blank')}
                        variant="outline"
                        className="flex-1 border-white/10"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Watch Recording
                      </Button>
                    )}
                    <Button 
                      variant="outline" 
                      onClick={() => copyToClipboard(meeting.meeting_url)}
                      className="border-white/10"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
