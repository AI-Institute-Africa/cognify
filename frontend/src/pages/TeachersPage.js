import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getTeachers } from '../services/api';
import { GraduationCap, Search, Mail, BookOpen, MoreVertical, Shield, Calendar, CheckCircle } from 'lucide-react';
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

export default function TeachersPage() {
  const { user } = useAuth();
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => { loadTeachers(); }, []);

  const loadTeachers = async () => {
    try {
      const data = await getTeachers();
      setTeachers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load staff:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name) => {
    return (name || '').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'TF';
  };

  const filteredTeachers = teachers.filter(t => {
    const name = t.full_name || t.user?.full_name || '';
    const email = t.email || t.user?.email || '';
    const q = searchQuery.toLowerCase();
    return name.toLowerCase().includes(q) || email.toLowerCase().includes(q);
  });

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Staff"
        subtitle={`${teachers.length} staff member${teachers.length !== 1 ? 's' : ''} in your organization`}
      />
      
      <div className="p-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card p-4" data-testid="total-staff-stat">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Total Staff</p>
            <p className="text-2xl font-bold mt-1">{teachers.length}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Teachers</p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {teachers.filter(t => t.role === 'teacher').length}
            </p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Admins</p>
            <p className="text-2xl font-bold text-violet-400 mt-1">
              {teachers.filter(t => t.role === 'org_admin').length}
            </p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Total Courses</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {teachers.reduce((sum, t) => sum + (t.courses_count || 0), 0)}
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search staff..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="staff-search-input"
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
            />
          </div>
        </div>
        
        {filteredTeachers.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <GraduationCap className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No staff found</h3>
            <p className="text-zinc-500">
              {searchQuery ? 'Try a different search term' : 'Invite staff via the Org Dashboard.'}
            </p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden" data-testid="staff-table">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-zinc-500">Staff Member</TableHead>
                  <TableHead className="text-zinc-500">Role</TableHead>
                  <TableHead className="text-zinc-500">Courses</TableHead>
                  <TableHead className="text-zinc-500">Permissions</TableHead>
                  <TableHead className="text-zinc-500">Joined</TableHead>
                  <TableHead className="text-zinc-500 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTeachers.map((teacher) => (
                  <TableRow 
                    key={teacher.id} 
                    className="border-white/5 hover:bg-white/5"
                    data-testid={`staff-row-${teacher.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white text-xs">
                            {getInitials(teacher.full_name || teacher.user?.full_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{teacher.full_name || teacher.user?.full_name || 'Unknown'}</p>
                          <p className="text-sm text-zinc-500">{teacher.email || teacher.user?.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={teacher.role === 'org_admin' 
                        ? 'bg-violet-500/20 text-violet-400' 
                        : 'bg-blue-500/20 text-blue-400'
                      }>
                        {teacher.role === 'org_admin' ? (
                          <><Shield className="w-3 h-3 mr-1" /> Admin</>
                        ) : (
                          <><GraduationCap className="w-3 h-3 mr-1" /> Teacher</>
                        )}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-zinc-500" />
                        <span>{teacher.courses_count || 0} courses</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {teacher.rights?.can_create_courses && (
                          <Badge className="bg-emerald-500/10 text-emerald-400 text-[10px]">Create</Badge>
                        )}
                        {teacher.rights?.can_manage_participants && (
                          <Badge className="bg-blue-500/10 text-blue-400 text-[10px]">Manage</Badge>
                        )}
                        {teacher.rights?.can_upload_content && (
                          <Badge className="bg-amber-500/10 text-amber-400 text-[10px]">Upload</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-zinc-400 text-sm">
                        <Calendar className="w-3.5 h-3.5" />
                        {teacher.created_at ? new Date(teacher.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
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
