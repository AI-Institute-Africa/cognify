import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import {
  BookOpen, Users, TrendingUp, TrendingDown, AlertTriangle,
  Award, BarChart3, Activity, RefreshCw, GraduationCap, Mail,
  CheckCircle, Clock, Loader2
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CourseAnalyticsDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState(null);
  const [selectedCourseId, setSelectedCourseId] = useState('all');

  useEffect(() => {
    loadAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAnalytics = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const res = await axios.get(`${API}/api/analytics/course-dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res.data);
    } catch (e) {
      console.error('Analytics load error', e);
      toast.error(e.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    toast.success('Analytics refreshed');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  const summary = data?.summary || {};
  const perCourse = data?.per_course || [];
  const atRisk = data?.at_risk || [];
  const topStudents = data?.top_students || [];
  const trend = data?.engagement_trend || [];

  const filteredCourses = selectedCourseId === 'all'
    ? perCourse
    : perCourse.filter(c => c.course_id === selectedCourseId);

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  const completionPieData = [
    { name: 'Completed', value: summary.total_completed || 0 },
    { name: 'In Progress', value: Math.max((summary.total_enrolled || 0) - (summary.total_completed || 0), 0) },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Course Analytics Dashboard"
        subtitle={data?.scope === 'teacher' ? 'Insights for your courses' : 'Organization-wide course insights'}
      />

      <div className="p-6 space-y-6" data-testid="course-analytics-dashboard">
        {/* Top action bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-blue-500/20">
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Performance overview</h3>
              <p className="text-sm text-zinc-400">
                {summary.total_courses || 0} courses · {summary.active_students || 0} students tracked
              </p>
            </div>
          </div>
          <Button
            data-testid="refresh-analytics-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            className="border-white/10"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Summary stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="summary-stats">
          <StatCard
            icon={<BookOpen className="w-5 h-5 text-blue-400" />}
            label="Total Courses"
            value={summary.total_courses || 0}
            tone="blue"
            testid="stat-total-courses"
          />
          <StatCard
            icon={<Users className="w-5 h-5 text-violet-400" />}
            label="Enrolled Students"
            value={summary.total_enrolled || 0}
            tone="violet"
            testid="stat-total-enrolled"
          />
          <StatCard
            icon={<CheckCircle className="w-5 h-5 text-emerald-400" />}
            label="Completion Rate"
            value={`${summary.completion_rate || 0}%`}
            tone="emerald"
            testid="stat-completion-rate"
          />
          <StatCard
            icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
            label="At-Risk Students"
            value={summary.at_risk_count || 0}
            tone="amber"
            testid="stat-at-risk"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            icon={<Award className="w-5 h-5 text-amber-400" />}
            label="Avg Grade"
            value={`${summary.avg_grade || 0}%`}
            tone="amber"
            testid="stat-avg-grade"
          />
          <StatCard
            icon={<GraduationCap className="w-5 h-5 text-emerald-400" />}
            label="Pass Rate"
            value={`${summary.pass_rate || 0}%`}
            tone="emerald"
            testid="stat-pass-rate"
          />
          <StatCard
            icon={<Activity className="w-5 h-5 text-blue-400" />}
            label="Active Students"
            value={summary.active_students || 0}
            tone="blue"
            testid="stat-active-students"
          />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Engagement trend */}
          <div className="glass-card p-5 lg:col-span-2" data-testid="engagement-trend-chart">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold">Engagement Trend</h3>
                <p className="text-xs text-zinc-500">Quiz attempts & passes — last 14 days</p>
              </div>
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" stroke="#71717a" fontSize={11} tickFormatter={(d) => d.slice(5)} />
                <YAxis stroke="#71717a" fontSize={11} />
                <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }} />
                <Legend />
                <Line type="monotone" dataKey="attempts" stroke="#3b82f6" strokeWidth={2} dot={false} name="Attempts" />
                <Line type="monotone" dataKey="passes" stroke="#10b981" strokeWidth={2} dot={false} name="Passes" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Completion donut */}
          <div className="glass-card p-5" data-testid="completion-pie-chart">
            <h3 className="font-semibold mb-1">Course Completion</h3>
            <p className="text-xs text-zinc-500 mb-4">Across enrolled students</p>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={completionPieData}
                  cx="50%" cy="50%"
                  innerRadius={50} outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {completionPieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <p className="text-center text-xs text-zinc-500 mt-2">
              {summary.completion_rate || 0}% completion rate
            </p>
          </div>
        </div>

        {/* Per-Course Performance */}
        <div className="glass-card p-5" data-testid="per-course-table">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Per-Course Performance</h3>
              <p className="text-xs text-zinc-500">Click a row to filter the dashboard</p>
            </div>
            {selectedCourseId !== 'all' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSelectedCourseId('all')}
                data-testid="clear-course-filter-btn"
              >
                Clear filter
              </Button>
            )}
          </div>

          {perCourse.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
              No courses found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-zinc-400 border-b border-white/10">
                  <tr>
                    <th className="py-2 px-3">Course</th>
                    <th className="py-2 px-3">Enrolled</th>
                    <th className="py-2 px-3">Completed</th>
                    <th className="py-2 px-3">Completion</th>
                    <th className="py-2 px-3">Avg Grade</th>
                    <th className="py-2 px-3">Pass Rate</th>
                    <th className="py-2 px-3">Attempts</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCourses.map((c) => (
                    <tr
                      key={c.course_id}
                      onClick={() => setSelectedCourseId(selectedCourseId === c.course_id ? 'all' : c.course_id)}
                      className={`border-b border-white/5 cursor-pointer hover:bg-white/5 transition ${
                        selectedCourseId === c.course_id ? 'bg-blue-500/10' : ''
                      }`}
                      data-testid={`course-row-${c.course_id}`}
                    >
                      <td className="py-3 px-3 font-medium">{c.course_name}</td>
                      <td className="py-3 px-3">{c.enrolled}</td>
                      <td className="py-3 px-3">{c.completed}</td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <Progress value={c.completion_rate} className="w-24 h-2" />
                          <span className="text-xs text-zinc-400">{c.completion_rate}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <Badge className={
                          c.avg_grade >= 75 ? 'bg-emerald-500/20 text-emerald-300' :
                          c.avg_grade >= 50 ? 'bg-amber-500/20 text-amber-300' :
                          c.avg_grade > 0 ? 'bg-red-500/20 text-red-300' :
                          'bg-zinc-700/40 text-zinc-400'
                        }>
                          {c.avg_grade}%
                        </Badge>
                      </td>
                      <td className="py-3 px-3">{c.pass_rate}%</td>
                      <td className="py-3 px-3">{c.quiz_attempts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Bar chart of avg grade per course */}
          {filteredCourses.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold mb-3 text-zinc-300">Avg Grade by Course</h4>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={filteredCourses.slice(0, 12)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="course_name" stroke="#71717a" fontSize={10} interval={0} angle={-15} textAnchor="end" height={60} />
                  <YAxis stroke="#71717a" fontSize={11} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }} />
                  <Bar dataKey="avg_grade" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Avg Grade %" />
                  <Bar dataKey="pass_rate" fill="#10b981" radius={[4, 4, 0, 0]} name="Pass Rate %" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* At-risk + Top students */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* At-risk */}
          <div className="glass-card p-5" data-testid="at-risk-panel">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <h3 className="font-semibold">At-Risk Students</h3>
              </div>
              <Badge className="bg-amber-500/20 text-amber-300">{atRisk.length}</Badge>
            </div>

            {atRisk.length === 0 ? (
              <div className="text-center py-10 text-zinc-500">
                <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <p>No at-risk students detected</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {atRisk.map((s) => (
                  <div
                    key={s.student_id}
                    className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20"
                    data-testid={`at-risk-${s.student_id}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{s.name}</p>
                          <span className="text-xs text-zinc-500">{s.email}</span>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {s.reasons.map((r, i) => (
                            <Badge key={i} className="bg-red-500/15 text-red-300 text-[10px]">
                              {r}
                            </Badge>
                          ))}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-zinc-400">
                          <span>Grade: <span className="text-zinc-200">{s.avg_grade}%</span></span>
                          <span>Progress: <span className="text-zinc-200">{s.progress_pct}%</span></span>
                          {s.inactive_days !== null && (
                            <span><Clock className="w-3 h-3 inline mr-1" />{s.inactive_days}d</span>
                          )}
                        </div>
                      </div>
                      <a
                        href={`mailto:${s.email}`}
                        className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition"
                        data-testid={`email-at-risk-${s.student_id}`}
                        title="Email student"
                      >
                        <Mail className="w-4 h-4 text-zinc-300" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top students */}
          <div className="glass-card p-5" data-testid="top-students-panel">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold">Top Performers</h3>
              </div>
              <Badge className="bg-emerald-500/20 text-emerald-300">{topStudents.length}</Badge>
            </div>

            {topStudents.length === 0 ? (
              <div className="text-center py-10 text-zinc-500">
                <TrendingDown className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>Not enough data yet</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                {topStudents.map((s, i) => (
                  <div
                    key={s.student_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/40 border border-white/5"
                    data-testid={`top-student-${s.student_id}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        i === 0 ? 'bg-amber-500/30 text-amber-300' :
                        i === 1 ? 'bg-zinc-400/30 text-zinc-200' :
                        i === 2 ? 'bg-orange-500/30 text-orange-300' :
                        'bg-zinc-700/40 text-zinc-400'
                      }`}>
                        {i + 1}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-zinc-500">{s.quiz_attempts} quiz attempts</p>
                      </div>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-300">{s.avg_grade}%</Badge>
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

function StatCard({ icon, label, value, tone, testid }) {
  const toneMap = {
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20',
    violet: 'from-violet-500/10 to-violet-500/5 border-violet-500/20',
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/20',
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/20',
  };
  return (
    <div
      className={`glass-card p-5 bg-gradient-to-br ${toneMap[tone] || toneMap.blue}`}
      data-testid={testid}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 rounded-lg bg-white/5">{icon}</div>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-zinc-400 mt-1">{label}</p>
    </div>
  );
}
