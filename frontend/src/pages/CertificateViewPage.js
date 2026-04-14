import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Award,
  Download,
  Share2,
  CheckCircle,
  Calendar,
  Shield,
  Printer,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import QRCode from 'qrcode';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CertificateViewPage() {
  const { certificateId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [certificate, setCertificate] = useState(null);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const certificateRef = useRef(null);

  useEffect(() => {
    if (certificateId) {
      loadCertificate();
    }
  }, [certificateId]);

  const loadCertificate = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const { data } = await axios.get(`${API}/api/certificates/${certificateId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      setCertificate(data);
      
      // Generate QR code for verification
      const verificationUrl = `${window.location.origin}/verify-certificate/${data.verification_code}`;
      const qr = await QRCode.toDataURL(verificationUrl, {
        width: 150,
        margin: 2,
        color: { dark: '#000000', light: '#ffffff' }
      });
      setQrCodeUrl(qr);
    } catch (error) {
      console.error('Failed to load certificate:', error);
      toast.error('Certificate not found');
      navigate('/credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await axios.get(`${API}/api/certificates/${certificateId}/pdf`, {
        headers: { 'Authorization': `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificate-${certificate?.verification_code || certificateId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Certificate downloaded!');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download certificate');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    const shareUrl = `${window.location.origin}/verify-certificate/${certificate?.verification_code}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Certificate: ${certificate?.course_name}`,
          text: `Check out my certificate from Cognify!`,
          url: shareUrl
        });
      } catch (error) {
        if (error.name !== 'AbortError') {
          copyToClipboard(shareUrl);
        }
      }
    } else {
      copyToClipboard(shareUrl);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Verification link copied to clipboard!');
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

  if (!certificate) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <Award className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Certificate Not Found</h2>
            <Button onClick={() => navigate('/credentials')}>Back to Credentials</Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Certificate"
        subtitle="View and share your achievement"
      />
      
      <div className="p-8">
        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mb-6 justify-end print:hidden">
          <Button
            onClick={handlePrint}
            variant="outline"
            className="border-white/10"
            data-testid="print-certificate-btn"
          >
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <Button
            onClick={handleDownloadPDF}
            variant="outline"
            className="border-white/10"
            data-testid="download-certificate-btn"
          >
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
          <Button
            onClick={handleShare}
            className="bg-violet-500 hover:bg-violet-600"
            data-testid="share-certificate-btn"
          >
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>

        {/* Certificate Display */}
        <div 
          ref={certificateRef}
          className="max-w-4xl mx-auto bg-white text-zinc-900 rounded-2xl shadow-2xl overflow-hidden print:shadow-none"
          id="certificate-content"
        >
          {/* Certificate Header */}
          <div className="bg-gradient-to-r from-blue-600 to-violet-600 p-8 text-white text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Award className="w-10 h-10" />
              <h1 className="text-3xl font-bold tracking-tight">CERTIFICATE OF COMPLETION</h1>
            </div>
            <p className="text-blue-100">This certifies that</p>
          </div>

          {/* Certificate Body */}
          <div className="p-12 text-center">
            {/* Recipient Name */}
            <h2 className="text-4xl font-bold text-zinc-800 mb-2 font-serif">
              {certificate.recipient_name}
            </h2>
            
            <p className="text-zinc-500 mb-8">has successfully completed</p>

            {/* Course Name */}
            <div className="bg-zinc-50 rounded-xl p-6 mb-8 inline-block">
              <h3 className="text-2xl font-bold text-blue-600 mb-2">
                {certificate.course_name}
              </h3>
              {certificate.organization_name && (
                <p className="text-zinc-600">
                  Offered by {certificate.organization_name}
                </p>
              )}
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8 text-sm">
              <div>
                <p className="text-zinc-500 mb-1">Issue Date</p>
                <p className="font-semibold text-zinc-800">
                  {new Date(certificate.issued_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
              <div>
                <p className="text-zinc-500 mb-1">Duration</p>
                <p className="font-semibold text-zinc-800">
                  {certificate.duration_weeks || 4} Weeks
                </p>
              </div>
              <div>
                <p className="text-zinc-500 mb-1">Grade</p>
                <p className="font-semibold text-zinc-800">
                  {certificate.grade || 'Pass'}
                </p>
              </div>
              <div>
                <p className="text-zinc-500 mb-1">Credits</p>
                <p className="font-semibold text-zinc-800">
                  {certificate.credits || 3} Credits
                </p>
              </div>
            </div>

            {/* QR Code and Verification */}
            <div className="flex items-center justify-center gap-8 pt-8 border-t border-zinc-200">
              <div className="text-left">
                <p className="text-xs text-zinc-500 mb-1">Verification Code</p>
                <p className="font-mono text-sm font-bold text-zinc-800">
                  {certificate.verification_code}
                </p>
                <p className="text-xs text-zinc-400 mt-2">
                  Scan QR code to verify authenticity
                </p>
              </div>
              
              {qrCodeUrl && (
                <div className="p-2 bg-white rounded-lg border border-zinc-200">
                  <img 
                    src={qrCodeUrl} 
                    alt="Verification QR Code"
                    className="w-24 h-24"
                  />
                </div>
              )}
            </div>

            {/* Signature Section */}
            <div className="flex justify-around mt-12 pt-8 border-t border-zinc-200">
              <div className="text-center">
                <div className="w-32 h-0.5 bg-zinc-300 mb-2 mx-auto" />
                <p className="text-xs text-zinc-500">Instructor</p>
                <p className="font-semibold text-zinc-800 text-sm">
                  {certificate.instructor_name || 'Course Instructor'}
                </p>
              </div>
              <div className="text-center">
                <div className="w-32 h-0.5 bg-zinc-300 mb-2 mx-auto" />
                <p className="text-xs text-zinc-500">Platform</p>
                <p className="font-semibold text-zinc-800 text-sm">Cognify Learning</p>
              </div>
            </div>
          </div>

          {/* Certificate Footer */}
          <div className="bg-zinc-50 p-4 text-center border-t border-zinc-200">
            <p className="text-xs text-zinc-500">
              Certificate ID: {certificate.id} | Verify at: cognify.edu/verify/{certificate.verification_code}
            </p>
          </div>
        </div>

        {/* Verification Status Card */}
        <div className="max-w-4xl mx-auto mt-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3 print:hidden">
          <Shield className="w-6 h-6 text-emerald-400" />
          <div>
            <p className="font-semibold text-emerald-400">Verified Certificate</p>
            <p className="text-sm text-zinc-400">
              This certificate has been verified and is recorded on our secure platform.
            </p>
          </div>
        </div>
      </div>

      {/* Print Styles */}
      <style>{`
        @media print {
          @page {
            size: landscape;
            margin: 0.5in;
          }
          body * {
            visibility: hidden;
          }
          #certificate-content, #certificate-content * {
            visibility: visible;
          }
          #certificate-content {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            box-shadow: none !important;
            border-radius: 0 !important;
          }
          .print\\:hidden {
            display: none !important;
          }
        }
      `}</style>
    </DashboardLayout>
  );
}

// Certificate Verification Page (Public)
export function CertificateVerifyPage() {
  const { verificationCode } = useParams();
  const [loading, setLoading] = useState(true);
  const [certificate, setCertificate] = useState(null);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    verifyCertificate();
  }, [verificationCode]);

  const verifyCertificate = async () => {
    try {
      const { data } = await axios.get(`${API}/api/certificates/verify/${verificationCode}`);
      setCertificate(data.certificate);
      setVerified(data.verified);
    } catch (error) {
      console.error('Verification error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {verified && certificate ? (
          <div className="glass-card p-8 text-center">
            <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-emerald-400" />
            </div>
            
            <Badge className="bg-emerald-500/20 text-emerald-400 mb-4">
              <Shield className="w-3 h-3 mr-1" />
              Verified Certificate
            </Badge>
            
            <h1 className="text-2xl font-bold mb-2">{certificate.course_name}</h1>
            <p className="text-zinc-400 mb-6">
              Awarded to <span className="text-white font-semibold">{certificate.recipient_name}</span>
            </p>
            
            <div className="grid grid-cols-2 gap-4 text-sm mb-6">
              <div className="p-3 rounded-lg bg-zinc-800/50">
                <Calendar className="w-4 h-4 text-zinc-500 mx-auto mb-1" />
                <p className="text-zinc-500">Issued</p>
                <p className="font-semibold">
                  {new Date(certificate.issued_at).toLocaleDateString()}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-zinc-800/50">
                <Award className="w-4 h-4 text-zinc-500 mx-auto mb-1" />
                <p className="text-zinc-500">Grade</p>
                <p className="font-semibold">{certificate.grade || 'Pass'}</p>
              </div>
            </div>
            
            <p className="text-xs text-zinc-500">
              Verification Code: {verificationCode}
            </p>
          </div>
        ) : (
          <div className="glass-card p-8 text-center">
            <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
              <Shield className="w-10 h-10 text-red-400" />
            </div>
            
            <h1 className="text-2xl font-bold mb-2">Certificate Not Found</h1>
            <p className="text-zinc-400">
              The verification code "{verificationCode}" could not be verified.
            </p>
          </div>
        )}
        
        <p className="text-center text-xs text-zinc-600 mt-6">
          Powered by Cognify Learning Platform
        </p>
      </div>
    </div>
  );
}
