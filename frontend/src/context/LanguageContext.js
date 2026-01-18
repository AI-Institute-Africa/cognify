import React, { createContext, useContext, useState, useEffect } from 'react';

const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'sn', name: 'Shona', native: 'chiShona', flag: '🇿🇼' },
  { code: 'nd', name: 'Ndebele', native: 'isiNdebele', flag: '🇿🇼' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili', flag: '🇰🇪' },
  { code: 'zu', name: 'Zulu', native: 'isiZulu', flag: '🇿🇦' }
];

// UI translations
const translations = {
  en: {
    dashboard: 'Dashboard',
    courses: 'Courses',
    grades: 'Grades',
    attendance: 'Attendance',
    fees: 'Fees',
    achievements: 'Achievements',
    settings: 'Settings',
    logout: 'Logout',
    welcome: 'Welcome',
    login: 'Login',
    register: 'Register',
    email: 'Email',
    password: 'Password',
    fullName: 'Full Name',
    submit: 'Submit',
    cancel: 'Cancel',
    save: 'Save',
    loading: 'Loading...',
    search: 'Search',
    filter: 'Filter',
    aiMentor: 'AI Mentor',
    knowledgeGraph: 'Knowledge Graph',
    voiceAvatar: 'Voice & Avatar',
    organization: 'Organization',
    participants: 'Participants'
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
    participants: 'Vatanhi'
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
    participants: 'Abahlanganyeli'
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
    participants: 'Washiriki'
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
    participants: 'Abahlanganyeli'
  }
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

  useEffect(() => {
    localStorage.setItem('eduos_language', language);
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations.en[key] || key;
  };

  const changeLanguage = (newLang) => {
    if (LANGUAGES.find(l => l.code === newLang)) {
      setLanguage(newLang);
    }
  };

  const currentLanguage = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];

  const value = {
    language,
    currentLanguage,
    languages: LANGUAGES,
    t,
    changeLanguage
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
