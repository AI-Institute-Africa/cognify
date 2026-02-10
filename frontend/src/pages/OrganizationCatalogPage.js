import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Building2,
  BookOpen,
  Users,
  Search,
  Clock,
  GraduationCap,
  Sparkles,
  ArrowRight,
  Plus,
  CheckCircle,
  Filter,
  Eye
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OrganizationCatalogPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [organization, setOrganization] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [enrolledCourseIds, setEnrolledCourseIds] = useState([]);

  useEffect(() => {
    loadOrganizationCatalog();
  }, []);

  const loadOrganizationCatalog = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      
      // Load organization info
      const orgResponse = await fetch(`${API}/api/org/my-organization`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (orgResponse.ok) {
        const orgData = await orgResponse.json();
        setOrganization(orgData);
      }

      // Load organization courses (strictly isolated)
      const coursesResponse = await fetch(`${API}/api/org/catalog`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (coursesResponse.ok) {
        const coursesData = await coursesResponse.json();
        setCourses(coursesData.courses || []);
        setEnrolledCourseIds(coursesData.enrolled_ids || []);
      }
    } catch (error) {
      console.error('Failed to load catalog:', error);
      toast.error('Failed to load organization catalog');
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async (courseId) => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/courses/${courseId}/enroll`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Enrolled successfully!');
        loadOrganizationCatalog();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to enroll');
      }
    } catch (error) {
      toast.error('Failed to enroll in course');
    }
  };

  const filteredCourses = courses.filter(course => {
    const matchesSearch = 
      course.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || course.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const isOrgAdmin = user?.role === 'org_admin';
  const isOrgStaff = user?.role === 'org_staff' || user?.organization_role === 'staff';

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
        title={organization?.name ? `${organization.name} Catalog` : 'Organization Catalog'}
        subtitle={`${courses.length} courses available in your organization`}
      />
      
      <div className="p-4 sm:p-6 lg:p-8">
        {/* Organization Banner */}
        {organization && (
          <div className="mb-6 p-6 rounded-xl bg-gradient-to-r from-blue-500/10 to-violet-500/10 border border-blue-500/20">
            <div className="flex items-start gap-4">
              {organization.logo_url ? (
                <img 
                  src={organization.logo_url} 
                  alt={organization.name}
                  className="w-16 h-16 rounded-xl object-cover"
                />
              ) : (
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
                  <Building2 className="w-8 h-8 text-white" />
                </div>
              )}
              <div className="flex-1">
                <h2 className="text-xl font-bold">{organization.name}</h2>
                <p className="text-zinc-400 text-sm mt-1">{organization.description || 'Organization learning portal'}</p>
                <div className="flex flex-wrap gap-3 mt-3">
                  <Badge className="bg-blue-500/20 text-blue-400">
                    <Users className="w-3 h-3 mr-1" />
                    {organization.stats?.students || 0} Students
                  </Badge>
                  <Badge className="bg-violet-500/20 text-violet-400">
                    <BookOpen className="w-3 h-3 mr-1" />
                    {courses.length} Courses
                  </Badge>
                  <Badge className="bg-emerald-500/20 text-emerald-400">
                    <GraduationCap className="w-3 h-3 mr-1" />
                    {organization.stats?.certificates || 0} Certificates Issued
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search organization courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
              data-testid="org-catalog-search"
            />
          </div>
          
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-[180px] h-12 bg-zinc-900/50 border-white/10">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-white/10">
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="certificate">Certificate</SelectItem>
              <SelectItem value="certification">Certification</SelectItem>
              <SelectItem value="diploma">Diploma</SelectItem>
              <SelectItem value="training">Training</SelectItem>
              <SelectItem value="workshop">Workshop</SelectItem>
            </SelectContent>
          </Select>

          {(isOrgAdmin || isOrgStaff) && (
            <Button 
              onClick={() => navigate('/create-custom-course')}
              className="h-12 bg-violet-500 hover:bg-violet-600"
              data-testid="add-course-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Course
            </Button>
          )}
        </div>

        {/* Courses Grid */}
        {filteredCourses.length === 0 ? (
          <div className="text-center py-20">
            <Building2 className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No courses found</h3>
            <p className="text-zinc-500 mb-4">
              {searchQuery 
                ? 'Try adjusting your search' 
                : 'Your organization has not added any courses yet.'}
            </p>
            {(isOrgAdmin || isOrgStaff) && (
              <Button 
                onClick={() => navigate('/create-custom-course')}
                className="bg-violet-500 hover:bg-violet-600"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add First Course
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course, index) => {
              const isEnrolled = enrolledCourseIds.includes(course.id);
              return (
                <div
                  key={course.id}
                  className={`glass-card p-6 hover:border-white/20 transition-all duration-300 group animate-fadeIn stagger-${(index % 5) + 1}`}
                  data-testid={`org-course-card-${course.id}`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <BookOpen className="w-7 h-7 text-blue-400" />
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {isEnrolled && (
                        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Enrolled
                        </Badge>
                      )}
                      <Badge className="bg-blue-500/20 text-blue-400">
                        <Building2 className="w-3 h-3 mr-1" />
                        Org Course
                      </Badge>
                      {course.price > 0 && (
                        <span className="text-lg font-bold text-emerald-400">${course.price}</span>
                      )}
                    </div>
                  </div>
                  
                  <h3 className="text-lg font-semibold mb-2">{course.name || course.title}</h3>
                  <p className="text-sm text-zinc-500 mb-4 line-clamp-2">{course.description}</p>
                  
                  <div className="flex items-center gap-4 text-sm text-zinc-500 mb-4">
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {course.duration_weeks || 4} weeks
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {course.enrolled_count || 0} enrolled
                    </span>
                  </div>
                  
                  {isEnrolled ? (
                    <Button
                      onClick={() => navigate(`/course/${course.id}`)}
                      className="w-full bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500 hover:text-white border border-emerald-500/30"
                      data-testid={`view-org-course-${course.id}`}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Course
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleEnroll(course.id)}
                      className="w-full bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white border border-blue-500/30"
                      data-testid={`enroll-org-course-${course.id}`}
                    >
                      Enroll Now
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Organization Notice */}
        <div className="mt-8 p-4 rounded-xl bg-zinc-800/50 border border-white/5">
          <p className="text-xs text-zinc-500 text-center">
            These courses are exclusively available to members of {organization?.name || 'your organization'}.
            Courses and content are not visible outside the organization.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
