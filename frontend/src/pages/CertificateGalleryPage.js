import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Award, Shield, Calendar, BookOpen, Share2,
  Loader2, ExternalLink, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

export default function CertificateGalleryPage() {
  const { userId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [certificates, setCertificates] = useState([]);
  const [targetUser, setTargetUser] = useState(null);

  const isOwnGallery = !userId || userId === user?.id;

  useEffect(() => {
    loadGallery();
  }, [userId]);

  const loadGallery = async () => {
    try {
      const url = isOwnGallery
        ? `${API}/api/certificates/gallery/my`
        : `${API}/api/certificates/gallery/user/${userId}`;
      const { data } = await axios.get(url, { headers: getAuth() });
      setCertificates(data.certificates || []);
      if (data.user) setTargetUser(data.user);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load certificates');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = (cert) => {
    const url = `${window.location.origin}/verify-certificate/${cert.verification_code}`;
    if (navigator.share) {
      navigator.share({ title: `Certificate: ${cert.course_name}`, url });
    } else {
      navigator.clipboard.writeText(url);
      toast.success('Verification link copied!');
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  const displayName = isOwnGallery ? user?.full_name : targetUser?.full_name;

  return (
    <DashboardLayout>
      <Header
        title="Certificate Gallery"
        subtitle={`${displayName || 'Student'}'s earned certificates`}
      />

      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Gallery Header */}
          <div className="glass-card p-6 mb-8 flex items-center justify-between" data-testid="gallery-header">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                <Award className="w-7 h-7 text-amber-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{displayName || 'Student'}</h2>
                <p className="text-sm text-zinc-400">{certificates.length} certificate{certificates.length !== 1 ? 's' : ''} earned</p>
              </div>
            </div>
            <Badge className="bg-emerald-500/20 text-emerald-400 text-sm px-3 py-1">
              <Shield className="w-3.5 h-3.5 mr-1.5" />
              Verified Portfolio
            </Badge>
          </div>

          {/* Certificate Grid */}
          {certificates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="certificate-grid">
              {certificates.map((cert) => (
                <div
                  key={cert.id}
                  className="glass-card overflow-hidden group hover:border-amber-500/30 transition-all cursor-pointer"
                  onClick={() => navigate(`/certificate/${cert.id}`)}
                  data-testid={`cert-card-${cert.id}`}
                >
                  {/* Card Header */}
                  <div className="bg-gradient-to-r from-blue-600/80 to-violet-600/80 p-4 text-center">
                    <Award className="w-8 h-8 mx-auto mb-1 text-white/90" />
                    <p className="text-xs text-blue-100 uppercase tracking-wider">Certificate of Completion</p>
                  </div>

                  {/* Card Body */}
                  <div className="p-5 space-y-3">
                    <h3 className="font-semibold text-base leading-tight group-hover:text-amber-400 transition-colors">
                      {cert.course_name}
                    </h3>

                    {cert.organization_name && (
                      <p className="text-xs text-zinc-500 flex items-center gap-1">
                        <BookOpen className="w-3 h-3" />
                        {cert.organization_name}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {cert.issued_at ? new Date(cert.issued_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
                      </span>
                      <Badge className="bg-emerald-500/15 text-emerald-400 text-[10px]">
                        {cert.grade || 'Pass'}
                      </Badge>
                    </div>

                    <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                      <span className="text-[10px] font-mono text-zinc-500">{cert.verification_code}</span>
                      <div className="flex gap-1.5">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0"
                          onClick={(e) => { e.stopPropagation(); handleShare(cert); }}
                          data-testid={`share-cert-${cert.id}`}
                        >
                          <Share2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card p-16 text-center" data-testid="empty-gallery">
              <Award className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Certificates Yet</h3>
              <p className="text-sm text-zinc-500 mb-6">
                {isOwnGallery
                  ? 'Complete courses to earn certificates and build your portfolio.'
                  : 'This user has not earned any certificates yet.'}
              </p>
              {isOwnGallery && (
                <Button onClick={() => navigate('/courses')} className="bg-violet-500 hover:bg-violet-600">
                  <BookOpen className="w-4 h-4 mr-2" />
                  Browse Courses
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
