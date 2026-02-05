import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { 
  CreditCard, Phone, Building2, CheckCircle, 
  Loader2, Lock, ArrowLeft, Shield
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PAYMENT_METHODS = [
  { id: 'ecocash', name: 'EcoCash', icon: Phone, color: 'green', description: 'Pay with EcoCash mobile money' },
  { id: 'paynow', name: 'Paynow', icon: Building2, color: 'blue', description: 'Pay via Paynow Zimbabwe' },
  { id: 'innbucks', name: 'InnBucks', icon: Phone, color: 'orange', description: 'Pay with InnBucks wallet' },
  { id: 'mastercard', name: 'Card Payment', icon: CreditCard, color: 'red', description: 'Visa/Mastercard' },
];

export default function PaymentPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [paymentResult, setPaymentResult] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [cardDetails, setCardDetails] = useState({ number: '', expiry: '', cvv: '' });

  useEffect(() => {
    loadCourse();
  }, [courseId]);

  const loadCourse = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API_URL}/api/courses/${courseId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCourse(data);
      }
    } catch (error) {
      console.error('Failed to load course:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!selectedMethod) {
      toast.error('Please select a payment method');
      return;
    }

    if ((selectedMethod === 'ecocash' || selectedMethod === 'innbucks' || selectedMethod === 'paynow') && !phoneNumber) {
      toast.error('Please enter your phone number');
      return;
    }

    setProcessing(true);
    try {
      const token = localStorage.getItem('cognify_token');
      
      // Use Paynow for EcoCash and InnBucks
      if (selectedMethod === 'ecocash' || selectedMethod === 'innbucks' || selectedMethod === 'paynow') {
        const response = await fetch(`${API_URL}/api/payments/paynow/initiate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            course_id: courseId,
            phone_number: phoneNumber,
            amount: course?.price || 99.99,
            payment_method: selectedMethod === 'paynow' ? 'ecocash' : selectedMethod
          })
        });

        if (response.ok) {
          const result = await response.json();
          setPaymentResult(result);
          
          // Poll for payment status
          const pollInterval = setInterval(async () => {
            try {
              const statusRes = await fetch(`${API_URL}/api/payments/paynow/check-status?poll_url=${encodeURIComponent(result.poll_url)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
              });
              
              if (statusRes.ok) {
                const statusData = await statusRes.json();
                if (statusData.paid || statusData.status === 'Paid') {
                  clearInterval(pollInterval);
                  toast.success('Payment successful! You are now enrolled.');
                  
                  // Enroll user in course
                  await fetch(`${API_URL}/api/courses/${courseId}/enroll`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                  });
                  
                  setTimeout(() => navigate(`/course/${courseId}`), 2000);
                } else if (statusData.status === 'Failed' || statusData.status === 'Cancelled') {
                  clearInterval(pollInterval);
                  toast.error('Payment failed or cancelled. Please try again.');
                  setPaymentResult(null);
                }
              }
            } catch (err) {
              console.error('Status check error:', err);
            }
          }, 5000); // Check every 5 seconds
          
          // Stop polling after 5 minutes
          setTimeout(() => clearInterval(pollInterval), 300000);
        } else {
          const errorData = await response.json();
          toast.error(errorData.detail || 'Payment initiation failed');
        }
      } else {
        // Card payment - use Stripe
        const response = await fetch(`${API_URL}/api/payments/initiate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            course_id: courseId,
            amount: course?.price || 99.99,
            method: selectedMethod,
            phone_number: phoneNumber
          })
        });

        if (response.ok) {
          const result = await response.json();
          setPaymentResult(result);
          
          // Simulate payment confirmation for demo
          setTimeout(async () => {
            const confirmRes = await fetch(`${API_URL}/api/payments/confirm/${result.payment_id}`, {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (confirmRes.ok) {
              toast.success('Payment successful! You are now enrolled.');
              setTimeout(() => navigate(`/course/${courseId}`), 2000);
            }
          }, 3000);
        }
      }
    } catch (error) {
      console.error('Payment error:', error);
      toast.error('Payment failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  if (paymentResult) {
    return (
      <DashboardLayout>
        <div className="p-8">
          <div className="max-w-lg mx-auto">
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Processing Payment</h2>
              <p className="text-zinc-400 mb-6">Reference: {paymentResult.reference}</p>
              
              {paymentResult.instructions && (
                <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/30 mb-4">
                  <p className="text-blue-400">{paymentResult.instructions}</p>
                </div>
              )}
              
              <p className="text-sm text-zinc-500">
                {selectedMethod === 'ecocash' || selectedMethod === 'innbucks'
                  ? 'Complete payment on your phone. You will be redirected automatically.'
                  : 'Processing your payment. Please wait...'}
              </p>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/courses')}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Courses
          </Button>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Course Summary */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold mb-4">Course Summary</h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-zinc-500">Course</p>
                  <p className="font-semibold">{course?.name}</p>
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Category</p>
                  <Badge className="bg-blue-500/20 text-blue-400">{course?.category || 'Certificate'}</Badge>
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Duration</p>
                  <p>{course?.duration || '4 weeks'}</p>
                </div>
                <div className="pt-4 border-t border-white/10">
                  <p className="text-sm text-zinc-500">Total Amount</p>
                  <p className="text-3xl font-bold text-blue-400">${course?.price || 99.99}</p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                <div className="flex items-center gap-2 text-green-400">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-medium">Secure Payment</span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">Your payment is protected with SSL encryption</p>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold mb-4">Payment Method</h2>
              
              <div className="space-y-3 mb-6">
                {PAYMENT_METHODS.map((method) => (
                  <button
                    key={method.id}
                    onClick={() => setSelectedMethod(method.id)}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                      selectedMethod === method.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className={`w-12 h-12 rounded-xl bg-${method.color}-500/20 flex items-center justify-center`}>
                      <method.icon className={`w-6 h-6 text-${method.color}-400`} />
                    </div>
                    <div className="text-left">
                      <p className="font-medium">{method.name}</p>
                      <p className="text-sm text-zinc-500">{method.description}</p>
                    </div>
                    {selectedMethod === method.id && (
                      <CheckCircle className="w-5 h-5 text-blue-400 ml-auto" />
                    )}
                  </button>
                ))}
              </div>

              {/* Phone number input for mobile money */}
              {(selectedMethod === 'ecocash' || selectedMethod === 'innbucks') && (
                <div className="mb-6">
                  <Label>Phone Number</Label>
                  <Input
                    placeholder="e.g., 0771234567"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="bg-zinc-800 border-white/10 mt-1"
                  />
                </div>
              )}

              {/* Card details for card payment */}
              {selectedMethod === 'mastercard' && (
                <div className="space-y-4 mb-6">
                  <div>
                    <Label>Card Number</Label>
                    <Input
                      placeholder="1234 5678 9012 3456"
                      value={cardDetails.number}
                      onChange={(e) => setCardDetails({...cardDetails, number: e.target.value})}
                      className="bg-zinc-800 border-white/10 mt-1"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Expiry</Label>
                      <Input
                        placeholder="MM/YY"
                        value={cardDetails.expiry}
                        onChange={(e) => setCardDetails({...cardDetails, expiry: e.target.value})}
                        className="bg-zinc-800 border-white/10 mt-1"
                      />
                    </div>
                    <div>
                      <Label>CVV</Label>
                      <Input
                        placeholder="123"
                        type="password"
                        value={cardDetails.cvv}
                        onChange={(e) => setCardDetails({...cardDetails, cvv: e.target.value})}
                        className="bg-zinc-800 border-white/10 mt-1"
                      />
                    </div>
                  </div>
                </div>
              )}

              <Button
                onClick={handlePayment}
                disabled={processing || !selectedMethod}
                className="w-full bg-blue-500 hover:bg-blue-600 h-12"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4 mr-2" />
                    Pay ${course?.price || 99.99}
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
