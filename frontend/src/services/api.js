import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => {
  const token = localStorage.getItem('cognify_token');
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
  const response = await axios.put(`${API}/mentor/profile`, profileData, { headers: getAuthHeaders() });
  return response.data;
};

export const analyzeLinkedInProfile = async () => {
  const response = await axios.post(`${API}/mentor/analyze-linkedin`, {}, { headers: getAuthHeaders() });
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

export const ingestSyllabusText = async (text, courseId = null) => {
  const params = new URLSearchParams({ text });
  if (courseId) params.append('course_id', courseId);
  const response = await axios.post(`${API}/content/ingest-syllabus-text?${params}`, {}, { headers: getAuthHeaders() });
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
  const response = await axios.post(`${API}/content/course/${courseId}/content?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const uploadCourseFile = async (courseId, file, title, description = '', contentType = '') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  if (description) formData.append('description', description);
  if (contentType) formData.append('content_type', contentType);
  
  const response = await axios.post(`${API}/content/course/${courseId}/upload-file`, formData, {
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const getCourseContent = async (courseId, contentType = null) => {
  const params = contentType ? `?content_type=${contentType}` : '';
  const response = await axios.get(`${API}/content/course/${courseId}/content${params}`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== EXAMS API ====================
export const getExams = async () => {
  const response = await axios.get(`${API}/exams`, { headers: getAuthHeaders() });
  return response.data;
};

export const createExam = async (examData) => {
  const response = await axios.post(`${API}/exams`, examData, { headers: getAuthHeaders() });
  return response.data;
};

export const getExamById = async (examId) => {
  const response = await axios.get(`${API}/exams/${examId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const submitExam = async (examId, submission) => {
  const response = await axios.post(`${API}/exams/${examId}/submit`, submission, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== PAYMENTS API ====================
export const initiatePayment = async (paymentData) => {
  const response = await axios.post(`${API}/payments/initiate`, paymentData, { headers: getAuthHeaders() });
  return response.data;
};

export const confirmPayment = async (paymentId) => {
  const response = await axios.post(`${API}/payments/confirm/${paymentId}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getPaymentHistory = async () => {
  const response = await axios.get(`${API}/payments/history`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== ASSIGNMENTS API ====================
export const getAssignments = async () => {
  const response = await axios.get(`${API}/assignments`, { headers: getAuthHeaders() });
  return response.data;
};

export const createAssignment = async (title, courseId, description = '', dueDate = null, maxScore = 100) => {
  const params = new URLSearchParams({ title, course_id: courseId, max_score: maxScore.toString() });
  if (description) params.append('description', description);
  if (dueDate) params.append('due_date', dueDate);
  const response = await axios.post(`${API}/assignments/create?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getCourseAssignments = async (courseId) => {
  const response = await axios.get(`${API}/assignments/course/${courseId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const submitAssignment = async (assignmentId, content) => {
  const response = await axios.post(
    `${API}/assignments/${assignmentId}/submit?content=${encodeURIComponent(content)}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getAssignmentSubmissions = async (assignmentId) => {
  const response = await axios.get(`${API}/assignments/${assignmentId}/submissions`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== WHATSAPP SHARING ====================
export const shareViaWhatsApp = (text, url = '') => {
  const message = encodeURIComponent(`${text}\n${url}`);
  window.open(`https://wa.me/?text=${message}`, '_blank');
};

// ==================== KNOWLEDGE GRAPH API ====================
export const generateConceptsFromCourses = async () => {
  const response = await axios.post(`${API}/knowledge/generate-from-courses`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== OUTCOME LEARNING API ====================
export const startOutcomeLearning = async (pathwayId) => {
  const response = await axios.post(`${API}/advanced/outcome/start-learning/${pathwayId}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getOutcomePathways = async () => {
  const response = await axios.get(`${API}/advanced/outcome/pathways`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== VIDEO & SLIDES GENERATION ====================
export const generateVideoContent = async (topic, courseId = null, duration = 4) => {
  const params = new URLSearchParams({ topic, duration: duration.toString() });
  if (courseId) params.append('course_id', courseId);
  const response = await axios.post(`${API}/content/generate-video?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const generateSlidesContent = async (topic, courseId = null, slideCount = 5) => {
  const params = new URLSearchParams({ topic, slide_count: slideCount.toString() });
  if (courseId) params.append('course_id', courseId);
  const response = await axios.post(`${API}/content/generate-slides?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== AVATAR & VOICE SETTINGS ====================
export const getPresetVoices = async () => {
  const response = await axios.get(`${API}/voice/preset-voices`, { headers: getAuthHeaders() });
  return response.data;
};

export const cloneVoiceSimple = async (name, voiceSampleUrl = null) => {
  const params = new URLSearchParams({ name });
  if (voiceSampleUrl) params.append('voice_sample_url', voiceSampleUrl);
  const response = await axios.post(`${API}/voice/clone-simple?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const saveAvatarSettings = async (settings) => {
  const params = new URLSearchParams();
  Object.entries(settings).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      params.append(key, value.toString());
    }
  });
  const response = await axios.post(`${API}/voice/save-avatar-settings?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getAvatarSettings = async () => {
  const response = await axios.get(`${API}/voice/avatar-settings`, { headers: getAuthHeaders() });
  return response.data;
};

export const avatarTeachLesson = async (lessonId, voiceId = 'nova') => {
  const response = await axios.post(`${API}/content/lesson/${lessonId}/avatar-teach?voice_id=${voiceId}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== STUDENT VIRTUAL CLASSROOM ====================
export const getStudentMeetings = async () => {
  const response = await axios.get(`${API}/zoom/student-meetings`, { headers: getAuthHeaders() });
  return response.data;
};

export const addMeetingRecording = async (meetingId, recordingUrl) => {
  const response = await axios.post(`${API}/zoom/meeting/${meetingId}/add-recording?recording_url=${encodeURIComponent(recordingUrl)}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== ORGANIZATION ADMIN ====================
export const getOrgAdminDashboard = async () => {
  const response = await axios.get(`${API}/org-admin/dashboard`, { headers: getAuthHeaders() });
  return response.data;
};

export const getOrgTeachers = async () => {
  const response = await axios.get(`${API}/org-admin/teachers`, { headers: getAuthHeaders() });
  return response.data;
};

export const getOrgStudents = async () => {
  const response = await axios.get(`${API}/org-admin/students`, { headers: getAuthHeaders() });
  return response.data;
};

export const createCourseFromPDF = async (file, title, category = 'certificate', price = 0) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('category', category);
  formData.append('price', price.toString());
  const response = await axios.post(`${API}/org-admin/create-course-from-pdf`, formData, {
    headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const bulkEnrollStudents = async (courseId, studentEmails) => {
  const response = await axios.post(`${API}/org-admin/bulk-enroll`, {
    course_id: courseId,
    student_emails: studentEmails
  }, { headers: getAuthHeaders() });
  return response.data;
};

export const getOrgAnalytics = async () => {
  const response = await axios.get(`${API}/org-admin/analytics`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== USER SETTINGS ====================
export const updateUserProfile = async (fullName, phone = null) => {
  const params = new URLSearchParams();
  if (fullName) params.append('full_name', fullName);
  if (phone) params.append('phone', phone);
  const response = await axios.put(`${API}/user/profile?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const uploadProfilePhoto = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API}/user/profile-photo`, formData, {
    headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const updateNotificationSettings = async (settings) => {
  const params = new URLSearchParams();
  Object.entries(settings).forEach(([key, value]) => {
    params.append(key, value.toString());
  });
  const response = await axios.put(`${API}/user/notifications?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getUserSettings = async () => {
  const response = await axios.get(`${API}/user/settings`, { headers: getAuthHeaders() });
  return response.data;
};

export const updateAppearance = async (theme) => {
  const response = await axios.put(`${API}/user/appearance?theme=${theme}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const changePassword = async (currentPassword, newPassword) => {
  const response = await axios.put(
    `${API}/user/password?current_password=${encodeURIComponent(currentPassword)}&new_password=${encodeURIComponent(newPassword)}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// ==================== PASSWORD RESET ====================
export const forgotPassword = async (email) => {
  const response = await axios.post(`${API}/auth/forgot-password?email=${encodeURIComponent(email)}`);
  return response.data;
};

export const resetPassword = async (email, resetCode, newPassword) => {
  const response = await axios.post(
    `${API}/auth/reset-password?email=${encodeURIComponent(email)}&reset_code=${resetCode}&new_password=${encodeURIComponent(newPassword)}`
  );
  return response.data;
};

// ==================== GOOGLE AUTH ====================
export const processGoogleSession = async (sessionId) => {
  const response = await axios.post(`${API}/auth/google/session?session_id=${sessionId}`);
  return response.data;
};

// ==================== STUDY GROUPS ====================
export const getAllStudyGroups = async (search = '', topic = '') => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (topic) params.append('topic', topic);
  const response = await axios.get(`${API}/study-groups/all?${params}`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== TEACHER COURSES ====================
export const getTeacherCourses = async () => {
  const response = await axios.get(`${API}/courses/teacher/my-courses`, { headers: getAuthHeaders() });
  return response.data;
};

export const deleteCourse = async (courseId) => {
  const response = await axios.delete(`${API}/courses/${courseId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const updateCourse = async (courseId, data) => {
  const params = new URLSearchParams();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== null && value !== undefined) params.append(key, value);
  });
  const response = await axios.put(`${API}/courses/${courseId}?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const uploadVideoFile = async (courseId, title, file, description = '') => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(
    `${API}/content/upload-video?course_id=${courseId}&title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// ==================== REAL GRADES & ATTENDANCE ====================
export const getStudentGrades = async (studentId) => {
  const response = await axios.get(`${API}/grades/student/${studentId}`, { headers: getAuthHeaders() });
  return response.data;
};

export const getStudentAttendance = async (studentId) => {
  const response = await axios.get(`${API}/attendance/student/${studentId}`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== LIVE RESEARCH ====================
export const searchResearch = async (query) => {
  const response = await axios.post(`${API}/research/search?query=${encodeURIComponent(query)}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== PARENT PORTAL ====================
export const getParentChildren = async () => {
  const response = await axios.get(`${API}/parents/children`, { headers: getAuthHeaders() });
  return response.data;
};

export const getChildDetails = async (childId) => {
  const response = await axios.get(`${API}/parents/children/${childId}/details`, { headers: getAuthHeaders() });
  return response.data;
};

export const linkChild = async (childEmail) => {
  const response = await axios.post(`${API}/parents/link-child?child_email=${encodeURIComponent(childEmail)}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== EMAIL VERIFICATION ====================
export const registerWithVerification = async (email, password, fullName, role = 'student', linkedinUrl = '') => {
  const params = new URLSearchParams({ email, password, full_name: fullName, role });
  if (linkedinUrl && linkedinUrl.trim()) {
    params.append('linkedin_url', linkedinUrl.trim());
  }
  const response = await axios.post(`${API}/auth/register-with-verification?${params}`);
  return response.data;
};

export const verifyEmail = async (email, verificationCode) => {
  const params = new URLSearchParams({ email, verification_code: verificationCode });
  const response = await axios.post(`${API}/auth/verify-email?${params}`);
  return response.data;
};

export const resendVerification = async (email) => {
  const response = await axios.post(`${API}/auth/resend-verification?email=${encodeURIComponent(email)}`);
  return response.data;
};

export const forgotPasswordV2 = async (email) => {
  const response = await axios.post(`${API}/auth/forgot-password-v2?email=${encodeURIComponent(email)}`);
  return response.data;
};

export const resetPasswordV2 = async (email, resetCode, newPassword) => {
  const params = new URLSearchParams({ email, reset_code: resetCode, new_password: newPassword });
  const response = await axios.post(`${API}/auth/reset-password-v2?${params}`);
  return response.data;
};

// ==================== GOOGLE AUTH ====================
export const processGoogleSessionV2 = async (sessionId) => {
  const response = await axios.post(`${API}/auth/google/session?session_id=${sessionId}`);
  return response.data;
};

export const initiateGoogleLogin = (redirectPath = '/dashboard') => {
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS - THIS BREAKS THE AUTH
  const redirectUrl = window.location.origin + redirectPath;
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

// ==================== FILE UPLOADS ====================
export const uploadImageFile = async (courseId, title, file, description = '') => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(
    `${API}/content/upload-image?course_id=${courseId}&title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}`,
    formData,
    { headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// ==================== TEACHER DASHBOARD ====================
export const getTeacherDashboardStats = async () => {
  const response = await axios.get(`${API}/teacher/dashboard-stats`, { headers: getAuthHeaders() });
  return response.data;
};

export const getCourseEnrolledStudents = async (courseId) => {
  const response = await axios.get(`${API}/teacher/course/${courseId}/students`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== COURSE TYPES & ACADEMIC LEVELS ====================
export const getAcademicLevels = async () => {
  const response = await axios.get(`${API}/academic-levels`, { headers: getAuthHeaders() });
  return response.data;
};

export const getCourseTypes = async () => {
  const response = await axios.get(`${API}/course-types`, { headers: getAuthHeaders() });
  return response.data;
};

export const createCourseWithDetails = async (title, description, category, academicLevel, numLessons = 10, subject = 'General') => {
  const params = new URLSearchParams({
    title,
    description,
    category,
    academic_level: academicLevel,
    num_lessons: numLessons.toString(),
    subject
  });
  const response = await axios.post(`${API}/courses/create-with-details?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== ASSIGNMENTS (ENHANCED) ====================
export const createLinkedAssignment = async (title, courseId, description = '', dueDate = null, maxScore = 100, autoGrade = true) => {
  const params = new URLSearchParams({
    title,
    course_id: courseId,
    max_score: maxScore.toString(),
    auto_grade: autoGrade.toString()
  });
  if (description) params.append('description', description);
  if (dueDate) params.append('due_date', dueDate);
  const response = await axios.post(`${API}/assignments/create-linked?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getStudentAssignments = async () => {
  const response = await axios.get(`${API}/assignments/student/my-assignments`, { headers: getAuthHeaders() });
  return response.data;
};

export const submitAndGradeAssignment = async (assignmentId, content) => {
  const response = await axios.post(
    `${API}/assignments/${assignmentId}/submit-and-grade?content=${encodeURIComponent(content)}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getSuggestedAnswer = async (assignmentId) => {
  const response = await axios.get(`${API}/assignments/${assignmentId}/suggested-answer`, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== STRIPE PAYMENTS ====================
export const createPaymentCheckout = async (courseId) => {
  const originUrl = window.location.origin;
  const response = await axios.post(
    `${API}/payments/create-checkout?course_id=${courseId}&origin_url=${encodeURIComponent(originUrl)}`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getPaymentStatus = async (sessionId) => {
  const originUrl = window.location.origin;
  const response = await axios.get(
    `${API}/payments/status/${sessionId}?origin_url=${encodeURIComponent(originUrl)}`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// ==================== RISK PREDICTION ACTIONS ====================
export const contactParentAboutRisk = async (studentId, riskType, message) => {
  const params = new URLSearchParams({ student_id: studentId, risk_type: riskType, message });
  const response = await axios.post(`${API}/risk/contact-parent?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const setStudentAlert = async (studentId, alertType, severity, notes) => {
  const params = new URLSearchParams({ student_id: studentId, alert_type: alertType, severity, notes });
  const response = await axios.post(`${API}/risk/set-alert?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== CREDENTIALS (FIXED) ====================
export const issueCredentialV2 = async (studentId, credentialType, title, description = '', courseId = null) => {
  const params = new URLSearchParams({ student_id: studentId, credential_type: credentialType, title });
  if (description) params.append('description', description);
  if (courseId) params.append('course_id', courseId);
  const response = await axios.post(`${API}/credentials/issue-v2?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== ORGANIZATION SCOPED ====================
export const getOrgCourses = async () => {
  const response = await axios.get(`${API}/org/courses`, { headers: getAuthHeaders() });
  return response.data;
};

export const getOrgParticipants = async () => {
  const response = await axios.get(`${API}/org/participants`, { headers: getAuthHeaders() });
  return response.data;
};

export const getOrgStaff = async () => {
  const response = await axios.get(`${API}/org/staff`, { headers: getAuthHeaders() });
  return response.data;
};

export const orgEnrollParticipant = async (email, fullName, role = 'student') => {
  const params = new URLSearchParams({ email, full_name: fullName, role });
  const response = await axios.post(`${API}/org/enroll-participant?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const orgBulkEnroll = async (emails, role = 'student') => {
  const response = await axios.post(`${API}/org/bulk-enroll`, { emails, role }, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== KTCE (Knowledge Time Compression Engine) ====================
export const ktceOptimizePath = async (courseId, learnerGoal) => {
  const params = new URLSearchParams({ course_id: courseId, learner_goal: learnerGoal });
  const response = await axios.post(`${API}/ktce/optimize-path?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const ktceGetCompressedLesson = async (conceptId, conceptName, description = '') => {
  const params = new URLSearchParams({ concept_id: conceptId, concept_name: conceptName });
  if (description) params.append('description', description);
  const response = await axios.post(`${API}/ktce/compressed-lesson?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

// ==================== TEACHER DASHBOARD ENHANCED ====================
export const getTeacherStudentsByCourse = async () => {
  const response = await axios.get(`${API}/teacher/students-by-course`, { headers: getAuthHeaders() });
  return response.data;
};

export const teacherSendMessage = async (studentId, subject, message) => {
  const params = new URLSearchParams({ student_id: studentId, subject, message });
  const response = await axios.post(`${API}/teacher/send-message?${params}`, {}, { headers: getAuthHeaders() });
  return response.data;
};

export const getStudentProfileForTeacher = async (studentId) => {
  const response = await axios.get(`${API}/teacher/student-profile/${studentId}`, { headers: getAuthHeaders() });
  return response.data;
};