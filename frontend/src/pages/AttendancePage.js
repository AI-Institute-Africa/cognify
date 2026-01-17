import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getAttendance, getCourses } from '../services/api';
import { Calendar as CalendarIcon, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Calendar } from '../components/ui/calendar';

export default function AttendancePage() {
  const { user } = useAuth();
  const [attendance, setAttendance] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [attendanceData, coursesData] = await Promise.all([
        getAttendance(),
        getCourses()
      ]);
      setAttendance(attendanceData);
      setCourses(coursesData);
    } catch (error) {
      console.error('Failed to load attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'present':
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case 'absent':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'late':
        return <Clock className="w-5 h-5 text-amber-400" />;
      case 'excused':
        return <AlertCircle className="w-5 h-5 text-blue-400" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      present: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      absent: 'bg-red-500/20 text-red-400 border-red-500/30',
      late: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      excused: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    };
    return styles[status] || '';
  };

  const calculateStats = () => {
    if (attendance.length === 0) return { rate: 100, present: 0, absent: 0, late: 0 };
    const present = attendance.filter(a => a.status === 'present').length;
    const absent = attendance.filter(a => a.status === 'absent').length;
    const late = attendance.filter(a => a.status === 'late').length;
    const rate = ((present + late) / attendance.length) * 100;
    return { rate: rate.toFixed(1), present, absent, late };
  };

  const getCourseName = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    return course?.name || 'Unknown Course';
  };

  const getAttendanceDates = () => {
    return attendance.map(a => new Date(a.date));
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

  const stats = calculateStats();

  return (
    <DashboardLayout>
      <Header 
        title="Attendance"
        subtitle="Track your class attendance"
      />
      
      <div className="p-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="md:col-span-2 glass-card p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-zinc-500 font-medium">Attendance Rate</p>
                <h2 className="text-5xl font-bold mt-2 tracking-tight">{stats.rate}%</h2>
                <p className="text-zinc-500 mt-2">
                  {stats.rate >= 90 ? 'Excellent attendance!' : 'Keep improving!'}
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500">
                <CalendarIcon className="w-8 h-8 text-white" />
              </div>
            </div>
            <div className="mt-6">
              <Progress value={parseFloat(stats.rate)} className="h-3 bg-zinc-800" />
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <span className="text-zinc-500">Present</span>
            </div>
            <h3 className="text-3xl font-bold">{stats.present}</h3>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <XCircle className="w-5 h-5 text-red-400" />
              <span className="text-zinc-500">Absent</span>
            </div>
            <h3 className="text-3xl font-bold">{stats.absent}</h3>
          </div>
        </div>
        
        {/* Calendar and Records */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-4">Calendar</h3>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              className="rounded-md"
              modifiers={{
                attended: getAttendanceDates()
              }}
              modifiersStyles={{
                attended: { backgroundColor: 'rgba(16, 185, 129, 0.2)' }
              }}
            />
            <div className="mt-4 flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500/30" />
                <span className="text-zinc-500">Attended</span>
              </div>
            </div>
          </div>
          
          {/* Recent Records */}
          <div className="lg:col-span-2 glass-card p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Records</h3>
            
            {attendance.length === 0 ? (
              <div className="text-center py-12">
                <CalendarIcon className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <p className="text-zinc-500">No attendance records yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {attendance.slice(0, 10).map((record, index) => (
                  <div
                    key={record.id}
                    className={`flex items-center justify-between p-4 rounded-xl bg-zinc-900/50 border border-white/5 animate-fadeIn stagger-${(index % 5) + 1}`}
                    data-testid={`attendance-record-${record.id}`}
                  >
                    <div className="flex items-center gap-4">
                      {getStatusIcon(record.status)}
                      <div>
                        <p className="font-medium">{getCourseName(record.course_id)}</p>
                        <p className="text-sm text-zinc-500">
                          {new Date(record.date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline" className={getStatusBadge(record.status)}>
                      {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
