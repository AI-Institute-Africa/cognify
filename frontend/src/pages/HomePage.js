import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  GraduationCap, Brain, Globe, Building2, Users, Shield, Sparkles,
  ArrowRight, CheckCircle, Play, ChevronRight, BookOpen, Award,
  TrendingUp, Network, Wifi, Video, MessageSquare, Mic, Camera,
  Image, Upload, X, Send, Loader2, Volume2, Languages, ChevronDown,
  Zap, User, Layers, Target, Bot
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

// Multi-language translations for landing page
const TRANSLATIONS = {
  en: {
    nav: { features: 'Features', organizations: 'For Organizations', pricing: 'Pricing', contact: 'Contact', signIn: 'Sign In', getStarted: 'Get Started', tryDemo: 'Try Demo' },
    hero: {
      badge: 'Powered by GPT-5.2 & Blockchain',
      title1: 'The Future of',
      title2: 'Education',
      subtitle: 'AI-powered learning platform with blockchain credentials, smart campus features, and multi-language support designed for educational transformation worldwide.',
      registerBtn: 'Register Your Institution',
      signUpBtn: 'Individual Sign Up',
      tryAvatarBtn: 'Try Avatar Learning Free'
    },
    stats: { partners: 'Partner Institutions', learners: 'Active Learners', languages: 'Languages Supported', uptime: 'Uptime' },
    features: {
      title: 'Comprehensive Features',
      subtitle: 'Everything you need to transform education',
      avatarTraining: 'Avatar-Based Training',
      avatarTrainingDesc: 'Learn from personalized AI avatars that adapt to your learning style with voice cloning and visual customization.',
      ktce: 'KTCE',
      ktceDesc: 'Knowledge Time Compression Engine minimizes time-to-competence while preserving correctness.',
      adaptiveLearning: 'Adaptive Identity-Based Learning',
      adaptiveLearningDesc: 'Personalized learning paths based on your LinkedIn profile, skills, and career goals.',
      multiModal: 'Multi-Modal Learning',
      multiModalDesc: 'Learn through text, video, audio, slides, and interactive content tailored to your preferences.',
      knowledgeGraph: 'Knowledge Graph & Career Guidance',
      knowledgeGraphDesc: 'Visual mapping of concepts with AI-powered career path recommendations.',
      learnByTeaching: 'Learn by Teaching',
      learnByTeachingDesc: 'Teach an AI student avatar to reinforce your understanding and identify knowledge gaps.',
      multiLanguage: 'Multi-Language Support',
      multiLanguageDesc: 'Full platform support in 10+ languages including African languages.',
      aiMentor: 'AI Personal Mentor',
      aiMentorDesc: 'Lifelong learning companion that reads your profile and provides personalized guidance.',
      outcomeBased: 'Outcome-Based Learning',
      outcomeBasedDesc: 'Define your learning goals and get a personalized pathway to achieve them with measurable outcomes.'
    },
    trialSection: {
      title: 'Try Avatar-Based Learning Now',
      subtitle: 'Experience our AI-powered avatar tutor without creating an account',
      startTrial: 'Start Free Trial',
      features: ['No account required', 'Instant access', '5 minute demo']
    },
    assistant: {
      title: 'Ask Cognify AI',
      subtitle: 'Get instant answers about our platform, education, or anything!',
      placeholder: 'Ask me anything about education, courses, or Cognify...',
      sendBtn: 'Send',
      uploadHint: 'You can also upload images, audio, or video for analysis',
      recording: 'Recording...',
      processing: 'Processing...'
    },
    orgs: {
      title: 'Built for All Types of Organizations',
      subtitle: 'Whether you\'re a school, university, or corporation',
      universities: 'Universities',
      universitiesDesc: 'Higher education institutions',
      schools: 'Schools',
      schoolsDesc: 'K-12 primary & secondary',
      government: 'Government',
      governmentDesc: 'Public education agencies',
      corporations: 'Corporations',
      corporationsDesc: 'Corporate training programs'
    },
    footer: {
      tagline: 'Transforming Education with AI',
      copyright: '© 2026 AI Institute Africa. All rights reserved.'
    },
    languageSelect: {
      title: 'Select Your Language',
      subtitle: 'Choose your preferred language for the platform'
    }
  },
  sw: {
    nav: { features: 'Vipengele', organizations: 'Kwa Mashirika', pricing: 'Bei', contact: 'Wasiliana', signIn: 'Ingia', getStarted: 'Anza', tryDemo: 'Jaribu Demo' },
    hero: {
      badge: 'Inayoendeshwa na GPT-5.2 na Blockchain',
      title1: 'Mustakabali wa',
      title2: 'Elimu',
      subtitle: 'Jukwaa la kujifunza linaloendeshwa na AI na vyeti vya blockchain, vipengele vya chuo cha kisasa, na msaada wa lugha nyingi.',
      registerBtn: 'Sajili Taasisi Yako',
      signUpBtn: 'Jiandikishe Kibinafsi',
      tryAvatarBtn: 'Jaribu Avatar Bure'
    },
    stats: { partners: 'Taasisi Washirika', learners: 'Wanafunzi Hai', languages: 'Lugha Zinazosaidiwa', uptime: 'Wakati wa Uendeshaji' },
    features: {
      title: 'Vipengele Kamili',
      subtitle: 'Kila unachohitaji kubadilisha elimu',
      avatarTraining: 'Mafunzo ya Avatar',
      avatarTrainingDesc: 'Jifunze kutoka kwa avatar za AI zinazobadilika kulingana na mtindo wako wa kujifunza.',
      ktce: 'KTCE',
      ktceDesc: 'Engine ya Kupunguza Muda wa Maarifa inayopunguza muda wa kufikia ustadi.',
      adaptiveLearning: 'Kujifunza Kulingana na Utambulisho',
      adaptiveLearningDesc: 'Njia za kujifunza zinazobinafsishwa kulingana na wasifu wako wa LinkedIn.',
      multiModal: 'Kujifunza kwa Njia Nyingi',
      multiModalDesc: 'Jifunze kupitia maandishi, video, sauti, slaidi, na maudhui ya maingiliano.',
      knowledgeGraph: 'Grafu ya Maarifa na Mwongozo wa Kazi',
      knowledgeGraphDesc: 'Uchoraji wa dhana na mapendekezo ya njia ya kazi yanayoendeshwa na AI.',
      learnByTeaching: 'Jifunze kwa Kufundisha',
      learnByTeachingDesc: 'Fundisha avatar ya mwanafunzi wa AI kuimarisha uelewa wako.',
      multiLanguage: 'Msaada wa Lugha Nyingi',
      multiLanguageDesc: 'Msaada kamili wa jukwaa katika lugha 10+ ikiwa ni pamoja na lugha za Kiafrika.',
      aiMentor: 'Mshauri wa AI Binafsi',
      aiMentorDesc: 'Mwandani wa kujifunza maisha yote anayesoma wasifu wako na kutoa mwongozo wa kibinafsi.',
      outcomeBased: 'Kujifunza Kulingana na Matokeo',
      outcomeBasedDesc: 'Weka malengo yako ya kujifunza na upate njia ya kibinafsi ya kuyafikia.'
    },
    trialSection: {
      title: 'Jaribu Kujifunza kwa Avatar Sasa',
      subtitle: 'Pata uzoefu wa mwalimu wetu wa avatar unaendeshwa na AI bila kuunda akaunti',
      startTrial: 'Anza Jaribio Bila Malipo',
      features: ['Hakuna akaunti inayohitajika', 'Ufikiaji wa papo hapo', 'Demo ya dakika 5']
    },
    assistant: {
      title: 'Uliza Cognify AI',
      subtitle: 'Pata majibu ya papo hapo kuhusu jukwaa letu!',
      placeholder: 'Niulize chochote kuhusu elimu...',
      sendBtn: 'Tuma',
      uploadHint: 'Unaweza pia kupakia picha, sauti, au video',
      recording: 'Inarekodiwa...',
      processing: 'Inachakatwa...'
    },
    orgs: {
      title: 'Imejengwa kwa Aina Zote za Mashirika',
      subtitle: 'Iwe wewe ni shule, chuo kikuu, au kampuni',
      universities: 'Vyuo Vikuu',
      universitiesDesc: 'Taasisi za elimu ya juu',
      schools: 'Shule',
      schoolsDesc: 'Msingi na sekondari',
      government: 'Serikali',
      governmentDesc: 'Mashirika ya elimu ya umma',
      corporations: 'Makampuni',
      corporationsDesc: 'Programu za mafunzo ya kampuni'
    },
    footer: {
      tagline: 'Kubadilisha Elimu na AI',
      copyright: '© 2026 AI Institute Africa. Haki zote zimehifadhiwa.'
    },
    languageSelect: {
      title: 'Chagua Lugha Yako',
      subtitle: 'Chagua lugha unayopendelea kwa jukwaa'
    }
  },
  sn: {
    nav: { features: 'Zvimwe', organizations: 'Kuma Sangano', pricing: 'Mitengo', contact: 'Bata Nesu', signIn: 'Pinda', getStarted: 'Tanga', tryDemo: 'Edza Demo' },
    hero: {
      badge: 'Inoshanda neGPT-5.2 neBlockchain',
      title1: 'Ramangwana re',
      title2: 'Dzidzo',
      subtitle: 'Nzvimbo yekudzidza inoshanda neAI ine zvitupa zveblockchain, zvimwe zvechikoro chitsva, nerutsigiro rwemitauro mizhinji.',
      registerBtn: 'Nyoresa Sangano Rako',
      signUpBtn: 'Nyoresa Wega',
      tryAvatarBtn: 'Edza Avatar Mahara'
    },
    stats: { partners: 'Masangano Anoshanda Nesu', learners: 'Vadzidzi Vanoshanda', languages: 'Mitauro Inotsigirwa', uptime: 'Nguva Yekushanda' },
    features: {
      title: 'Zvese Zvimwe',
      subtitle: 'Zvese zvaunoda kushandura dzidzo',
      avatarTraining: 'Kudzidziswa neAvatar',
      avatarTrainingDesc: 'Dzidza kubva kumaAvatar eAI anoshanduka maererano nemaitiro ako ekudzidza.',
      ktce: 'KTCE',
      ktceDesc: 'Injini Yekuderedza Nguva Yeruzivo inoderedza nguva yekusvika pakugona.',
      adaptiveLearning: 'Kudzidza Kunoenderana Nezita',
      adaptiveLearningDesc: 'Nzira dzekudzidza dzinoenderana neprofile yako yeLinkedIn.',
      multiModal: 'Kudzidza Nenzira Dzakawanda',
      multiModalDesc: 'Dzidza kuburikidza nezvinyorwa, mavhidhiyo, manzwi, maslaidi, nezvimwe zvinoshanda.',
      knowledgeGraph: 'Chati yeRuzivo neKutungamira Basa',
      knowledgeGraphDesc: 'Kuona kwemifungo ine zvidzidzo zvenharaunda inoshanda neAI.',
      learnByTeaching: 'Dzidza Nekudzidzisa',
      learnByTeachingDesc: 'Dzidzisa avatar yemudzidzi weAI kusimbisa kunzwisisa kwako.',
      multiLanguage: 'Rutsigiro rweMitauro Mizhinji',
      multiLanguageDesc: 'Rutsigiro rwakakwana munzvimbo mumitauro 10+ kusanganisira mitauro yeAfrica.',
      aiMentor: 'Mudzidzisi weAI Wako',
      aiMentorDesc: 'Shamwari yekudzidza kweupenyu hwese inoverenga profile yako uye inopa kutungamira kwako.',
      outcomeBased: 'Kudzidza Kunobva Pazvigumisiro',
      outcomeBasedDesc: 'Isa zvinangwa zvako zvekudzidza uye uwane nzira yako yekuzvisvika.'
    },
    trialSection: {
      title: 'Edza Kudzidza kweAvatar Iye Zvino',
      subtitle: 'Ona mudzidzisi wedu weAvatar inoshanda neAI usina kugadzira account',
      startTrial: 'Tanga Kuedza Mahara',
      features: ['Hapana account inodikanwa', 'Kupinda pakarepo', 'Demo yemaminetsi 5']
    },
    assistant: {
      title: 'Bvunza Cognify AI',
      subtitle: 'Wana mhinduro dzekukurumidza pamusoro penzvimbo yedu!',
      placeholder: 'Ndibvunze chero chii pamusoro pedzidzo...',
      sendBtn: 'Tumira',
      uploadHint: 'Unogona zvakare kuisa mifananidzo, manzwi, kana mavhidhiyo',
      recording: 'Iri kurekodha...',
      processing: 'Iri kushanda...'
    },
    orgs: {
      title: 'Yakagadzirirwa Marudzi Ese eMasangano',
      subtitle: 'Kunyangwe uri chikoro, koreji, kana kambani',
      universities: 'Mayunivhesiti',
      universitiesDesc: 'Masangano edzidzo yepamusoro',
      schools: 'Zvikoro',
      schoolsDesc: 'Pakutanga uye sekondari',
      government: 'Hurumende',
      governmentDesc: 'Masangano edzidzo yeruzhinji',
      corporations: 'Makambani',
      corporationsDesc: 'Mapurogiramu ekudzidzisa makambani'
    },
    footer: {
      tagline: 'Kushandura Dzidzo neAI',
      copyright: '© 2026 AI Institute Africa. Kodzero dzese dzakachengetwa.'
    },
    languageSelect: {
      title: 'Sarudza Mutauro Wako',
      subtitle: 'Sarudza mutauro waunoda kunzvimbo'
    }
  },
  zu: {
    nav: { features: 'Izici', organizations: 'Ezezinhlangano', pricing: 'Amanani', contact: 'Xhumana', signIn: 'Ngena', getStarted: 'Qala', tryDemo: 'Zama iDemo' },
    hero: {
      badge: 'Isebenza nge-GPT-5.2 ne-Blockchain',
      title1: 'Ikusasa Le',
      title2: 'mfundo',
      subtitle: 'Inkundla yokufunda esebenza nge-AI enezitifiketi ze-blockchain, izici zekhempasi ehlakaniphile, nokusekela izilimi eziningi.',
      registerBtn: 'Bhalisa Isikhungo Sakho',
      signUpBtn: 'Bhalisa Uwedwa',
      tryAvatarBtn: 'Zama i-Avatar Mahhala'
    },
    stats: { partners: 'Izikhungo Ezibambisene', learners: 'Abafundi Abasebenzayo', languages: 'Izilimi Ezisekelwayo', uptime: 'Isikhathi Sokusebenza' },
    features: {
      title: 'Izici Eziphelele',
      subtitle: 'Konke okudingayo ukushintsha imfundo',
      avatarTraining: 'Ukuqeqeshwa Nge-Avatar',
      avatarTrainingDesc: 'Funda kuma-avatar e-AI ajikayo ngokwendlela yakho yokufunda.',
      ktce: 'KTCE',
      ktceDesc: 'I-Engine Yokuncipha Kwesikhathi Solwazi enciphisa isikhathi sokufinyelela amakhono.',
      adaptiveLearning: 'Ukufunda Okujikayo Okususelwe Kuwe',
      adaptiveLearningDesc: 'Izindlela zokufunda ezihambisana nephrofayela yakho ye-LinkedIn.',
      multiModal: 'Ukufunda Ngezindlela Eziningi',
      multiModalDesc: 'Funda ngombhalo, ividiyo, umsindo, amaslayidi, nokuqukethwe okusebenzisanayo.',
      knowledgeGraph: 'Igrafu Yolwazi Nokwelulekwa Ngomsebenzi',
      knowledgeGraphDesc: 'Ukubonisa imibono ngezincomo zendlela yomsebenzi ezisebenza nge-AI.',
      learnByTeaching: 'Funda Ngokufundisa',
      learnByTeachingDesc: 'Fundisa i-avatar yomfundi we-AI ukuqinisa ukuqonda kwakho.',
      multiLanguage: 'Ukusekela Izilimi Eziningi',
      multiLanguageDesc: 'Ukusekela okuphelele kwinkundla ngezilimi ezingu-10+ kufaka phakathi izilimi zase-Afrika.',
      aiMentor: 'Umeluleki Wakho We-AI',
      aiMentorDesc: 'Umngane wokufunda wempilo yonke ofunda iphrofayela yakho futhi anikeze isiqondiso sakho.',
      outcomeBased: 'Ukufunda Okususelwe Emiphumeleni',
      outcomeBasedDesc: 'Beka izinhloso zakho zokufunda futhi uthole indlela yakho esiqu sokuzifinyelela.'
    },
    trialSection: {
      title: 'Zama Ukufunda Nge-Avatar Manje',
      subtitle: 'Thola ulwazi lomfundisi wethu we-avatar osebenza nge-AI ngaphandle kokudala i-akhawunti',
      startTrial: 'Qala Ukuzama Mahhala',
      features: ['Ayikho i-akhawunti edingekayo', 'Ukufinyelela okusheshayo', 'Idemo yemizuzu emi-5']
    },
    assistant: {
      title: 'Buza i-Cognify AI',
      subtitle: 'Thola izimpendulo ezisheshayo mayelana nenkundla yethu!',
      placeholder: 'Ngibuze noma yini mayelana nemfundo...',
      sendBtn: 'Thumela',
      uploadHint: 'Ungalayisha futhi izithombe, umsindo, noma ividiyo',
      recording: 'Iyarekhoda...',
      processing: 'Iyacubungula...'
    },
    orgs: {
      title: 'Yakhelwe Zonke Izinhlobo Zezinhlangano',
      subtitle: 'Noma ngabe isikole, inyuvesi, noma inkampani',
      universities: 'Amanyuvesi',
      universitiesDesc: 'Izikhungo zemfundo ephakeme',
      schools: 'Izikole',
      schoolsDesc: 'Amabanga aphansi naphezulu',
      government: 'Uhulumeni',
      governmentDesc: 'Izinhlangano zemfundo yomphakathi',
      corporations: 'Izinkampani',
      corporationsDesc: 'Izinhlelo zokuqeqesha izinkampani'
    },
    footer: {
      tagline: 'Ukuguqula Imfundo Nge-AI',
      copyright: '© 2026 AI Institute Africa. Wonke amalungelo agodliwe.'
    },
    languageSelect: {
      title: 'Khetha Ulimi Lwakho',
      subtitle: 'Khetha ulimi olusithandayo kwinkundla'
    }
  },
  fr: {
    nav: { features: 'Fonctionnalités', organizations: 'Pour les Organisations', pricing: 'Tarifs', contact: 'Contact', signIn: 'Connexion', getStarted: 'Commencer', tryDemo: 'Essayer Démo' },
    hero: {
      badge: 'Propulsé par GPT-5.2 et Blockchain',
      title1: "L'avenir de",
      title2: "l'éducation",
      subtitle: "Plateforme d'apprentissage alimentée par l'IA avec des certifications blockchain, des fonctionnalités de campus intelligent et un support multilingue.",
      registerBtn: 'Enregistrez votre institution',
      signUpBtn: 'Inscription individuelle',
      tryAvatarBtn: "Essayer l'Avatar Gratuit"
    },
    stats: { partners: 'Institutions partenaires', learners: 'Apprenants actifs', languages: 'Langues supportées', uptime: 'Disponibilité' },
    features: {
      title: 'Fonctionnalités Complètes',
      subtitle: "Tout ce dont vous avez besoin pour transformer l'éducation",
      avatarTraining: 'Formation par Avatar',
      avatarTrainingDesc: "Apprenez avec des avatars IA personnalisés qui s'adaptent à votre style d'apprentissage.",
      ktce: 'KTCE',
      ktceDesc: "Le moteur de compression du temps de connaissance minimise le temps d'acquisition des compétences.",
      adaptiveLearning: 'Apprentissage Adaptatif Basé sur l\'Identité',
      adaptiveLearningDesc: "Parcours d'apprentissage personnalisés basés sur votre profil LinkedIn.",
      multiModal: 'Apprentissage Multi-Modal',
      multiModalDesc: 'Apprenez par le texte, la vidéo, l\'audio, les diapositives et le contenu interactif.',
      knowledgeGraph: 'Graphe de Connaissances et Orientation',
      knowledgeGraphDesc: "Cartographie visuelle des concepts avec recommandations de carrière alimentées par l'IA.",
      learnByTeaching: 'Apprendre en Enseignant',
      learnByTeachingDesc: 'Enseignez à un avatar étudiant IA pour renforcer votre compréhension.',
      multiLanguage: 'Support Multilingue',
      multiLanguageDesc: 'Support complet de la plateforme en 10+ langues incluant les langues africaines.',
      aiMentor: 'Mentor IA Personnel',
      aiMentorDesc: 'Compagnon d\'apprentissage à vie qui lit votre profil et fournit des conseils personnalisés.',
      outcomeBased: 'Apprentissage Basé sur les Résultats',
      outcomeBasedDesc: 'Définissez vos objectifs d\'apprentissage et obtenez un parcours personnalisé pour les atteindre.'
    },
    trialSection: {
      title: "Essayez l'Apprentissage par Avatar Maintenant",
      subtitle: 'Découvrez notre tuteur avatar alimenté par l\'IA sans créer de compte',
      startTrial: 'Commencer l\'Essai Gratuit',
      features: ['Aucun compte requis', 'Accès instantané', 'Démo de 5 minutes']
    },
    assistant: {
      title: 'Demandez à Cognify AI',
      subtitle: 'Obtenez des réponses instantanées sur notre plateforme!',
      placeholder: "Posez-moi n'importe quelle question sur l'éducation...",
      sendBtn: 'Envoyer',
      uploadHint: 'Vous pouvez également télécharger des images, audio ou vidéo',
      recording: 'Enregistrement...',
      processing: 'Traitement...'
    },
    orgs: {
      title: "Conçu pour tous les types d'organisations",
      subtitle: "Que vous soyez une école, une université ou une entreprise",
      universities: 'Universités',
      universitiesDesc: "Établissements d'enseignement supérieur",
      schools: 'Écoles',
      schoolsDesc: 'Primaire et secondaire',
      government: 'Gouvernement',
      governmentDesc: "Agences d'éducation publique",
      corporations: 'Entreprises',
      corporationsDesc: 'Programmes de formation en entreprise'
    },
    footer: {
      tagline: "Transformer l'éducation avec l'IA",
      copyright: '© 2026 AI Institute Africa. Tous droits réservés.'
    },
    languageSelect: {
      title: 'Sélectionnez Votre Langue',
      subtitle: 'Choisissez votre langue préférée pour la plateforme'
    }
  }
};

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'sw', name: 'Kiswahili', flag: '🇰🇪' },
  { code: 'sn', name: 'Shona', flag: '🇿🇼' },
  { code: 'zu', name: 'isiZulu', flag: '🇿🇦' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
];

