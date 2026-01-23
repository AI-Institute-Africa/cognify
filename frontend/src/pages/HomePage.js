import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  GraduationCap, Brain, Globe, Building2, Users, Shield, Sparkles,
  ArrowRight, CheckCircle, Play, ChevronRight, BookOpen, Award,
  TrendingUp, Network, Wifi, Video, MessageSquare, Mic, Camera,
  Image, Upload, X, Send, Loader2, Volume2, Languages, ChevronDown
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
    nav: { features: 'Features', organizations: 'For Organizations', pricing: 'Pricing', contact: 'Contact', signIn: 'Sign In', getStarted: 'Get Started' },
    hero: {
      badge: 'Powered by GPT-5.2 & Blockchain',
      title1: 'The Future of',
      title2: 'African Education',
      subtitle: 'AI-powered learning platform with blockchain credentials, smart campus features, and multi-language support built for Africa\'s educational transformation.',
      registerBtn: 'Register Your Institution',
      signUpBtn: 'Individual Sign Up'
    },
    stats: { partners: 'Partner Institutions', learners: 'Active Learners', languages: 'African Languages', uptime: 'Uptime' },
    features: {
      title: 'Comprehensive Features',
      subtitle: 'Everything you need to transform education',
      aiMentor: 'AI Personal Mentor',
      aiMentorDesc: 'Personalized learning with GPT-5.2 powered tutoring in 5 African languages',
      knowledgeGraph: 'Knowledge Graph',
      knowledgeGraphDesc: 'Visual mapping of concepts with mastery tracking and spaced repetition',
      blockchain: 'Blockchain Credentials',
      blockchainDesc: 'Tamper-proof digital certificates verified on Ethereum blockchain',
      smartCampus: 'Smart Campus',
      smartCampusDesc: 'RFID/NFC attendance, biometric verification, and IoT integration',
      virtualClass: 'Virtual Classrooms',
      virtualClassDesc: 'Seamless Zoom & Google Meet integration for hybrid learning',
      riskPrediction: 'Risk Prediction',
      riskPredictionDesc: 'AI-powered early warning system for at-risk students'
    },
    assistant: {
      title: 'Ask EduOS AI',
      subtitle: 'Get instant answers about our platform, education, or anything!',
      placeholder: 'Ask me anything about education, courses, or EduOS...',
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
      tagline: 'Transforming African Education with AI',
      copyright: '© 2026 AI Institute Africa. All rights reserved.'
    }
  },
  sw: {
    nav: { features: 'Vipengele', organizations: 'Kwa Mashirika', pricing: 'Bei', contact: 'Wasiliana', signIn: 'Ingia', getStarted: 'Anza' },
    hero: {
      badge: 'Inayoendeshwa na GPT-5.2 na Blockchain',
      title1: 'Mustakabali wa',
      title2: 'Elimu ya Afrika',
      subtitle: 'Jukwaa la kujifunza linaloendeshwa na AI na vyeti vya blockchain, vipengele vya chuo cha kisasa, na msaada wa lugha nyingi uliotengenezwa kwa mabadiliko ya elimu ya Afrika.',
      registerBtn: 'Sajili Taasisi Yako',
      signUpBtn: 'Jiandikishe Kibinafsi'
    },
    stats: { partners: 'Taasisi Washirika', learners: 'Wanafunzi Hai', languages: 'Lugha za Kiafrika', uptime: 'Wakati wa Uendeshaji' },
    features: {
      title: 'Vipengele Kamili',
      subtitle: 'Kila unachohitaji kubadilisha elimu',
      aiMentor: 'Mshauri wa AI',
      aiMentorDesc: 'Kujifunza kwa kibinafsi na ufundishaji unaoendesha na GPT-5.2 katika lugha 5 za Kiafrika',
      knowledgeGraph: 'Grafu ya Maarifa',
      knowledgeGraphDesc: 'Uchoraji wa dhana na ufuatiliaji wa umahiri',
      blockchain: 'Vyeti vya Blockchain',
      blockchainDesc: 'Vyeti vya kidijitali visivyoweza kubadilishwa',
      smartCampus: 'Chuo cha Kisasa',
      smartCampusDesc: 'Mahudhurio ya RFID/NFC na uthibitishaji wa biometri',
      virtualClass: 'Madarasa ya Mtandaoni',
      virtualClassDesc: 'Ujumuishaji wa Zoom na Google Meet',
      riskPrediction: 'Utabiri wa Hatari',
      riskPredictionDesc: 'Mfumo wa onyo la mapema kwa wanafunzi walio hatarini'
    },
    assistant: {
      title: 'Uliza EduOS AI',
      subtitle: 'Pata majibu ya haraka kuhusu jukwaa letu!',
      placeholder: 'Niulize chochote kuhusu elimu...',
      sendBtn: 'Tuma',
      uploadHint: 'Unaweza pia kupakia picha, sauti, au video',
      recording: 'Inarekodi...',
      processing: 'Inachakata...'
    },
    orgs: {
      title: 'Imeundwa kwa Aina Zote za Mashirika',
      subtitle: 'Iwe ni shule, chuo kikuu, au shirika',
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
      tagline: 'Kubadilisha Elimu ya Afrika na AI',
      copyright: '© 2026 Taasisi ya AI Afrika. Haki zote zimehifadhiwa.'
    }
  },
  sn: {
    nav: { features: 'Zvinhu', organizations: 'KuMasangano', pricing: 'Mutengo', contact: 'Bata', signIn: 'Pinda', getStarted: 'Tanga' },
    hero: {
      badge: 'Inofambiswa neGPT-5.2 neBlockchain',
      title1: 'Ramangwana re',
      title2: 'Dzidzo yeAfrica',
      subtitle: 'Nzvimbo yekudzidza inofambiswa neAI nezvitupa zveblockchain, zvinhu zvechikoro chepamusoro, uye rutsigiro rwemitauro yakawanda rwakavakwa kuchinja dzidzo yeAfrica.',
      registerBtn: 'Nyoresa Sangano Rako',
      signUpBtn: 'Nyoresa Iwe Pachako'
    },
    stats: { partners: 'Masangano Eshamwari', learners: 'Vadzidzi Vanoshanda', languages: 'Mitauro yeAfrica', uptime: 'Nguva Yekushanda' },
    features: {
      title: 'Zvinhu Zvakakwana',
      subtitle: 'Zvese zvaunoda kuchinja dzidzo',
      aiMentor: 'Mudzidzisi weAI',
      aiMentorDesc: 'Kudzidza kwemunhu mumwe chete nekudzidzisa kunofambiswa neGPT-5.2',
      knowledgeGraph: 'Mufananidzo weRuzivo',
      knowledgeGraphDesc: 'Kuratidza mazano nekutevera kugona',
      blockchain: 'Zvitupa zveBlockchain',
      blockchainDesc: 'Zvitupa zvedigitaru zvisingagoni kushandurwa',
      smartCampus: 'Chikoro Chechinyakare',
      smartCampusDesc: 'Kupinda kweRFID/NFC nekusimbisa kwebiometric',
      virtualClass: 'Makirasi eInternet',
      virtualClassDesc: 'Kubatanidza Zoom neGoogle Meet',
      riskPrediction: 'Kufembera Njodzi',
      riskPredictionDesc: 'Hurongwa hweyambiro yekutanga kuvadzidzi vari panjodzi'
    },
    assistant: {
      title: 'Bvunza EduOS AI',
      subtitle: 'Wana mhinduro dzekukurumidza pamusoro penzvimbo yedu!',
      placeholder: 'Ndibvunze chero chinhu pamusoro pedzidzo...',
      sendBtn: 'Tumira',
      uploadHint: 'Unogona zvakare kuisa mifananidzo, ruzha, kana vhidhiyo',
      recording: 'Iri kurekodha...',
      processing: 'Iri kugadzira...'
    },
    orgs: {
      title: 'Yakavakwa Kune Marudzi Ese eMasangano',
      subtitle: 'Kunyangwe uri chikoro, yunivhesiti, kana kambani',
      universities: 'Mayunivhesiti',
      universitiesDesc: 'Nzvimbo dzedzidzo yepamusoro',
      schools: 'Zvikoro',
      schoolsDesc: 'Primary nesekondari',
      government: 'Hurumende',
      governmentDesc: 'Masangano edzidzo yeruzhinji',
      corporations: 'Makambani',
      corporationsDesc: 'Mapurogiramu ekudzidzisa makambani'
    },
    footer: {
      tagline: 'Kuchinja Dzidzo yeAfrica neAI',
      copyright: '© 2026 AI Institute Africa. Kodzero dzese dzakachengetwa.'
    }
  },
  zu: {
    nav: { features: 'Izici', organizations: 'Kuzinhlangano', pricing: 'Amanani', contact: 'Xhumana', signIn: 'Ngena', getStarted: 'Qala' },
    hero: {
      badge: 'Iqhutshwa yi-GPT-5.2 ne-Blockchain',
      title1: 'Ikusasa le',
      title2: 'Mfundo yase-Afrika',
      subtitle: 'Inkundla yokufunda eqhutshwa yi-AI nezitifiketi ze-blockchain, izici zekhempasi ehlakaniphile, nokusekela izilimi eziningi okwakhelwe ukuguqula imfundo yase-Afrika.',
      registerBtn: 'Bhalisa Isikhungo Sakho',
      signUpBtn: 'Bhalisa Ngokwakho'
    },
    stats: { partners: 'Izikhungo Ezilingani', learners: 'Abafundi Abasebenzayo', languages: 'Izilimi zase-Afrika', uptime: 'Isikhathi Sokusebenza' },
    features: {
      title: 'Izici Eziphelele',
      subtitle: 'Konke okudingayo ukuguqula imfundo',
      aiMentor: 'Umeluleki we-AI',
      aiMentorDesc: 'Ukufunda ngokwakho nokufundisa okuqhutshwa yi-GPT-5.2',
      knowledgeGraph: 'Igrafu Yolwazi',
      knowledgeGraphDesc: 'Ukubonisa imiqondo nokulandelela ukwazi',
      blockchain: 'Izitifiketi ze-Blockchain',
      blockchainDesc: 'Izitifiketi zedijithali ezingashintshwa',
      smartCampus: 'Ikhempasi Ehlakaniphile',
      smartCampusDesc: 'Ukuba khona kwe-RFID/NFC nokuqinisekisa kwe-biometric',
      virtualClass: 'Amakilasi Akhona Nge-Inthanethi',
      virtualClassDesc: 'Ukuhlanganisa i-Zoom ne-Google Meet',
      riskPrediction: 'Ukubikezela Ubungozi',
      riskPredictionDesc: 'Uhlelo lokuxwayisa kusenesikhathi kubafundi abasengozini'
    },
    assistant: {
      title: 'Buza i-EduOS AI',
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
      tagline: 'Ukuguqula Imfundo Yase-Afrika Nge-AI',
      copyright: '© 2026 AI Institute Africa. Wonke amalungelo agodliwe.'
    }
  },
  fr: {
    nav: { features: 'Fonctionnalités', organizations: 'Pour les Organisations', pricing: 'Tarifs', contact: 'Contact', signIn: 'Connexion', getStarted: 'Commencer' },
    hero: {
      badge: 'Propulsé par GPT-5.2 et Blockchain',
      title1: "L'avenir de",
      title2: "l'éducation africaine",
      subtitle: "Plateforme d'apprentissage alimentée par l'IA avec des certifications blockchain, des fonctionnalités de campus intelligent et un support multilingue conçu pour la transformation éducative de l'Afrique.",
      registerBtn: 'Enregistrez votre institution',
      signUpBtn: 'Inscription individuelle'
    },
    stats: { partners: 'Institutions partenaires', learners: 'Apprenants actifs', languages: 'Langues africaines', uptime: 'Disponibilité' },
    features: {
      title: 'Fonctionnalités complètes',
      subtitle: "Tout ce dont vous avez besoin pour transformer l'éducation",
      aiMentor: 'Mentor IA Personnel',
      aiMentorDesc: 'Apprentissage personnalisé avec tutorat GPT-5.2 en 5 langues africaines',
      knowledgeGraph: 'Graphe de Connaissances',
      knowledgeGraphDesc: 'Cartographie visuelle des concepts avec suivi de maîtrise',
      blockchain: 'Certifications Blockchain',
      blockchainDesc: 'Certificats numériques inviolables vérifiés sur Ethereum',
      smartCampus: 'Campus Intelligent',
      smartCampusDesc: 'Présence RFID/NFC, vérification biométrique et intégration IoT',
      virtualClass: 'Salles de Classe Virtuelles',
      virtualClassDesc: 'Intégration transparente de Zoom et Google Meet',
      riskPrediction: 'Prédiction des Risques',
      riskPredictionDesc: "Système d'alerte précoce alimenté par l'IA pour les étudiants à risque"
    },
    assistant: {
      title: 'Demandez à EduOS AI',
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
      tagline: "Transformer l'éducation africaine avec l'IA",
      copyright: '© 2026 AI Institute Africa. Tous droits réservés.'
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

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function HomePage() {
  const [language, setLanguage] = useState(() => localStorage.getItem('eduos_language') || 'en');
  const [showAssistant, setShowAssistant] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const t = TRANSLATIONS[language] || TRANSLATIONS.en;

  useEffect(() => {
    localStorage.setItem('eduos_language', language);
  }, [language]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!query.trim() && !uploadedFile) return;
    
    const userMessage = { role: 'user', content: query, file: uploadedFile?.name };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ai/landing-assistant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: query || `Please analyze this ${uploadedFile?.type} file`,
          language,
          has_file: !!uploadedFile
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        // Fallback response if API not available
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: language === 'sw' 
            ? 'Karibu EduOS! Ninaweza kukusaidia na maswali kuhusu elimu, kozi, na jukwaa letu. Je, una swali gani?' 
            : 'Welcome to EduOS! I can help you with questions about education, courses, and our platform. What would you like to know?'
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I\'m here to help! EduOS is an AI-powered learning platform with features like personalized AI tutoring, knowledge graphs, blockchain credentials, and smart campus features. How can I assist you today?'
      }]);
    } finally {
      setIsLoading(false);
      setUploadedFile(null);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
      toast.success(`File "${file.name}" ready to analyze`);
    }
  };

  const features = [
    { icon: Brain, title: t.features.aiMentor, description: t.features.aiMentorDesc, color: 'blue' },
    { icon: Network, title: t.features.knowledgeGraph, description: t.features.knowledgeGraphDesc, color: 'violet' },
    { icon: Shield, title: t.features.blockchain, description: t.features.blockchainDesc, color: 'emerald' },
    { icon: Wifi, title: t.features.smartCampus, description: t.features.smartCampusDesc, color: 'amber' },
    { icon: Video, title: t.features.virtualClass, description: t.features.virtualClassDesc, color: 'red' },
    { icon: TrendingUp, title: t.features.riskPrediction, description: t.features.riskPredictionDesc, color: 'cyan' }
  ];

  const stats = [
    { value: '50+', label: t.stats.partners },
    { value: '100K+', label: t.stats.learners },
    { value: '5', label: t.stats.languages },
    { value: '99.9%', label: t.stats.uptime }
  ];

  const orgTypes = [
    { icon: Building2, title: t.orgs.universities, description: t.orgs.universitiesDesc },
    { icon: GraduationCap, title: t.orgs.schools, description: t.orgs.schoolsDesc },
    { icon: Globe, title: t.orgs.government, description: t.orgs.governmentDesc },
    { icon: Users, title: t.orgs.corporations, description: t.orgs.corporationsDesc }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-zinc-950/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg">EduOS 2026</h1>
                <p className="text-xs text-zinc-500">by AI Institute Africa</p>
              </div>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">{t.nav.features}</a>
              <a href="#organizations" className="text-sm text-zinc-400 hover:text-white transition-colors">{t.nav.organizations}</a>
              <a href="#assistant" className="text-sm text-zinc-400 hover:text-white transition-colors">AI Assistant</a>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Language Selector */}
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-[130px] bg-zinc-900/50 border-white/10" data-testid="home-language-selector">
                  <Globe className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10">
                  {LANGUAGES.map(lang => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Link to="/login">
                <Button variant="ghost" className="text-zinc-400 hover:text-white">
                  {t.nav.signIn}
                </Button>
              </Link>
              <Link to="/register-organization">
                <Button className="bg-blue-500 hover:bg-blue-600">
                  {t.nav.getStarted}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-8">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-400">{t.hero.badge}</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              {t.hero.title1}
              <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent"> {t.hero.title2}</span>
            </h1>
            
            <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
              {t.hero.subtitle}
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register-organization">
                <Button size="lg" className="bg-blue-500 hover:bg-blue-600 h-14 px-8 text-lg">
                  {t.hero.registerBtn}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="h-14 px-8 text-lg border-white/10 hover:bg-white/5">
                  <Play className="w-5 h-5 mr-2" />
                  {t.hero.signUpBtn}
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20">
            {stats.map((stat, index) => (
              <div key={index} className="text-center p-6 rounded-2xl bg-zinc-900/50 border border-white/5">
                <p className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-sm text-zinc-500 mt-2">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Assistant Section */}
      <section id="assistant" className="py-20 px-6 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent">
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
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="border-white/10"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Camera className="w-4 h-4" />
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

      {/* Features Section */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.features.title}</h2>
            <p className="text-zinc-400 max-w-xl mx-auto">{t.features.subtitle}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group p-6 rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-white/10 transition-all duration-300"
              >
                <div className={`w-12 h-12 rounded-xl bg-${feature.color}-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-zinc-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Organizations Section */}
      <section id="organizations" className="py-20 px-6 bg-zinc-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.orgs.title}</h2>
            <p className="text-zinc-400">{t.orgs.subtitle}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {orgTypes.map((org, index) => (
              <div key={index} className="text-center p-8 rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-blue-500/30 transition-all">
                <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
                  <org.icon className="w-8 h-8 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{org.title}</h3>
                <p className="text-sm text-zinc-400">{org.description}</p>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-12">
            <Link to="/register-organization">
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600">
                {t.hero.registerBtn}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold">EduOS 2026</h1>
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
