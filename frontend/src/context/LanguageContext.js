import React, { createContext, useContext, useState, useEffect } from 'react';
import { getSupportedLanguages, getUITranslations } from '../services/api';

const DEFAULT_LANGUAGES = [
  // African Languages
  { code: 'en', name: 'English', native: 'English', region: 'Global', flag: '🌐' },
  { code: 'sn', name: 'Shona', native: 'chiShona', region: 'Zimbabwe', flag: '🇿🇼' },
  { code: 'nd', name: 'Ndebele', native: 'isiNdebele', region: 'Zimbabwe/South Africa', flag: '🇿🇼' },
  { code: 'zu', name: 'Zulu', native: 'isiZulu', region: 'South Africa', flag: '🇿🇦' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili', region: 'East Africa', flag: '🇰🇪' },
  { code: 'xh', name: 'Xhosa', native: 'isiXhosa', region: 'South Africa', flag: '🇿🇦' },
  { code: 'st', name: 'Sesotho', native: 'Sesotho', region: 'South Africa/Lesotho', flag: '🇱🇸' },
  { code: 'tn', name: 'Setswana', native: 'Setswana', region: 'Botswana/South Africa', flag: '🇧🇼' },
  { code: 'af', name: 'Afrikaans', native: 'Afrikaans', region: 'South Africa', flag: '🇿🇦' },
  { code: 'yo', name: 'Yoruba', native: 'Yorùbá', region: 'Nigeria', flag: '🇳🇬' },
  { code: 'ig', name: 'Igbo', native: 'Igbo', region: 'Nigeria', flag: '🇳🇬' },
  { code: 'ha', name: 'Hausa', native: 'Hausa', region: 'Nigeria/Niger', flag: '🇳🇬' },
  { code: 'am', name: 'Amharic', native: 'አማርኛ', region: 'Ethiopia', flag: '🇪🇹' },
  { code: 'om', name: 'Oromo', native: 'Afaan Oromoo', region: 'Ethiopia', flag: '🇪🇹' },
  { code: 'so', name: 'Somali', native: 'Soomaali', region: 'Somalia', flag: '🇸🇴' },
  { code: 'rw', name: 'Kinyarwanda', native: 'Ikinyarwanda', region: 'Rwanda', flag: '🇷🇼' },
  { code: 'lg', name: 'Luganda', native: 'Oluganda', region: 'Uganda', flag: '🇺🇬' },
  { code: 'ny', name: 'Chichewa', native: 'Chichewa', region: 'Malawi', flag: '🇲🇼' },
  // Global Languages
  { code: 'fr', name: 'French', native: 'Français', region: 'Global/Africa', flag: '🇫🇷' },
  { code: 'pt', name: 'Portuguese', native: 'Português', region: 'Global/Africa', flag: '🇵🇹' },
  { code: 'ar', name: 'Arabic', native: 'العربية', region: 'North Africa/Middle East', flag: '🇸🇦' },
  { code: 'es', name: 'Spanish', native: 'Español', region: 'Global', flag: '🇪🇸' },
  { code: 'zh', name: 'Chinese', native: '中文', region: 'Global', flag: '🇨🇳' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', region: 'India', flag: '🇮🇳' },
];

// UI translations
const translations = {
  en: {
    // Navigation
    dashboard: 'Dashboard',
    courses: 'Courses',
    grades: 'Grades',
    attendance: 'Attendance',
    fees: 'Fees',
    achievements: 'Achievements',
    settings: 'Settings',
    logout: 'Logout',
    // Auth
    welcome: 'Welcome',
    login: 'Login',
    register: 'Register',
    email: 'Email',
    password: 'Password',
    fullName: 'Full Name',
    // Actions
    submit: 'Submit',
    cancel: 'Cancel',
    save: 'Save',
    loading: 'Loading...',
    search: 'Search',
    filter: 'Filter',
    create: 'Create',
    upload: 'Upload',
    download: 'Download',
    share: 'Share',
    enroll: 'Enroll',
    start: 'Start',
    continue: 'Continue',
    complete: 'Complete',
    // Features
    aiMentor: 'AI Mentor',
    knowledgeGraph: 'Knowledge Graph',
    voiceAvatar: 'Voice & Avatar',
    organization: 'Organization',
    participants: 'Participants',
    virtualClassroom: 'Virtual Classroom',
    studyGroups: 'Study Groups',
    learningJourney: 'Learning Journey',
    learnByTeaching: 'Learn by Teaching',
    // AI Features
    getHint: 'Get Hint',
    showAnalogy: 'Show Analogy',
    askAI: 'Ask AI',
    generate: 'Generate',
    translate: 'Translate',
    listen: 'Listen',
    teachBack: 'Teach It Back',
    createQuestion: 'Create Question',
    analyze: 'Analyze',
    // Learning
    concept: 'Concept',
    lesson: 'Lesson',
    quiz: 'Quiz',
    assignment: 'Assignment',
    progress: 'Progress',
    mastery: 'Mastery',
    review: 'Review',
    practice: 'Practice',
    // Content Types
    video: 'Video',
    audio: 'Audio',
    image: 'Image',
    text: 'Text',
    interactive: 'Interactive',
    // Tutor
    selectTutor: 'Select Your Tutor',
    cloneVoice: 'Clone Voice',
    changeAvatar: 'Change Avatar',
    speakToMe: 'Speak to Me',
    // Messages
    success: 'Success',
    error: 'Error',
    noData: 'No data available',
    confirmDelete: 'Are you sure you want to delete?',
  },
  sw: {
    dashboard: 'Dashibodi',
    courses: 'Kozi',
    grades: 'Daraja',
    attendance: 'Mahudhurio',
    fees: 'Ada',
    achievements: 'Mafanikio',
    settings: 'Mipangilio',
    logout: 'Toka',
    welcome: 'Karibu',
    login: 'Ingia',
    register: 'Jiandikishe',
    email: 'Barua pepe',
    password: 'Nenosiri',
    fullName: 'Jina Kamili',
    submit: 'Wasilisha',
    cancel: 'Ghairi',
    save: 'Hifadhi',
    loading: 'Inapakia...',
    search: 'Tafuta',
    filter: 'Chuja',
    aiMentor: 'Mshauri wa AI',
    knowledgeGraph: 'Grafu ya Maarifa',
    voiceAvatar: 'Sauti na Avatar',
    organization: 'Shirika',
    participants: 'Washiriki',
    virtualClassroom: 'Darasa Pepe',
    studyGroups: 'Vikundi vya Kusoma',
    learningJourney: 'Safari ya Kujifunza',
    learnByTeaching: 'Jifunze kwa Kufundisha',
    getHint: 'Pata Dokezo',
    askAI: 'Uliza AI',
    translate: 'Tafsiri',
    listen: 'Sikiliza',
    video: 'Video',
    audio: 'Sauti',
    image: 'Picha',
    text: 'Maandishi',
  },
  zu: {
    dashboard: 'Ikhasi Lokuqala',
    courses: 'Izifundo',
    grades: 'Amamaki',
    attendance: 'Ukuba Khona',
    fees: 'Imali Yesikole',
    achievements: 'Ukuphumelela',
    settings: 'Izilungiselelo',
    logout: 'Phuma',
    welcome: 'Siyakwamukela',
    login: 'Ngena',
    register: 'Bhalisa',
    email: 'I-imeyili',
    password: 'Iphasiwedi',
    fullName: 'Igama Eligcwele',
    submit: 'Thumela',
    cancel: 'Khansela',
    save: 'Gcina',
    loading: 'Kuyalayisha...',
    search: 'Sesha',
    filter: 'Hlunga',
    aiMentor: 'Umfundisi we-AI',
    knowledgeGraph: 'Igrafu Yolwazi',
    voiceAvatar: 'Izwi ne-Avatar',
    organization: 'Inhlangano',
    participants: 'Abahlanganyeli',
    virtualClassroom: 'Ikilasi Lenethiweki',
    studyGroups: 'Amaqembu Okufunda',
  },
  sn: {
    dashboard: 'Peji Rekutanga',
    courses: 'Zvidzidzo',
    grades: 'Mamariki',
    attendance: 'Kupinda',
    fees: 'Mari Yechikoro',
    achievements: 'Zvakaitwa',
    settings: 'Zvigadziriso',
    logout: 'Buda',
    welcome: 'Titambire',
    login: 'Pinda',
    register: 'Nyoresa',
    email: 'Email',
    password: 'Pasiwedhi',
    fullName: 'Zita Rizere',
    submit: 'Tumira',
    cancel: 'Kanzura',
    save: 'Chengetedza',
    loading: 'Kuverenga...',
    search: 'Tsvaga',
    filter: 'Sefa',
    aiMentor: 'Mudzidzisi weAI',
    knowledgeGraph: 'Mufananidzo weRuzivo',
    voiceAvatar: 'Inzwi neAvatar',
    organization: 'Sangano',
    participants: 'Vatanhi',
    virtualClassroom: 'Kirasi yeInternet',
    studyGroups: 'Mapoka Ekudzidza',
  },
  nd: {
    dashboard: 'Ikhasi Lokuqala',
    courses: 'Izifundo',
    grades: 'Amamaki',
    attendance: 'Ukuba Khona',
    fees: 'Imali Yesikolo',
    achievements: 'Impumelelo',
    settings: 'Izilungiselelo',
    logout: 'Phuma',
    welcome: 'Siyakwamukela',
    login: 'Ngena',
    register: 'Bhalisa',
    email: 'I-imeyili',
    password: 'Iphasiwedi',
    fullName: 'Ibizo Eligcweleyo',
    submit: 'Thumela',
    cancel: 'Khansela',
    save: 'Gcina',
    loading: 'Kuyalayisha...',
    search: 'Sesha',
    filter: 'Hlunga',
    aiMentor: 'Umfundisi we-AI',
    knowledgeGraph: 'Igrafu Yolwazi',
    voiceAvatar: 'Ilizwi le-Avatar',
    organization: 'Inhlangano',
    participants: 'Abahlanganyeli',
  },
  xh: {
    dashboard: 'Ibhodi',
    courses: 'Izifundo',
    settings: 'Iisetingi',
    logout: 'Phuma',
    welcome: 'Wamkelekile',
  },
};

const LanguageContext = createContext(null);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('eduos_language') || 'en';
  });
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES);

  useEffect(() => {
    localStorage.setItem('eduos_language', language);
    document.documentElement.lang = language;
  }, [language]);

  // Fetch languages from backend on mount
  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        const data = await getSupportedLanguages();
        if (data && data.length > 0) {
          const langWithFlags = data.map(lang => ({
            ...lang,
            flag: DEFAULT_LANGUAGES.find(l => l.code === lang.code)?.flag || '🌍'
          }));
          setLanguages(langWithFlags);
        }
      } catch (error) {
        console.error('Failed to fetch languages:', error);
      }
    };
    fetchLanguages();
  }, []);

  const t = (key) => {
    return translations[language]?.[key] || translations.en[key] || key;
  };

  const changeLanguage = (newLang) => {
    if (languages.find(l => l.code === newLang)) {
      setLanguage(newLang);
    }
  };

  const currentLanguage = languages.find(l => l.code === language) || languages[0];

  // Group languages by region for UI
  const languagesByRegion = languages.reduce((acc, lang) => {
    const region = lang.region || 'Other';
    if (!acc[region]) acc[region] = [];
    acc[region].push(lang);
    return acc;
  }, {});

  const value = {
    language,
    currentLanguage,
    languages,
    languagesByRegion,
    t,
    changeLanguage
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