const ROBOT_IMAGE = "https://static.prod-images.emergentagent.com/jobs/04bc6db1-7ac3-4709-aae3-54bc87bb7c66/images/e0ffb9d236aaca027e7180c6e198ee0638091ebb1f8d4b51ee90fd171a5d8ebb.png";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function HomePage() {
  const navigate = useNavigate();
  const [language, setLanguage] = useState(() => localStorage.getItem('cognify_language') || 'en');
  const [showAssistant, setShowAssistant] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const t = TRANSLATIONS[language] || TRANSLATIONS.en;

  useEffect(() => {
    localStorage.setItem('cognify_language', language);
  }, [language]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!query.trim() && !uploadedFile) return;
    
    const userMessage = { role: 'user', content: query, file: uploadedFile?.name };
    setMessages(prev => [...prev, userMessage]);
    const currentQuery = query;
    setQuery('');
    setIsLoading(true);

    try {
      let response;
      
      if (uploadedFile) {
        // Handle file upload with AI analysis
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('question', currentQuery || 'Please analyze this file and tell me what you see.');
        
        response = await fetch(`${API_URL}/api/ai/landing-upload`, {
          method: 'POST',
          body: formData
        });
      } else {
        // Regular text message
        response = await fetch(`${API_URL}/api/ai/landing-assistant`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: currentQuery,
            language
          })
        });
      }
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Welcome to Cognify! I can help you with questions about education, courses, and our platform. What would you like to know?'
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I\'m here to help! Ask me anything about Cognify, our features, or education in general.'
      }]);
    } finally {
      setIsLoading(false);
      setUploadedFile(null);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      toast.success(`File uploaded: ${file.name}`);
    }
  };

  const startAvatarTrial = () => {
    navigate('/avatar-trial');
  };

  const stats = [
    { value: '500+', label: t.stats.partners },
    { value: '100K+', label: t.stats.learners },
    { value: '10+', label: t.stats.languages },
    { value: '99.9%', label: t.stats.uptime }
  ];

  // Updated features list (removed Outcome-Based Learning)
  const features = [
    { 
      key: 'avatarTraining',
      icon: User, 
      color: 'violet',
      title: t.features.avatarTraining, 
      description: t.features.avatarTrainingDesc 
    },
    { 
      key: 'ktce',
      icon: Zap, 
      color: 'emerald',
      title: t.features.ktce, 
      description: t.features.ktceDesc 
    },
    { 
      key: 'adaptiveLearning',
      icon: Target, 
      color: 'blue',
      title: t.features.adaptiveLearning, 
      description: t.features.adaptiveLearningDesc 
    },
    { 
      key: 'multiModal',
      icon: Layers, 
      color: 'amber',
      title: t.features.multiModal, 
      description: t.features.multiModalDesc 
    },
    { 
      key: 'knowledgeGraph',
      icon: Network, 
      color: 'cyan',
      title: t.features.knowledgeGraph, 
      description: t.features.knowledgeGraphDesc 
    },
    { 
      key: 'learnByTeaching',
      icon: Users, 
      color: 'pink',
      title: t.features.learnByTeaching, 
      description: t.features.learnByTeachingDesc 
    },
    { 
      key: 'multiLanguage',
      icon: Globe, 
      color: 'indigo',
      title: t.features.multiLanguage, 
      description: t.features.multiLanguageDesc 
    },
    { 
      key: 'aiMentor',
      icon: Brain, 
      color: 'rose',
      title: t.features.aiMentor, 
      description: t.features.aiMentorDesc 
    },
    { 
      key: 'outcomeBased',
      icon: TrendingUp, 
      color: 'orange',
      title: t.features.outcomeBased, 
      description: t.features.outcomeBasedDesc 
    }
  ];

  const orgTypes = [
    { icon: GraduationCap, title: t.orgs.universities, description: t.orgs.universitiesDesc },
    { icon: BookOpen, title: t.orgs.schools, description: t.orgs.schoolsDesc },
    { icon: Building2, title: t.orgs.government, description: t.orgs.governmentDesc },
    { icon: Users, title: t.orgs.corporations, description: t.orgs.corporationsDesc }
  ];

  return (
    <div className="min-h-screen bg-[#09090B] text-white">
      {/* Language Selection Modal (Prominent) */}
      {showLanguageModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-white/10 rounded-2xl p-8 max-w-md w-full">
            <div className="text-center mb-6">
              <Globe className="w-12 h-12 text-blue-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold">{t.languageSelect.title}</h2>
              <p className="text-zinc-400 mt-2">{t.languageSelect.subtitle}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {LANGUAGES.map(lang => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setLanguage(lang.code);
                    setShowLanguageModal(false);
                  }}
                  className={`p-4 rounded-xl border transition-all ${
                    language === lang.code 
                      ? 'border-blue-500 bg-blue-500/10' 
                      : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                  }`}
                >
                  <span className="text-2xl mb-2 block">{lang.flag}</span>
                  <span className="font-medium">{lang.name}</span>
                </button>
              ))}
            </div>
            <Button 
              onClick={() => setShowLanguageModal(false)}
              className="w-full mt-6 bg-blue-500 hover:bg-blue-600"
            >
              Continue
            </Button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-[#09090B]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Brain className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-base sm:text-lg">Cognify</h1>
                <p className="text-xs text-zinc-500 hidden sm:block">AI-Powered Education</p>
              </div>
            </div>
            
            <div className="hidden lg:flex items-center gap-8">
              <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">{t.nav.features}</a>
              <a href="#organizations" className="text-sm text-zinc-400 hover:text-white transition-colors">{t.nav.organizations}</a>
              <a href="#assistant" className="text-sm text-zinc-400 hover:text-white transition-colors">AI Assistant</a>
            </div>
            
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Language Selector - icon only on mobile */}
              <Button 
                variant="outline" 
                onClick={() => setShowLanguageModal(true)}
                className="border-blue-500/50 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 px-2 sm:px-3"
                data-testid="language-selector-btn"
              >
                <Globe className="w-4 h-4" />
                <span className="hidden sm:inline ml-2">{LANGUAGES.find(l => l.code === language)?.flag} {LANGUAGES.find(l => l.code === language)?.name}</span>
              </Button>
              
              <Link to="/login">
                <Button variant="ghost" className="text-zinc-400 hover:text-white px-2 sm:px-4">
                  <span className="hidden sm:inline">{t.nav.signIn}</span>
                  <User className="w-4 h-4 sm:hidden" />
                </Button>
              </Link>
              <Link to="/register">
                <Button className="bg-blue-500 hover:bg-blue-600 px-3 sm:px-4 text-sm">
                  <span className="hidden sm:inline">{t.nav.getStarted}</span>
                  <span className="sm:hidden">Join</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section with Robot */}
      <section className="pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Text Content */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6 sm:mb-8">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <span className="text-xs sm:text-sm text-blue-400">{t.hero.badge}</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-4 sm:mb-6 leading-tight">
                {t.hero.title1}
                <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent block"> {t.hero.title2}</span>
              </h1>
              
              <p className="text-base sm:text-lg lg:text-xl text-zinc-400 mb-6 sm:mb-10 max-w-2xl mx-auto lg:mx-0">
                {t.hero.subtitle}
              </p>
              
              <div className="flex flex-col sm:flex-row items-center lg:items-start gap-3 sm:gap-4">
                <Link to="/register-organization" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto bg-blue-500 hover:bg-blue-600 h-12 sm:h-14 px-6 sm:px-8 text-base sm:text-lg">
                    {t.hero.registerBtn}
                    <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/register" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto h-12 sm:h-14 px-6 sm:px-8 text-base sm:text-lg border-white/10 hover:bg-white/5">
                    <Play className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                    {t.hero.signUpBtn}
                  </Button>
                </Link>
              </div>
            </div>
            
            {/* Robot Image - hidden on small mobile */}
            <div className="relative hidden sm:flex justify-center lg:justify-end">
              <div className="relative">
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/30 via-violet-500/30 to-cyan-500/30 blur-3xl scale-150" />
                
                {/* Robot image */}
                <img 
                  src={ROBOT_IMAGE} 
                  alt="AI Education Robot" 
                  className="relative z-10 w-full max-w-md lg:max-w-lg transform -scale-x-100"
                  style={{ filter: 'drop-shadow(0 0 40px rgba(59, 130, 246, 0.5))' }}
                />
                
                {/* Floating badges - hidden on tablet */}
                <div className="absolute top-10 left-0 bg-zinc-900/90 backdrop-blur border border-white/10 rounded-xl px-3 py-1.5 sm:px-4 sm:py-2 animate-pulse hidden lg:block">
                  <p className="text-xs sm:text-sm font-medium text-emerald-400">AI-Powered</p>
                </div>
                <div className="absolute bottom-20 right-0 bg-zinc-900/90 backdrop-blur border border-white/10 rounded-xl px-3 py-1.5 sm:px-4 sm:py-2 animate-pulse delay-500 hidden lg:block">
                  <p className="text-xs sm:text-sm font-medium text-violet-400">24/7 Learning</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mt-12 sm:mt-20">
            {stats.map((stat, index) => (
              <div key={index} className="text-center p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-zinc-900/50 border border-white/5">
                <p className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-xs sm:text-sm text-zinc-500 mt-1 sm:mt-2">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Avatar Trial Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-violet-500/10 via-blue-500/10 to-emerald-500/10 border-y border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/20 border border-violet-500/30 mb-6">
            <User className="w-4 h-4 text-violet-400" />
            <span className="text-sm text-violet-400">Free Trial Available</span>
          </div>
          
          <h2 className="text-3xl md:text-5xl font-bold mb-4">{t.trialSection.title}</h2>
          <p className="text-xl text-zinc-400 mb-8 max-w-2xl mx-auto">{t.trialSection.subtitle}</p>
          
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            {t.trialSection.features.map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2 bg-zinc-900/50 px-4 py-2 rounded-full">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
          
          <Button 
            size="lg" 
            onClick={startAvatarTrial}
            className="h-16 px-12 text-xl bg-gradient-to-r from-violet-500 to-blue-500 hover:from-violet-600 hover:to-blue-600"
            data-testid="try-avatar-btn"
          >
            <Bot className="w-6 h-6 mr-3" />
            {t.trialSection.startTrial}
            <ArrowRight className="w-6 h-6 ml-3" />
          </Button>
        </div>
      </section>

      {/* AI Assistant Section */}
      <section id="assistant" className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.assistant.title}</h2>
            <p className="text-zinc-400">{t.assistant.subtitle}</p>
          </div>
          
          <div className="glass-card rounded-2xl p-6 border border-white/10 bg-zinc-900/50">
            {/* Messages */}
            <div className="h-[300px] overflow-y-auto mb-4 space-y-4 p-4">
              {messages.length === 0 && (
                <div className="text-center text-zinc-500 py-10">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>{t.assistant.subtitle}</p>
                </div>
              )}
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded-2xl ${
                    msg.role === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-zinc-800 text-zinc-200'
                  }`}>
                    {msg.file && <p className="text-xs opacity-70 mb-1">📎 {msg.file}</p>}
                    <p className="text-sm">{msg.content}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-zinc-800 p-4 rounded-2xl">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area */}
            <div className="flex flex-col gap-3">
              {uploadedFile && (
                <div className="flex items-center gap-2 bg-zinc-800 p-2 rounded-lg">
                  <span className="text-sm text-zinc-400">📎 {uploadedFile.name}</span>
                  <Button size="sm" variant="ghost" onClick={() => setUploadedFile(null)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
              <div className="flex gap-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept="image/*,audio/*,video/*"
                  onChange={handleFileUpload}
                />
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="border-white/10"
                  onClick={() => fileInputRef.current?.click()}
                  data-testid="upload-media-btn"
                >
                  <Upload className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="border-white/10"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Image className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="border-white/10"
                  onClick={() => setIsRecording(!isRecording)}
                >
                  <Mic className={`w-4 h-4 ${isRecording ? 'text-red-500' : ''}`} />
                </Button>
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t.assistant.placeholder}
                  className="flex-1 bg-zinc-800 border-white/10"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  data-testid="assistant-input"
                />
                <Button 
                  onClick={handleSendMessage} 
                  disabled={isLoading || (!query.trim() && !uploadedFile)}
                  className="bg-blue-500 hover:bg-blue-600"
                  data-testid="send-message-btn"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-zinc-500 text-center">{t.assistant.uploadHint}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - 8 Feature Cards */}
      <section id="features" className="py-12 sm:py-20 px-4 sm:px-6 bg-zinc-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 sm:mb-4">{t.features.title}</h2>
            <p className="text-sm sm:text-base text-zinc-400 max-w-xl mx-auto px-4">{t.features.subtitle}</p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {features.map((feature, index) => (
              <div
                key={feature.key}
                className="group p-4 sm:p-6 rounded-xl sm:rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-white/20 transition-all duration-300 hover:transform hover:-translate-y-1"
              >
                <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-${feature.color}-500/20 flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-6 h-6 sm:w-7 sm:h-7 text-${feature.color}-400`} />
                </div>
                <h3 className="text-base sm:text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-xs sm:text-sm text-zinc-400 mb-3 sm:mb-4">{feature.description}</p>
                <Link to="/register" className="inline-flex items-center text-xs sm:text-sm text-blue-400 hover:text-blue-300 transition-colors">
                  Learn More <ChevronRight className="w-4 h-4 ml-1" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Organizations Section */}
      <section id="organizations" className="py-12 sm:py-20 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 sm:mb-4">{t.orgs.title}</h2>
            <p className="text-sm sm:text-base text-zinc-400">{t.orgs.subtitle}</p>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
            {orgTypes.map((org, index) => (
              <div key={index} className="text-center p-4 sm:p-8 rounded-xl sm:rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-blue-500/30 transition-all">
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-xl sm:rounded-2xl bg-blue-500/10 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <org.icon className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400" />
                </div>
                <h3 className="text-sm sm:text-lg font-semibold mb-1 sm:mb-2">{org.title}</h3>
                <p className="text-xs sm:text-sm text-zinc-400 hidden sm:block">{org.description}</p>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-8 sm:mt-12">
            <Link to="/register-organization">
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600 h-12 sm:h-auto">
                {t.hero.registerBtn}
                <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 px-4 sm:px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Brain className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-sm sm:text-base">Cognify 2026</h1>
                <p className="text-xs text-zinc-500">{t.footer.tagline}</p>
              </div>
            </div>
            <p className="text-sm text-zinc-500">{t.footer.copyright}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
