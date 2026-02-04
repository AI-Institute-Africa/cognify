import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { StatCard, WideStatCard } from '../components/StatCard';
import { getDashboardStats, getCourses, getAchievements, getTeacherStudentsByCourse } from '../services/api';
import { 
  GraduationCap, 
  BookOpen, 
  Calendar, 
  CreditCard, 
  Trophy, 
  TrendingUp,
  Users,
  Clock,
  Target,
  Sparkles,
  ArrowUpRight,
  Eye,
  Mail,
  FileText
} from 'lucide-react';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [stats, setStats] = useState({});
  const [courses, setCourses] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [teacherCourseStudents, setTeacherCourseStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, coursesData, achievementsData] = await Promise.all([
        getDashboardStats(),
        getCourses().catch(() => []),
        getAchievements().catch(() => [])
      ]);
      setStats(statsData);
      setCourses(coursesData.slice(0, 4));
      setAchievements(achievementsData.slice(0, 3));
      
      // Load teacher-specific data
      if (user?.role === 'teacher') {
        try {
          const teacherData = await getTeacherStudentsByCourse();
          setTeacherCourseStudents(teacherData);
        } catch (e) {
          console.log('Could not load teacher course data');
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('goodMorning');
    if (hour < 18) return t('goodAfternoon');
    return t('goodEvening');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-zinc-500 mt-4">Loading dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title={`${getGreeting()}, ${user?.full_name?.split(' ')[0] || 'User'}!`}
        subtitle={new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
      />
      
      <div className="p-4 sm:p-6 lg:p-8">
        {/* Stats Grid */}
        <div className="bento-grid mb-6 sm:mb-8">
          {user?.role === 'student' && (
            <>
              <WideStatCard
                title="Current GPA"
                value={stats.gpa?.toFixed(2) || '0.00'}
                subtitle="Out of 4.00"
                icon={GraduationCap}
                gradient="from-blue-500 to-cyan-500"
              >
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-zinc-500">Progress to Dean's List (3.5)</span>
                    <span className="text-blue-400">{Math.min((stats.gpa / 3.5) * 100, 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={Math.min((stats.gpa / 3.5) * 100, 100)} className="h-2 bg-zinc-800" />
                </div>
              </WideStatCard>
              
              <StatCard
                title="Enrolled Courses"
                value={stats.enrolled_courses || 0}
                icon={BookOpen}
                iconColor="text-violet-400"
              />
              
              <StatCard
                title="Attendance Rate"
                value={`${stats.attendance_rate || 100}%`}
                change={stats.attendance_rate >= 90 ? 'Excellent' : 'Needs improvement'}
                changeType={stats.attendance_rate >= 90 ? 'up' : 'down'}
                icon={Calendar}
                iconColor="text-emerald-400"
              />
              
              <StatCard
                title="Pending Fees"
                value={`$${(stats.pending_fees || 0).toLocaleString()}`}
                icon={CreditCard}
                iconColor="text-amber-400"
              />
              
              <StatCard
                title="Achievements"
                value={stats.achievements_count || 0}
                icon={Trophy}
                iconColor="text-pink-400"
              />
            </>
          )}
          
          {user?.role === 'teacher' && (
            <>
              <WideStatCard
                title={t('totalStudents')}
                value={stats.total_students || 0}
                subtitle="Across all your classes"
                icon={Users}
                gradient="from-violet-500 to-purple-500"
              />
              
              <StatCard
                title={t('activeCourses')}
                value={stats.total_courses || 0}
                icon={BookOpen}
                iconColor="text-blue-400"
              />
              
              <StatCard
                title="Pending Grades"
                value={stats.pending_grades || 0}
                icon={Target}
                iconColor="text-amber-400"
              />
              
              <StatCard
                title={t('exams')}
                value={stats.total_exams || 0}
                icon={FileText}
                iconColor="text-cyan-400"
              />
            </>
          )}
          
          {user?.role === 'admin' && (
            <>
              <WideStatCard
                title="Total Students"
                value={stats.total_students || 0}
                subtitle="Active enrollments"
                icon={Users}
                gradient="from-blue-500 to-indigo-500"
              />
              
              <StatCard
                title="Teachers"
                value={stats.total_teachers || 0}
                icon={GraduationCap}
                iconColor="text-violet-400"
              />
              
              <StatCard
                title="Courses"
                value={stats.total_courses || 0}
                icon={BookOpen}
                iconColor="text-emerald-400"
              />
              
              <StatCard
                title="Pending Fees"
                value={stats.pending_fees || 0}
                icon={CreditCard}
                iconColor="text-amber-400"
              />
            </>
          )}
          
          {user?.role === 'parent' && (
            <>
              <StatCard
                title="Children"
                value={stats.children_count || 0}
                icon={Users}
                iconColor="text-blue-400"
              />
              
              <StatCard
                title="Pending Fees"
                value={`$${(stats.pending_fees || 0).toLocaleString()}`}
                icon={CreditCard}
                iconColor="text-amber-400"
              />
            </>
          )}
        </div>
        
        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Courses Section */}
          <div className="lg:col-span-2">
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold">
                    {user?.role === 'student' ? 'My Courses' : 'Active Courses'}
                  </h3>
                  <p className="text-sm text-zinc-500 mt-1">Your enrolled courses for this semester</p>
                </div>
                <Link to="/courses">
                  <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
                    View all
                    <ArrowUpRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
              </div>
              
              {courses.length === 0 ? (
                <div className="text-center py-12">
                  <BookOpen className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                  <p className="text-zinc-500">No courses yet</p>
                  <Link to="/courses">
                    <Button className="mt-4" size="sm">
                      Browse Courses
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {courses.map((course, index) => (
                    <div
                      key={course.id}
                      className={`flex items-center justify-between p-4 rounded-xl bg-zinc-900/50 border border-white/5 hover:border-white/10 transition-all animate-fadeIn stagger-${index + 1}`}
                      data-testid={`course-card-${course.id}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center">
                          <BookOpen className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="font-medium">{course.name}</h4>
                          <p className="text-sm text-zinc-500">{course.code} • {course.credits} credits</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-zinc-400 border-zinc-700">
                        {course.grade_level}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Quick Actions & Achievements */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-3">
                {user?.role === 'student' && (
                  <>
                    <Link to="/career" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30 hover:text-blue-400 transition-all">
                        <Sparkles className="w-5 h-5" />
                        AI Career Guidance
                      </Button>
                    </Link>
                    <Link to="/grades" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-violet-500/10 hover:border-violet-500/30 hover:text-violet-400 transition-all">
                        <TrendingUp className="w-5 h-5" />
                        View Report Card
                      </Button>
                    </Link>
                    <Link to="/fees" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-400 transition-all">
                        <CreditCard className="w-5 h-5" />
                        Pay Fees
                      </Button>
                    </Link>
                  </>
                )}
                {user?.role === 'teacher' && (
                  <>
                    <Link to="/lesson-planner" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30 hover:text-blue-400 transition-all">
                        <Sparkles className="w-5 h-5" />
                        AI Lesson Planner
                      </Button>
                    </Link>
                    <Link to="/attendance" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-violet-500/10 hover:border-violet-500/30 hover:text-violet-400 transition-all">
                        <Calendar className="w-5 h-5" />
                        Mark Attendance
                      </Button>
                    </Link>
                    <Link to="/grades" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-400 transition-all">
                        <Target className="w-5 h-5" />
                        Enter Grades
                      </Button>
                    </Link>
                  </>
                )}
                {user?.role === 'admin' && (
                  <>
                    <Link to="/students" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30 hover:text-blue-400 transition-all">
                        <Users className="w-5 h-5" />
                        Manage Students
                      </Button>
                    </Link>
                    <Link to="/courses" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-violet-500/10 hover:border-violet-500/30 hover:text-violet-400 transition-all">
                        <BookOpen className="w-5 h-5" />
                        Manage Courses
                      </Button>
                    </Link>
                    <Link to="/fees" className="block">
                      <Button variant="outline" className="w-full justify-start gap-3 h-12 border-white/10 hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-400 transition-all">
                        <CreditCard className="w-5 h-5" />
                        Finance Overview
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>
            
            {/* Recent Achievements */}
            {user?.role === 'student' && (
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">{t('achievements')}</h3>
                  <Link to="/achievements">
                    <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
                      {t('viewAll')}
                    </Button>
                  </Link>
                </div>
                
                {achievements.length === 0 ? (
                  <div className="text-center py-8">
                    <Trophy className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
                    <p className="text-sm text-zinc-500">No achievements yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {achievements.map((achievement) => (
                      <div
                        key={achievement.id}
                        className="flex items-center gap-3 p-3 rounded-lg bg-zinc-900/50"
                      >
                        <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                          <Trophy className="w-5 h-5 text-amber-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">{achievement.title}</p>
                          <p className="text-xs text-zinc-500">{achievement.category}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Recent Students for Teachers */}
            {user?.role === 'teacher' && stats.recent_students && stats.recent_students.length > 0 && (
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Recent Students</h3>
                  <Link to="/students">
                    <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
                      {t('viewAll')}
                    </Button>
                  </Link>
                </div>
                <div className="space-y-3">
                  {stats.recent_students.map((student) => (
                    <div
                      key={student.id}
                      className="flex items-center gap-3 p-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center overflow-hidden">
                        {student.profile_picture ? (
                          <img src={student.profile_picture} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <Users className="w-5 h-5 text-blue-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{student.full_name}</p>
                        <p className="text-xs text-zinc-500">{student.email}</p>
                      </div>
                      <div className="flex gap-1">
                        <Link to={`/students?view=${student.id}`}>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Eye className="w-4 h-4 text-zinc-400" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Teacher Course Students Section */}
        {user?.role === 'teacher' && teacherCourseStudents.length > 0 && (
          <div className="mt-8">
            <h3 className="text-xl font-semibold mb-4">Students by Course</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {teacherCourseStudents.map((courseData) => (
                <div key={courseData.course.id} className="glass-card p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center">
                      <BookOpen className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-semibold">{courseData.course.title || courseData.course.name}</h4>
                      <p className="text-sm text-zinc-500">{courseData.student_count} students enrolled</p>
                    </div>
                  </div>
                  
                  {courseData.students.length > 0 ? (
                    <div className="space-y-2">
                      {courseData.students.slice(0, 3).map((student) => (
                        <div key={student.id} className="flex items-center justify-between p-2 rounded-lg bg-zinc-900/30">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm">
                              {student.full_name?.charAt(0) || '?'}
                            </div>
                            <div>
                              <p className="text-sm font-medium">{student.full_name}</p>
                              <p className="text-xs text-zinc-500">Avg: {student.average_grade || 0}%</p>
                            </div>
                          </div>
                          <Link to={`/students?view=${student.id}`}>
                            <Button variant="ghost" size="sm" className="h-7 text-xs">
                              View
                            </Button>
                          </Link>
                        </div>
                      ))}
                      {courseData.students.length > 3 && (
                        <p className="text-xs text-center text-zinc-500 pt-2">
                          +{courseData.students.length - 3} more students
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-500 text-center py-4">No students enrolled yet</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
