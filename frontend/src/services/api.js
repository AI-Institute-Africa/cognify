import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('eduos_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Dashboard
export const getDashboardStats = async () => {
  const response = await axios.get(`${API}/dashboard/stats`, { headers: getAuthHeaders() });
  return response.data;
};

// Courses
export const getCourses = async () => {
  const response = await axios.get(`${API}/courses`, { headers: getAuthHeaders() });
  return response.data;
};

export const getCourse = async (courseId) => {
  const response = await axios.get(`${API}/courses/${courseId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const createCourse = async (courseData) => {
  const response = await axios.post(`${API}/courses`, courseData, { headers: getAuthHeaders() });
  return response.data;
};

export const enrollCourse = async (courseId) => {
  const response = await axios.post(`${API}/courses/${courseId}/enroll`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Attendance
export const getAttendance = async (studentId, courseId) => {
  const params = new URLSearchParams();
  if (studentId) params.append('student_id', studentId);
  if (courseId) params.append('course_id', courseId);
  const response = await axios.get(`${API}/attendance?${params}`, { headers: getAuthHeaders() });
  return response.data;
};

export const markAttendance = async (attendanceData) => {
  const response = await axios.post(`${API}/attendance`, attendanceData, { headers: getAuthHeaders() });
  return response.data;
};

// Grades
export const getGrades = async (studentId, courseId) => {
  const params = new URLSearchParams();
  if (studentId) params.append('student_id', studentId);
  if (courseId) params.append('course_id', courseId);
  const response = await axios.get(`${API}/grades?${params}`, { headers: getAuthHeaders() });
  return response.data;
};

export const addGrade = async (gradeData) => {
  const response = await axios.post(`${API}/grades`, gradeData, { headers: getAuthHeaders() });
  return response.data;
};

// Fees
export const getFees = async () => {
  const response = await axios.get(`${API}/fees`, { headers: getAuthHeaders() });
  return response.data;
};

export const createFee = async (feeData) => {
  const response = await axios.post(`${API}/fees`, feeData, { headers: getAuthHeaders() });
  return response.data;
};

export const payFee = async (feeId, amount, paymentMethod = 'card') => {
  const response = await axios.post(
    `${API}/fees/${feeId}/pay?amount=${amount}&payment_method=${paymentMethod}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Achievements
export const getAchievements = async () => {
  const response = await axios.get(`${API}/achievements`, { headers: getAuthHeaders() });
  return response.data;
};

export const createAchievement = async (achievementData) => {
  const response = await axios.post(`${API}/achievements`, achievementData, { headers: getAuthHeaders() });
  return response.data;
};

// Notifications
export const getNotifications = async () => {
  const response = await axios.get(`${API}/notifications`, { headers: getAuthHeaders() });
  return response.data;
};

export const markNotificationRead = async (notificationId) => {
  const response = await axios.post(`${API}/notifications/${notificationId}/read`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Students (Admin/Teacher)
export const getStudents = async () => {
  const response = await axios.get(`${API}/students`, { headers: getAuthHeaders() });
  return response.data;
};

export const getStudent = async (studentId) => {
  const response = await axios.get(`${API}/students/${studentId}`, { headers: getAuthHeaders() });
  return response.data;
};

// Teachers (Admin)
export const getTeachers = async () => {
  const response = await axios.get(`${API}/teachers`, { headers: getAuthHeaders() });
  return response.data;
};

// AI Services
export const careerChat = async (message, context = null) => {
  const response = await axios.post(
    `${API}/ai/career-chat`,
    { message, context },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const lessonPlanner = async (message) => {
  const response = await axios.post(
    `${API}/ai/lesson-planner`,
    { message },
    { headers: getAuthHeaders() }
  );
  return response.data;
};
