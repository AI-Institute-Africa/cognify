import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  GraduationCap, 
  Brain, 
  Globe, 
  Building2, 
  Users, 
  Shield, 
  Sparkles,
  ArrowRight,
  CheckCircle,
  Play,
  ChevronRight,
  BookOpen,
  Award,
  TrendingUp,
  Network,
  Wifi,
  Video
} from 'lucide-react';
import { Button } from '../components/ui/button';

const features = [
  {
    icon: Brain,
    title: 'AI Personal Mentor',
    description: 'Personalized learning with GPT-5.2 powered tutoring in 5 African languages',
    color: 'blue'
  },
  {
    icon: Network,
    title: 'Knowledge Graph',
    description: 'Visual mapping of concepts with mastery tracking and spaced repetition',
    color: 'violet'
  },
  {
    icon: Shield,
    title: 'Blockchain Credentials',
    description: 'Tamper-proof digital certificates verified on Ethereum blockchain',
    color: 'emerald'
  },
  {
    icon: Wifi,
    title: 'Smart Campus',
    description: 'RFID/NFC attendance, biometric verification, and IoT integration',
    color: 'amber'
  },
  {
    icon: Video,
    title: 'Virtual Classrooms',
    description: 'Seamless Zoom & Google Meet integration for hybrid learning',
    color: 'red'
  },
  {
    icon: TrendingUp,
    title: 'Risk Prediction',
    description: 'AI-powered early warning system for at-risk students',
    color: 'cyan'
  }
];

const stats = [
  { value: '50+', label: 'Partner Institutions' },
  { value: '100K+', label: 'Active Learners' },
  { value: '5', label: 'African Languages' },
  { value: '99.9%', label: 'Uptime' }
];

const orgTypes = [
  { icon: Building2, title: 'Universities', description: 'Higher education institutions' },
  { icon: GraduationCap, title: 'Schools', description: 'K-12 primary & secondary' },
  { icon: Globe, title: 'Government', description: 'Public education agencies' },
  { icon: Users, title: 'Corporations', description: 'Corporate training programs' }
];

export default function HomePage() {
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
              <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">Features</a>
              <a href="#organizations" className="text-sm text-zinc-400 hover:text-white transition-colors">For Organizations</a>
              <a href="#pricing" className="text-sm text-zinc-400 hover:text-white transition-colors">Pricing</a>
              <a href="#contact" className="text-sm text-zinc-400 hover:text-white transition-colors">Contact</a>
            </div>
            
            <div className="flex items-center gap-3">
              <Link to="/login">
                <Button variant="ghost" className="text-zinc-400 hover:text-white">
                  Sign In
                </Button>
              </Link>
              <Link to="/register-organization">
                <Button className="bg-blue-500 hover:bg-blue-600">
                  Get Started
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
              <span className="text-sm text-blue-400">Powered by GPT-5.2 & Blockchain</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              The Future of
              <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-emerald-400 bg-clip-text text-transparent"> African Education</span>
            </h1>
            
            <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
              AI-powered learning platform with blockchain credentials, smart campus features, 
              and multi-language support built for Africa's educational transformation.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register-organization">
                <Button size="lg" className="bg-blue-500 hover:bg-blue-600 h-14 px-8 text-lg">
                  Register Your Institution
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="h-14 px-8 text-lg border-white/10 hover:bg-white/5">
                  <Play className="w-5 h-5 mr-2" />
                  Individual Sign Up
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

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-zinc-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything You Need</h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              A comprehensive platform combining AI, blockchain, and smart campus technology
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="p-6 rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-white/10 transition-all group"
              >
                <div className={`w-12 h-12 rounded-xl bg-${feature.color}-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-zinc-500">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For Organizations Section */}
      <section id="organizations" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Built for African Institutions
              </h2>
              <p className="text-zinc-400 mb-8">
                Whether you're a university, school, government agency, or corporation, 
                EduOS 2026 scales to meet your needs with multi-tenant architecture and 
                customizable workflows.
              </p>
              
              <div className="space-y-4 mb-8">
                {[
                  'Enroll unlimited students and staff',
                  'Custom branding and white-labeling',
                  'Multi-language support (English, Shona, Ndebele, Swahili, Zulu)',
                  'Blockchain-verified certificates',
                  'Smart campus IoT integration',
                  'AI-powered analytics and insights'
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span className="text-zinc-300">{item}</span>
                  </div>
                ))}
              </div>
              
              <Link to="/register-organization">
                <Button size="lg" className="bg-violet-500 hover:bg-violet-600">
                  Register Your Organization
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {orgTypes.map((org, index) => (
                <div 
                  key={index}
                  className="p-6 rounded-2xl bg-zinc-900/50 border border-white/5 hover:border-violet-500/30 transition-all"
                >
                  <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center mb-4">
                    <org.icon className="w-6 h-6 text-violet-400" />
                  </div>
                  <h3 className="font-semibold mb-1">{org.title}</h3>
                  <p className="text-sm text-zinc-500">{org.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-blue-500/10 via-violet-500/10 to-emerald-500/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Transform Education?
          </h2>
          <p className="text-zinc-400 mb-8">
            Join hundreds of African institutions already using EduOS 2026 to deliver 
            world-class education.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register-organization">
              <Button size="lg" className="bg-blue-500 hover:bg-blue-600 h-14 px-8">
                <Building2 className="w-5 h-5 mr-2" />
                Register Institution
              </Button>
            </Link>
            <Link to="/register">
              <Button size="lg" variant="outline" className="h-14 px-8 border-white/10">
                <Users className="w-5 h-5 mr-2" />
                Individual Sign Up
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="ghost" className="h-14 px-8">
                Sign In
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-bold">EduOS 2026</h3>
                <p className="text-xs text-zinc-500">© 2026 AI Institute Africa</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-zinc-500">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
