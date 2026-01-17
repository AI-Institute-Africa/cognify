import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getGrades, getCourses } from '../services/api';
import { GraduationCap, TrendingUp, TrendingDown, Award, BookOpen } from 'lucide-react';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';

export default function GradesPage() {
  const { user } = useAuth();
  const [grades, setGrades] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [gradesData, coursesData] = await Promise.all([
        getGrades(),
        getCourses()
      ]);
      setGrades(gradesData);
      setCourses(coursesData);
    } catch (error) {
      console.error('Failed to load grades:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLetterGrade = (percentage) => {
    if (percentage >= 90) return { letter: 'A', color: 'text-emerald-400' };
    if (percentage >= 80) return { letter: 'B', color: 'text-blue-400' };
    if (percentage >= 70) return { letter: 'C', color: 'text-amber-400' };
    if (percentage >= 60) return { letter: 'D', color: 'text-orange-400' };
    return { letter: 'F', color: 'text-red-400' };
  };

  const calculateGPA = () => {
    if (grades.length === 0) return 0;
    const total = grades.reduce((sum, g) => sum + (g.score / g.max_score) * 4, 0);
    return (total / grades.length).toFixed(2);
  };

  const groupGradesByCourse = () => {
    const grouped = {};
    grades.forEach(grade => {
      if (!grouped[grade.course_id]) {
        grouped[grade.course_id] = [];
      }
      grouped[grade.course_id].push(grade);
    });
    return grouped;
  };

  const getCourseName = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    return course?.name || 'Unknown Course';
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

  const groupedGrades = groupGradesByCourse();
  const gpa = calculateGPA();

  return (
    <DashboardLayout>
      <Header 
        title="Grades & Report Card"
        subtitle="View your academic performance"
      />
      
      <div className="p-8">
        {/* GPA Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="md:col-span-2 glass-card p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-zinc-500 font-medium">Cumulative GPA</p>
                <h2 className="text-5xl font-bold mt-2 tracking-tight">{gpa}</h2>
                <p className="text-zinc-500 mt-2">Out of 4.00</p>
              </div>
              <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500">
                <GraduationCap className="w-8 h-8 text-white" />
              </div>
            </div>
            <div className="mt-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-500">Progress to Dean's List (3.5)</span>
                <span className="text-blue-400">{Math.min((gpa / 3.5) * 100, 100).toFixed(0)}%</span>
              </div>
              <Progress value={Math.min((gpa / 3.5) * 100, 100)} className="h-3 bg-zinc-800" />
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Total Assessments</p>
                <h3 className="text-3xl font-bold mt-2">{grades.length}</h3>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <Award className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Courses</p>
                <h3 className="text-3xl font-bold mt-2">{Object.keys(groupedGrades).length}</h3>
              </div>
              <div className="p-3 rounded-xl bg-violet-500/20">
                <BookOpen className="w-6 h-6 text-violet-400" />
              </div>
            </div>
          </div>
        </div>
        
        {/* Grades by Course */}
        {Object.keys(groupedGrades).length === 0 ? (
          <div className="glass-card p-12 text-center">
            <GraduationCap className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No grades yet</h3>
            <p className="text-zinc-500">Your grades will appear here once they are entered</p>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedGrades).map(([courseId, courseGrades]) => {
              const avgScore = courseGrades.reduce((sum, g) => sum + (g.score / g.max_score) * 100, 0) / courseGrades.length;
              const { letter, color } = getLetterGrade(avgScore);
              
              return (
                <div key={courseId} className="glass-card overflow-hidden" data-testid={`grade-course-${courseId}`}>
                  <div className="p-6 border-b border-white/5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center">
                          <BookOpen className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold">{getCourseName(courseId)}</h3>
                          <p className="text-sm text-zinc-500">{courseGrades.length} assessments</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-3xl font-bold ${color}`}>{letter}</span>
                        <p className="text-sm text-zinc-500">{avgScore.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  
                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/5 hover:bg-transparent">
                        <TableHead className="text-zinc-500">Assessment</TableHead>
                        <TableHead className="text-zinc-500">Type</TableHead>
                        <TableHead className="text-zinc-500">Score</TableHead>
                        <TableHead className="text-zinc-500">Percentage</TableHead>
                        <TableHead className="text-zinc-500">Grade</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {courseGrades.map((grade) => {
                        const percentage = (grade.score / grade.max_score) * 100;
                        const { letter: gradeLetter, color: gradeColor } = getLetterGrade(percentage);
                        
                        return (
                          <TableRow key={grade.id} className="border-white/5">
                            <TableCell className="font-medium">{grade.assessment_name}</TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-zinc-400 border-zinc-700">
                                {grade.assessment_type}
                              </Badge>
                            </TableCell>
                            <TableCell>{grade.score}/{grade.max_score}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress value={percentage} className="w-20 h-2 bg-zinc-800" />
                                <span className="text-sm">{percentage.toFixed(1)}%</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <span className={`font-bold ${gradeColor}`}>{gradeLetter}</span>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
