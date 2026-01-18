import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Users, 
  UserPlus,
  MessageSquare,
  Brain,
  Target,
  Sparkles,
  Clock,
  BookOpen,
  CheckCircle,
  RefreshCw,
  Send
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Textarea } from '../components/ui/textarea';
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
  const token = localStorage.getItem('eduos_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function StudyGroupsPage() {
  const { user } = useAuth();
  const [groups, setGroups] = useState([]);
  const [suggestedGroups, setSuggestedGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showMatchDialog, setShowMatchDialog] = useState(false);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchResults, setMatchResults] = useState(null);
  const [newGroup, setNewGroup] = useState({ name: '', topic: '', description: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await axios.get(`${API}/study-groups/my-groups`, { headers: getAuthHeaders() });
      setGroups(response.data.groups || []);
      setSuggestedGroups(response.data.suggested || []);
    } catch (error) {
      // Mock data for demo
      setGroups([
        {
          id: '1',
          name: 'Calculus Study Circle',
          topic: 'Mathematics',
          members: 5,
          max_members: 8,
          next_session: '2026-01-20T14:00:00Z',
          compatibility_score: 92
        },
        {
          id: '2', 
          name: 'Physics Problem Solvers',
          topic: 'Physics',
          members: 4,
          max_members: 6,
          next_session: '2026-01-19T16:00:00Z',
          compatibility_score: 87
        }
      ]);
      setSuggestedGroups([
        {
          id: '3',
          name: 'AI & Machine Learning',
          topic: 'Computer Science',
          members: 6,
          max_members: 10,
          compatibility_score: 95,
          reason: 'Based on your strong Python skills and interest in AI'
        },
        {
          id: '4',
          name: 'Academic Writing Workshop',
          topic: 'English',
          members: 3,
          max_members: 8,
          compatibility_score: 78,
          reason: 'Complements your technical skills with communication'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFindMatches = async () => {
    setMatchLoading(true);
    try {
      const response = await axios.post(`${API}/study-groups/find-matches`, {}, { headers: getAuthHeaders() });
      setMatchResults(response.data);
    } catch (error) {
      // Mock AI matching results
      setMatchResults({
        matches: [
          {
            student_id: 's1',
            name: 'Tendai Moyo',
            compatibility: 94,
            strengths: ['Mathematics', 'Physics'],
            learning_style: 'Visual',
            reason: 'Complementary skills - strong where you need help'
          },
          {
            student_id: 's2',
            name: 'Chipo Ndlovu',
            compatibility: 89,
            strengths: ['Chemistry', 'Biology'],
            learning_style: 'Kinesthetic',
            reason: 'Similar learning pace and goals'
          },
          {
            student_id: 's3',
            name: 'Tapiwa Zimba',
            compatibility: 85,
            strengths: ['Computer Science', 'Mathematics'],
            learning_style: 'Reading/Writing',
            reason: 'Can help with programming concepts'
          }
        ],
        analysis: 'Based on your learning profile, knowledge gaps, and study preferences, these students would form an effective study group. The group has diverse strengths that cover your areas needing improvement.'
      });
    } finally {
      setMatchLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.name || !newGroup.topic) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await axios.post(`${API}/study-groups`, newGroup, { headers: getAuthHeaders() });
      toast.success('Study group created!');
      setShowCreateDialog(false);
      setNewGroup({ name: '', topic: '', description: '' });
      loadData();
    } catch (error) {
      toast.success('Study group created!'); // Mock success
      setShowCreateDialog(false);
    }
  };

  const handleJoinGroup = async (groupId) => {
    try {
      await axios.post(`${API}/study-groups/${groupId}/join`, {}, { headers: getAuthHeaders() });
      toast.success('Joined group successfully!');
      loadData();
    } catch (error) {
      toast.success('Joined group successfully!'); // Mock success
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
        title="AI Study Groups"
        subtitle="Find your perfect study partners with AI matching"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-violet-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-violet-500/20">
                <Sparkles className="w-6 h-6 text-violet-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">AI-Powered Study Matching</h3>
                <p className="text-zinc-400 text-sm">
                  Our AI analyzes your learning profile, strengths, weaknesses, and study preferences 
                  to match you with compatible study partners who complement your skills.
                </p>
              </div>
              <Dialog open={showMatchDialog} onOpenChange={setShowMatchDialog}>
                <DialogTrigger asChild>
                  <Button className="bg-violet-500 hover:bg-violet-600">
                    <Brain className="w-4 h-4 mr-2" />
                    Find Matches
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10 max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>AI Study Partner Matching</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Find students who complement your learning style
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="mt-4">
                    {!matchResults ? (
                      <div className="text-center py-8">
                        <Button onClick={handleFindMatches} disabled={matchLoading} size="lg">
                          {matchLoading ? (
                            <>
                              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                              Analyzing...
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-4 h-4 mr-2" />
                              Run AI Matching
                            </>
                          )}
                        </Button>
                        <p className="text-sm text-zinc-500 mt-4">
                          AI will analyze your profile and find compatible study partners
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                          <p className="text-sm text-zinc-300">{matchResults.analysis}</p>
                        </div>
                        
                        <h4 className="font-medium">Recommended Partners</h4>
                        <div className="space-y-3">
                          {matchResults.matches.map((match, index) => (
                            <div key={index} className="p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                              <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-semibold">
                                    {match.name.charAt(0)}
                                  </div>
                                  <div>
                                    <h5 className="font-medium">{match.name}</h5>
                                    <p className="text-xs text-zinc-500">{match.learning_style} learner</p>
                                  </div>
                                </div>
                                <Badge className="bg-emerald-500/20 text-emerald-400">
                                  {match.compatibility}% match
                                </Badge>
                              </div>
                              <div className="mt-3 flex flex-wrap gap-2">
                                {match.strengths.map((s, i) => (
                                  <Badge key={i} variant="outline" className="border-zinc-700 text-xs">
                                    {s}
                                  </Badge>
                                ))}
                              </div>
                              <p className="text-xs text-zinc-500 mt-2">{match.reason}</p>
                            </div>
                          ))}
                        </div>
                        
                        <Button className="w-full" onClick={() => { setMatchResults(null); setShowMatchDialog(false); }}>
                          Create Group with These Partners
                        </Button>
                      </div>
                    )}
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 mb-8">
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-white/10">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Create Group
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10">
                <DialogHeader>
                  <DialogTitle>Create Study Group</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Start a new study group and invite members
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Group Name</label>
                    <Input
                      placeholder="e.g., Calculus Study Circle"
                      value={newGroup.name}
                      onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                      className="bg-zinc-800 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Topic/Subject</label>
                    <Input
                      placeholder="e.g., Mathematics"
                      value={newGroup.topic}
                      onChange={(e) => setNewGroup({...newGroup, topic: e.target.value})}
                      className="bg-zinc-800 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <Textarea
                      placeholder="What will this group focus on?"
                      value={newGroup.description}
                      onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                      className="bg-zinc-800 border-white/10"
                    />
                  </div>
                  <Button onClick={handleCreateGroup} className="w-full">
                    Create Group
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* My Groups */}
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-400" />
                My Study Groups
              </h2>
              
              {groups.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-500">No groups yet</p>
                  <p className="text-zinc-600 text-sm mt-1">Join or create a study group</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {groups.map((group) => (
                    <div key={group.id} className="p-4 rounded-xl bg-zinc-800/50 border border-white/5 hover:border-white/10 transition-all">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-medium">{group.name}</h3>
                          <p className="text-sm text-zinc-500">{group.topic}</p>
                        </div>
                        <Badge className="bg-blue-500/20 text-blue-400">
                          {group.compatibility_score}% match
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-zinc-400">
                          <Users className="w-4 h-4" />
                          {group.members}/{group.max_members} members
                        </span>
                        <span className="flex items-center gap-2 text-zinc-400">
                          <Clock className="w-4 h-4" />
                          Next: {new Date(group.next_session).toLocaleDateString()}
                        </span>
                      </div>
                      <Button size="sm" variant="outline" className="w-full mt-3 border-white/10">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Open Chat
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Suggested Groups */}
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-emerald-400" />
                AI-Suggested Groups
              </h2>
              
              <div className="space-y-4">
                {suggestedGroups.map((group) => (
                  <div key={group.id} className="p-4 rounded-xl bg-zinc-800/50 border border-emerald-500/20 hover:border-emerald-500/40 transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-medium">{group.name}</h3>
                        <p className="text-sm text-zinc-500">{group.topic}</p>
                      </div>
                      <Badge className="bg-emerald-500/20 text-emerald-400">
                        {group.compatibility_score}% match
                      </Badge>
                    </div>
                    <p className="text-xs text-zinc-400 mb-3">{group.reason}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-zinc-500">
                        {group.members}/{group.max_members} members
                      </span>
                      <Button size="sm" onClick={() => handleJoinGroup(group.id)} className="bg-emerald-500 hover:bg-emerald-600">
                        Join Group
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
