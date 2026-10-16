import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getStudents } from '../services/api';
import { Users, Search, Mail, BookOpen, MoreVertical, Calendar, CheckCircle } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';

export default function StudentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => { loadStudents(); }, []);

  const loadStudents = async () => {
    try {
      const data = await getStudents();
      setStudents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load participants:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name) => {
    return (name || '').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'ST';
  };

  const filteredStudents = students.filter(s => {
    const name = s.full_name || s.user?.full_name || '';
    const email = s.email || s.user?.email || '';
    const q = searchQuery.toLowerCase();
    return name.toLowerCase().includes(q) || email.toLowerCase().includes(q);
  });

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
        title="Participants"
        subtitle={`${students.length} participant${students.length !== 1 ? 's' : ''} in your organization`}
      />
      
      <div className="p-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card p-4" data-testid="total-participants-stat">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Total Participants</p>
            <p className="text-2xl font-bold mt-1">{students.length}</p>
          </div>
          <div className="glass-card p-4" data-testid="active-stat">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Active</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {students.filter(s => s.org_status === 'approved').length}
            </p>
          </div>
          <div className="glass-card p-4" data-testid="enrolled-stat">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">With Courses</p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {students.filter(s => (s.enrolled_courses?.length || 0) > 0).length}
            </p>
          </div>
          <div className="glass-card p-4" data-testid="pending-stat">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Pending</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">
              {students.filter(s => s.org_status === 'pending').length}
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search participants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="participant-search-input"
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
            />
          </div>
        </div>
        
        {filteredStudents.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Users className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No participants found</h3>
            <p className="text-zinc-500">
              {searchQuery ? 'Try a different search term' : 'Use Bulk Enroll to add participants to your organization.'}
            </p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden" data-testid="participants-table">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-zinc-500">Participant</TableHead>
                  <TableHead className="text-zinc-500">Status</TableHead>
                  <TableHead className="text-zinc-500">Courses Enrolled</TableHead>
                  <TableHead className="text-zinc-500">Joined</TableHead>
                  <TableHead className="text-zinc-500 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredStudents.map((student) => (
                  <TableRow 
                    key={student.id} 
                    className="border-white/5 hover:bg-white/5"
                    data-testid={`participant-row-${student.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback className="bg-gradient-to-br from-blue-500 to-violet-500 text-white text-xs">
                            {getInitials(student.full_name || student.user?.full_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{student.full_name || student.user?.full_name || 'Unknown'}</p>
                          <p className="text-sm text-zinc-500">{student.email || student.user?.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={student.org_status === 'approved' 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-amber-500/20 text-amber-400'
                      }>
                        {student.org_status === 'approved' ? (
                          <><CheckCircle className="w-3 h-3 mr-1" /> Active</>
                        ) : 'Pending'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-zinc-500" />
                        <span>{student.enrolled_courses?.length || 0} courses</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-zinc-400 text-sm">
                        <Calendar className="w-3.5 h-3.5" />
                        {student.created_at ? new Date(student.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-zinc-900 border-white/10">
                          <DropdownMenuItem className="cursor-pointer">
                            <Mail className="w-4 h-4 mr-2" />
                            Send Message
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
