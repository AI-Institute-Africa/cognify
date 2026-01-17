import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getStudents } from '../services/api';
import { Users, Search, Filter, Mail, GraduationCap, MoreVertical } from 'lucide-react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
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

export default function StudentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      const data = await getStudents();
      setStudents(data);
    } catch (error) {
      console.error('Failed to load students:', error);
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
      .slice(0, 2) || 'ST';
  };

  const filteredStudents = students.filter(student => {
    const name = student.user?.full_name || '';
    const email = student.user?.email || '';
    const studentId = student.student_id || '';
    const query = searchQuery.toLowerCase();
    return name.toLowerCase().includes(query) || 
           email.toLowerCase().includes(query) ||
           studentId.toLowerCase().includes(query);
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
        title="Students"
        subtitle={`${students.length} students enrolled`}
      />
      
      <div className="p-8">
        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search students..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="student-search-input"
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
            />
          </div>
          
          <Button variant="outline" className="h-12 border-white/10">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>
        
        {/* Students Table */}
        {filteredStudents.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Users className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No students found</h3>
            <p className="text-zinc-500">
              {searchQuery ? 'Try a different search term' : 'No students registered yet'}
            </p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="text-zinc-500">Student</TableHead>
                  <TableHead className="text-zinc-500">Student ID</TableHead>
                  <TableHead className="text-zinc-500">Grade</TableHead>
                  <TableHead className="text-zinc-500">Section</TableHead>
                  <TableHead className="text-zinc-500">GPA</TableHead>
                  <TableHead className="text-zinc-500">Courses</TableHead>
                  <TableHead className="text-zinc-500 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredStudents.map((student) => (
                  <TableRow 
                    key={student.id} 
                    className="border-white/5 hover:bg-white/5"
                    data-testid={`student-row-${student.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback className="bg-gradient-to-br from-blue-500 to-violet-500 text-white text-xs">
                            {getInitials(student.user?.full_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{student.user?.full_name || 'Unknown'}</p>
                          <p className="text-sm text-zinc-500">{student.user?.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-sm text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                        {student.student_id}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-zinc-700 text-zinc-400">
                        {student.grade_level}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-zinc-400">{student.section}</TableCell>
                    <TableCell>
                      <span className={`font-semibold ${
                        student.gpa >= 3.5 ? 'text-emerald-400' :
                        student.gpa >= 3.0 ? 'text-blue-400' :
                        student.gpa >= 2.0 ? 'text-amber-400' : 'text-red-400'
                      }`}>
                        {student.gpa?.toFixed(2) || '0.00'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge className="bg-zinc-800 text-zinc-300">
                        {student.enrolled_courses?.length || 0} enrolled
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
