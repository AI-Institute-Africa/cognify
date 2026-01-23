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
export const careerChat = async (message, context = null, language = 'en', includeAudio = false) => {
  const response = await axios.post(
    `${API}/ai/career-chat`,
    { message, context, language, include_audio: includeAudio },
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

// ==================== PHASE 2 APIs ====================

// Organizations
export const registerOrganization = async (orgData) => {
  const response = await axios.post(`${API}/organizations/register`, orgData);
  return response.data;
};

export const getOrganization = async (orgId) => {
  const response = await axios.get(`${API}/organizations/${orgId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const uploadVerificationDocs = async (orgId, files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  const response = await axios.post(
    `${API}/organizations/${orgId}/upload-verification`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

export const enrollParticipant = async (orgId, userData) => {
  const response = await axios.post(
    `${API}/organizations/${orgId}/enroll-participant`,
    userData,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Knowledge Graph
export const getConcepts = async (subject, gradeLevel) => {
  const params = new URLSearchParams();
  if (subject) params.append('subject', subject);
  if (gradeLevel) params.append('grade_level', gradeLevel);
  const response = await axios.get(`${API}/knowledge/concepts?${params}`, { headers: getAuthHeaders() });
  return response.data;
};

export const getConcept = async (conceptId) => {
  const response = await axios.get(`${API}/knowledge/concepts/${conceptId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const getUserKnowledgeProgress = async () => {
  const response = await axios.get(`${API}/knowledge/user-progress`, { headers: getAuthHeaders() });
  return response.data;
};

export const updateConceptState = async (conceptId, confidence, timeSpent, correct) => {
  const response = await axios.post(
    `${API}/knowledge/concepts/${conceptId}/update-state?confidence=${confidence}&time_spent=${timeSpent}&correct=${correct}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// AI Mentor
export const getMentorProfile = async () => {
  const response = await axios.get(`${API}/mentor/profile`, { headers: getAuthHeaders() });
  return response.data;
};

export const updateMentorProfile = async (profileData) => {
  const params = new URLSearchParams();
  Object.entries(profileData).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });
  const response = await axios.post(`${API}/mentor/profile/update?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const mentorChat = async (message, context = null, language = 'en', includeAudio = false) => {
  const response = await axios.post(
    `${API}/mentor/chat`,
    { message, context, language, include_audio: includeAudio },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getConceptHint = async (conceptId) => {
  const response = await axios.post(
    `${API}/mentor/hint?concept_id=${conceptId}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const teachBack = async (conceptId, explanation) => {
  const response = await axios.post(
    `${API}/mentor/teach-back?concept_id=${conceptId}`,
    { explanation },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Multimodal Content
export const translateContent = async (text, targetLanguage) => {
  const response = await axios.post(
    `${API}/content/translate?text=${encodeURIComponent(text)}&target_language=${targetLanguage}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const generateMultimodalContent = async (conceptId, contentTypes, language = 'en') => {
  const response = await axios.post(
    `${API}/content/generate-multimodal?concept_id=${conceptId}&language=${language}`,
    { content_types: contentTypes },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const analyzeUpload = async (file, question = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (question) formData.append('question', question);
  const response = await axios.post(
    `${API}/content/analyze-upload`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

export const ingestSyllabus = async (file, courseId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  let url = `${API}/content/ingest-syllabus`;
  if (courseId) url += `?course_id=${courseId}`;
  const response = await axios.post(url, formData, {
    headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// Voice & Avatar
export const textToSpeech = async (text, voiceId = null, language = 'en') => {
  const response = await axios.post(
    `${API}/voice/tts`,
    { text, voice_id: voiceId, language },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getAvailableVoices = async () => {
  const response = await axios.get(`${API}/voice/voices`, { headers: getAuthHeaders() });
  return response.data;
};

export const cloneVoice = async (name, description, cloneSource, files) => {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('description', description || '');
  formData.append('clone_source', cloneSource);
  files.forEach(file => formData.append('files', file));
  const response = await axios.post(
    `${API}/voice/clone`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// Languages
export const getSupportedLanguages = async () => {
  const response = await axios.get(`${API}/languages`);
  return response.data;
};

// ==================== PHASE 3 & 4 APIs ====================

// Real Student Dashboard
export const getStudentDashboard = async () => {
  const response = await axios.get(`${API}/dashboard/student-dashboard`, { headers: getAuthHeaders() });
  return response.data;
};

// Messaging
export const getMessages = async () => {
  const response = await axios.get(`${API}/messages`, { headers: getAuthHeaders() });
  return response.data;
};

export const sendMessage = async (recipientId, subject, content) => {
  const response = await axios.post(
    `${API}/messages`,
    { recipient_id: recipientId, subject, content },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getConversation = async (userId) => {
  const response = await axios.get(`${API}/messages/conversation/${userId}`, { headers: getAuthHeaders() });
  return response.data;
};

// Study Groups
export const getStudyGroups = async () => {
  const response = await axios.get(`${API}/study-groups/my-groups`, { headers: getAuthHeaders() });
  return response.data;
};

export const createStudyGroup = async (groupData) => {
  const response = await axios.post(`${API}/study-groups`, groupData, { headers: getAuthHeaders() });
  return response.data;
};

export const joinStudyGroup = async (groupId) => {
  const response = await axios.post(`${API}/study-groups/${groupId}/join`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getGroupChat = async (groupId) => {
  const response = await axios.get(`${API}/study-groups/${groupId}/chat`, { headers: getAuthHeaders() });
  return response.data;
};

export const sendGroupMessage = async (groupId, content) => {
  const response = await axios.post(
    `${API}/study-groups/${groupId}/chat`,
    { content },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const findStudyMatches = async () => {
  const response = await axios.post(`${API}/study-groups/find-matches`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// At-Risk Students
export const getAtRiskStudents = async () => {
  const response = await axios.get(`${API}/students/at-risk`, { headers: getAuthHeaders() });
  return response.data;
};

// Zoom Integration
export const createZoomMeeting = async (topic, duration = 60, startTime = null) => {
  const params = new URLSearchParams({ topic, duration });
  if (startTime) params.append('start_time', startTime);
  const response = await axios.post(`${API}/zoom/create-meeting?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getZoomMeetings = async () => {
  const response = await axios.get(`${API}/zoom/meetings`, { headers: getAuthHeaders() });
  return response.data;
};

// Profile Photo
export const uploadProfilePhoto = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(
    `${API}/users/profile-photo`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// RFID Attendance
export const registerRFID = async (studentId, rfidTag) => {
  const response = await axios.post(
    `${API}/rfid/register`,
    { student_id: studentId, rfid_tag: rfidTag },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const scanRFID = async (rfidTag, deviceId, location) => {
  const response = await axios.post(
    `${API}/rfid/scan`,
    { rfid_tag: rfidTag, device_id: deviceId, location },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getTodayRFIDAttendance = async () => {
  const response = await axios.get(`${API}/rfid/attendance/today`, { headers: getAuthHeaders() });
  return response.data;
};

// Credentials
export const issueCredential = async (credentialData) => {
  const response = await axios.post(`${API}/credentials/issue`, credentialData, { headers: getAuthHeaders() });
  return response.data;
};

export const verifyCredential = async (hash) => {
  const response = await axios.get(`${API}/credentials/verify/${hash}`);
  return response.data;
};

export const getStudentCredentials = async (studentId) => {
  const response = await axios.get(`${API}/credentials/student/${studentId}`, { headers: getAuthHeaders() });
  return response.data;
};

// Report Cards
export const getReportCard = async (studentId) => {
  const response = await axios.get(`${API}/reports/report-card/${studentId}`, { 
    headers: getAuthHeaders(),
    responseType: 'blob'
  });
  return response.data;
};

// ==================== MULTILINGUAL API ====================

export const getSupportedLanguages = async () => {
  const response = await axios.get(`${API}/language/supported`);
  return response.data;
};

export const getUITranslations = async (languageCode) => {
  const response = await axios.get(`${API}/language/translations/${languageCode}`);
  return response.data;
};

export const translateText = async (text, targetLanguage, sourceLanguage = 'en') => {
  const params = new URLSearchParams({ text, target_language: targetLanguage, source_language: sourceLanguage });
  const response = await axios.post(`${API}/language/translate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const detectLanguage = async (text) => {
  const response = await axios.post(`${API}/language/detect?text=${encodeURIComponent(text)}`, {});
  return response.data;
};

// ==================== ADVANCED AI API ====================

// TTS with Emergent LLM Key
export const generateTTS = async (text, voice = 'nova', speed = 1.0) => {
  const params = new URLSearchParams({ text, voice, speed: speed.toString() });
  const response = await axios.post(`${API}/advanced/tts?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Avatar Generation
export const generateAvatar = async (prompt, style = 'professional educator') => {
  const params = new URLSearchParams({ prompt, style });
  const response = await axios.post(`${API}/advanced/avatar/generate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Educational Visual Generation
export const generateVisual = async (concept, visualType = 'diagram', subject = 'general') => {
  const params = new URLSearchParams({ concept, visual_type: visualType, subject });
  const response = await axios.post(`${API}/advanced/visual/generate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Micro-hints
export const getMicroHint = async (concept, learnerBackground = 'general', previousMistakes = [], hintType = 'perspective_shift') => {
  const params = new URLSearchParams({ 
    concept, 
    learner_background: learnerBackground, 
    hint_type: hintType 
  });
  const response = await axios.post(`${API}/advanced/hint?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Analogies
export const getAnalogy = async (concept, learnerBackground = 'general', interests = []) => {
  const params = new URLSearchParams({ concept, learner_background: learnerBackground });
  const response = await axios.post(`${API}/advanced/analogy?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Comprehension Questions
export const getComprehensionQuestions = async (concept, difficulty = 'medium', count = 3) => {
  const params = new URLSearchParams({ concept, difficulty, count: count.toString() });
  const response = await axios.post(`${API}/advanced/comprehension-questions?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Syllabus Ingestion
export const analyzeSyllabus = async (content, contentType = 'syllabus') => {
  const params = new URLSearchParams({ content, content_type: contentType });
  const response = await axios.post(`${API}/advanced/syllabus/analyze?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Interactive Lesson Generation
export const generateLesson = async (topic, learningObjectives, durationMinutes = 30) => {
  const params = new URLSearchParams({ topic, duration_minutes: durationMinutes.toString() });
  learningObjectives.forEach(obj => params.append('learning_objectives', obj));
  const response = await axios.post(`${API}/advanced/lesson/generate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Learn by Teaching - AI Student Interaction
export const teachAIStudent = async (explanation, concept, studentPersonality = 'curious') => {
  const params = new URLSearchParams({ explanation, concept, student_personality: studentPersonality });
  const response = await axios.post(`${API}/advanced/teach/interact?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Teaching Quality Evaluation
export const evaluateTeaching = async (explanation, concept) => {
  const params = new URLSearchParams({ explanation, concept });
  const response = await axios.post(`${API}/advanced/teach/evaluate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Question Analysis
export const analyzeQuestion = async (question, subject = 'general') => {
  const params = new URLSearchParams({ question, subject });
  const response = await axios.post(`${API}/advanced/question/analyze?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Answer Evaluation
export const evaluateAnswer = async (question, answer, subject = 'general') => {
  const params = new URLSearchParams({ question, answer, subject });
  const response = await axios.post(`${API}/advanced/question/evaluate-answer?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Assignment Generation
export const generateAssignment = async (lessonTopic, learningObjectives, assignmentType = 'reflection', difficulty = 'medium') => {
  const params = new URLSearchParams({ 
    lesson_topic: lessonTopic, 
    assignment_type: assignmentType, 
    difficulty 
  });
  learningObjectives.forEach(obj => params.append('learning_objectives', obj));
  const response = await axios.post(`${API}/advanced/assignment/generate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Assignment Submission Evaluation
export const evaluateAssignmentSubmission = async (assignmentId, submission) => {
  const params = new URLSearchParams({ submission });
  const response = await axios.post(`${API}/advanced/assignment/${assignmentId}/evaluate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// Multi-disciplinary Course Generation
export const generateMultidisciplinaryLesson = async (topic, subjects, durationMinutes = 45) => {
  const params = new URLSearchParams({ topic, duration_minutes: durationMinutes.toString() });
  subjects.forEach(sub => params.append('subjects', sub));
  const response = await axios.post(`${API}/advanced/multidisciplinary/generate?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// AIBL - Learner Identity Analysis
export const analyzeIdentity = async () => {
  const response = await axios.get(`${API}/advanced/identity/analyze`, { headers: getAuthHeaders() });
  return response.data;
};

// OFL - Outcome Decomposition
export const decomposeOutcome = async (outcome) => {
  const params = new URLSearchParams({ outcome });
  const response = await axios.post(`${API}/advanced/outcome/decompose?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== MULTIMODAL CONTENT API ====================

export const uploadCourseContent = async (courseId, contentType, title, description = '', contentUrl = '', contentText = '') => {
  const params = new URLSearchParams({ 
    content_type: contentType, 
    title,
    description,
    content_url: contentUrl,
    content_text: contentText
  });
  const response = await axios.post(`${API}/multimodal/course/${courseId}/content?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getCourseContent = async (courseId, contentType = null) => {
  const params = contentType ? `?content_type=${contentType}` : '';
  const response = await axios.get(`${API}/multimodal/course/${courseId}/content${params}`, { headers: getAuthHeaders() });
  return response.data;
};
