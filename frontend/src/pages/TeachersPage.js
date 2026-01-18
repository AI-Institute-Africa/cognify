import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getTeachers } from '../services/api';
import { GraduationCap, Search, Filter, Mail, BookOpen, MoreVertical, Building } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';

export default function TeachersPage() {
  const { user } = useAuth();
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTeachers();
  }, []);

  const loadTeachers = async () => {
    try {
      const data = await getTeachers();
      setTeachers(data);
    } catch (error) {
      console.error('Failed to load teachers:', error);
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name) => {
    return name
      ?.split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'TC';
  };

  const filteredTeachers = teachers.filter(teacher => {
    const name = teacher.user?.full_name || '';
    const email = teacher.user?.email || '';
    const department = teacher.department || '';
    const query = searchQuery.toLowerCase();
    return name.toLowerCase().includes(query) || 
           email.toLowerCase().includes(query) ||
           department.toLowerCase().includes(query);
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
        title="Teachers"
        subtitle={`${teachers.length} teachers on staff`}
      />
      
      <div className="p-8">
        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search teachers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="teacher-search-input"
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
            />
          </div>
          
          <Button variant="outline" className="h-12 border-white/10">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>
        
        {/* Teachers Table */}
        {filteredTeachers.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <GraduationCap className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No teachers found</h3>
            <p className="text-zinc-500">
              {searchQuery ? 'Try a different search term' : 'No teachers registered yet'}
            </p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-zinc-500">Teacher</TableHead>
                  <TableHead className="text-zinc-500">Employee ID</TableHead>
                  <TableHead className="text-zinc-500">Department</TableHead>
                  <TableHead className="text-zinc-500">Subjects</TableHead>
                  <TableHead className="text-zinc-500">Courses</TableHead>
                  <TableHead className="text-zinc-500 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTeachers.map((teacher) => (
                  <TableRow 
                    key={teacher.id} 
                    className="border-white/5 hover:bg-white/5"
                    data-testid={`teacher-row-${teacher.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback className="bg-gradient-to-br from-violet-500 to-purple-500 text-white text-xs">
                            {getInitials(teacher.user?.full_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{teacher.user?.full_name || 'Unknown'}</p>
                          <p className="text-sm text-zinc-500">{teacher.user?.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-sm text-violet-400 bg-violet-500/10 px-2 py-1 rounded">
                        {teacher.employee_id}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Building className="w-4 h-4 text-zinc-500" />
                        <span>{teacher.department}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {teacher.subjects?.slice(0, 2).map((subject, idx) => (
                          <Badge key={idx} variant="outline" className="border-zinc-700 text-zinc-400 text-xs">
                            {subject}
                          </Badge>
                        ))}
                        {teacher.subjects?.length > 2 && (
                          <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-xs">
                            +{teacher.subjects.length - 2}
                          </Badge>
                        )}
                        {(!teacher.subjects || teacher.subjects.length === 0) && (
                          <span className="text-zinc-500 text-sm">No subjects</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-zinc-800 text-zinc-300">
                        {teacher.assigned_courses?.length || 0} assigned
                      </Badge>
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
                            <GraduationCap className="w-4 h-4 mr-2" />
                            View Profile
                          </DropdownMenuItem>
                          <DropdownMenuItem className="cursor-pointer">
                            <BookOpen className="w-4 h-4 mr-2" />
                            Assign Courses
                          </DropdownMenuItem>
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
