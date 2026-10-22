import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { 
  CreditCard, Phone, Building2, CheckCircle, 
  Loader2, Lock, ArrowLeft, Shield, AlertTriangle, Calendar, Info, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { getCoursePaymentBreakdown, getCoursePaymentStatus } from '../services/api';
import PhoneInputWithCountry from '../components/PhoneInputWithCountry';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const DEDICATED_PAYNOW_URL = 'https://www.paynow.co.zw/aiia';

const PAYMENT_METHODS = [
  { id: 'paynow', name: 'Paynow Dedicated Portal', icon: Building2, color: 'blue', description: 'Pay directly via paynow.co.zw/aiia (All methods)' },
  { id: 'ecocash', name: 'EcoCash Push Prompt', icon: Phone, color: 'green', description: 'Instant prompt sent to your mobile phone' },
  { id: 'innbucks', name: 'InnBucks Wallet', icon: Phone, color: 'orange', description: 'Pay with InnBucks wallet' },
  { id: 'mastercard', name: 'Visa / Mastercard', icon: CreditCard, color: 'red', description: 'Debit or Credit Card' },
];

export default function PaymentPage() {
  const { courseId: paramCourseId } = useParams();
  const [searchParams] = useSearchParams();
  const courseId = paramCourseId || searchParams.get('course_id') || searchParams.get('courseId');
  const navigate = useNavigate();
  const { user } = useAuth();
  const [course, setCourse] = useState(null);
  const [paymentBreakdown, setPaymentBreakdown] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [paymentOption, setPaymentOption] = useState('minimum'); // 'minimum' | 'full' | 'custom'
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [paymentResult, setPaymentResult] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [cardDetails, setCardDetails] = useState({ number: '', expiry: '', cvv: '' });

  useEffect(() => {
    if (courseId) {
      loadCourseAndBreakdown();
    } else {
      setLoading(false);
    }
  }, [courseId]);

  const loadCourseAndBreakdown = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API_URL}/api/courses/${courseId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCourse(data);
      }

      // Fetch payment breakdown & status
      try {
        const [breakdownData, statusData] = await Promise.all([
          getCoursePaymentBreakdown(courseId).catch(() => null),
          getCoursePaymentStatus(courseId).catch(() => null)
        ]);
        if (breakdownData) setPaymentBreakdown(breakdownData);
        if (statusData) setPaymentStatus(statusData);
      } catch (err) {
        console.warn('Could not fetch payment breakdown:', err);
      }
    } catch (error) {
      console.error('Failed to load course:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEffectiveAmount = () => {
    if (paymentOption === 'custom' && customAmount) {
      return parseFloat(customAmount) || 0;
    }
    if (paymentOption === 'minimum' && paymentBreakdown?.minimum_monthly_payment) {
      return paymentBreakdown.minimum_monthly_payment;
    }
    if (paymentOption === 'full') {
      if (paymentStatus?.amount_remaining != null) {
        return paymentStatus.amount_remaining;
      }
      return course?.price || 99.99;
    }
    return paymentBreakdown?.minimum_monthly_payment || course?.price || 99.99;
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

    const amountToPay = getEffectiveAmount();
    if (!amountToPay || amountToPay <= 0) {
      toast.error('Invalid payment amount. Please select a payment option.');
      return;
    }

    setProcessing(true);
    try {
      const token = localStorage.getItem('cognify_token');

      const extractErrorMessage = (errData, fallback = 'Payment initiation failed') => {
        if (!errData) return fallback;
        const detail = errData.detail || errData.message;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
          return detail.map(d => (typeof d === 'string' ? d : d.msg || JSON.stringify(d))).join('; ') || fallback;
        }
        if (typeof detail === 'object' && detail !== null) {
          return detail.msg || detail.message || JSON.stringify(detail);
        }
        return fallback;
      };

      // Dedicated Paynow portal payment
      if (selectedMethod === 'paynow') {
        const response = await fetch(`${API_URL}/api/payments/paynow/initiate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            course_id: courseId,
            course_name: course?.title || 'Cognify Course',
            amount: amountToPay,
            payment_method: 'paynow',
            phone: phoneNumber || user?.phone_number || ''
          })
        });

        const result = response.ok ? await response.json() : {};
        const payUrl = result.payment_url || DEDICATED_PAYNOW_URL;
        window.open(payUrl, '_blank');
        setPaymentResult({
          reference: result.reference || `COG-PAY-${Date.now().toString().slice(-6)}`,
          payment_url: payUrl,
          instructions: `Payment portal opened in a new tab. Please complete your transaction on Paynow using reference ${result.reference || 'COG-PAY'}.`
        });
        toast.info('Paynow Bill Portal opened in a new tab!');
        return;
      }
      
      // Use Paynow for EcoCash and InnBucks push prompts
      if (selectedMethod === 'ecocash' || selectedMethod === 'innbucks') {
        const response = await fetch(`${API_URL}/api/payments/paynow/initiate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            course_id: courseId,
            course_name: course?.title || 'Cognify Course',
            phone: phoneNumber,
            phone_number: phoneNumber,
            amount: amountToPay,
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
          toast.error(extractErrorMessage(errorData, 'Payment initiation failed'));
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
            course_name: course?.title || 'Cognify Course',
            amount: amountToPay,
            method: selectedMethod,
            phone: phoneNumber,
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
        } else {
          const errorData = await response.json();
          toast.error(extractErrorMessage(errorData, 'Card payment failed'));
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
                <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/30 mb-4 text-left">
                  <p className="text-blue-300 text-sm leading-relaxed">{paymentResult.instructions}</p>
                </div>
              )}

              <div className="space-y-3 my-6">
                <a
                  href={paymentResult.payment_url || DEDICATED_PAYNOW_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all shadow-lg shadow-blue-500/20"
                >
                  <ExternalLink className="w-4 h-4" /> Open Paynow Dedicated Bill Portal
                </a>
                <p className="text-xs text-zinc-400">
                  Bill Link: <a href={DEDICATED_PAYNOW_URL} target="_blank" rel="noreferrer" className="font-mono text-blue-400 underline">{DEDICATED_PAYNOW_URL}</a>
                </p>
              </div>
              
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
            {/* Course Summary + Payment Breakdown */}
            <div className="space-y-4">
              <div className="glass-card p-6">
                <h2 className="text-xl font-bold mb-4">Course Payment Summary</h2>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-zinc-500">Course</p>
                    <p className="font-semibold">{course?.name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-zinc-500">Total Price</p>
                      <p className="text-2xl font-bold text-blue-400">${course?.price || 99.99}</p>
                    </div>
                    {(paymentBreakdown?.duration_months || course?.duration_months) && (
                      <div>
                        <p className="text-sm text-zinc-500">Duration</p>
                        <p className="font-semibold text-zinc-300">{paymentBreakdown?.duration_months || course?.duration_months} month{(paymentBreakdown?.duration_months || course?.duration_months) > 1 ? 's' : ''}</p>
                      </div>
                    )}
                  </div>

                  {paymentBreakdown?.minimum_monthly_payment && (
                    <div className="pt-3 border-t border-white/10">
                      <p className="text-sm text-zinc-500 flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Min. Monthly Payment</p>
                      <p className="text-xl font-bold text-emerald-400">${Number(paymentBreakdown.minimum_monthly_payment).toFixed(2)}<span className="text-sm font-normal text-zinc-400 ml-1">/ month</span></p>
                      <p className="text-xs text-zinc-500 mt-1">= ${course?.price || 99.99} ÷ {paymentBreakdown.duration_months} months</p>
                    </div>
                  )}

                  {paymentStatus && (
                    <div className="pt-3 border-t border-white/10 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-zinc-500">Payment Status</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                          paymentStatus.payment_status === 'CURRENT' ? 'bg-emerald-500/20 text-emerald-400' :
                          paymentStatus.payment_status === 'PARTIALLY_PAID' ? 'bg-amber-500/20 text-amber-400' :
                          paymentStatus.payment_status === 'OVERDUE' ? 'bg-red-500/20 text-red-400' :
                          paymentStatus.payment_status === 'COMPLETED' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-zinc-500/20 text-zinc-400'
                        }`}>{paymentStatus.payment_status?.replace('_', ' ')}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-zinc-500">Assessment Access</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${paymentStatus.assessment_eligible ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                          {paymentStatus.assessment_eligible ? '✓ Available' : '⚠ Locked'}
                        </span>
                      </div>
                      {paymentStatus.amount_remaining > 0 && (
                        <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30">
                          <p className="text-xs text-amber-300 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                            ${Number(paymentStatus.amount_remaining).toFixed(2)} more needed to unlock assessments
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Payment Option Selector (if breakdown available) */}
              {paymentBreakdown?.minimum_monthly_payment && paymentStatus?.payment_status !== 'COMPLETED' && (
                <div className="glass-card p-4">
                  <h3 className="text-sm font-semibold mb-3 text-zinc-400 uppercase tracking-wider">Payment Option</h3>
                  <div className="space-y-2">
                    {['minimum', 'full', 'custom'].map((opt) => (
                      <button
                        key={opt}
                        onClick={() => setPaymentOption(opt)}
                        className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all text-left ${
                          paymentOption === opt ? 'border-blue-500 bg-blue-500/10' : 'border-white/10 hover:border-white/20'
                        }`}
                      >
                        <span className="text-sm font-medium capitalize">
                          {opt === 'minimum' ? `Monthly Minimum — $${Number(paymentBreakdown.minimum_monthly_payment).toFixed(2)}` :
                           opt === 'full' ? `Full Remaining — $${Number(paymentStatus?.amount_remaining || course?.price || 0).toFixed(2)}` :
                           'Custom Amount'}
                        </span>
                        {paymentOption === opt && <CheckCircle className="w-4 h-4 text-blue-400" />}
                      </button>
                    ))}
                  </div>
                  {paymentOption === 'custom' && (
                    <div className="mt-3">
                      <Label className="text-xs text-zinc-400">Enter Amount (USD)</Label>
                      <Input
                        type="number"
                        min="1"
                        step="0.01"
                        placeholder="e.g. 25.00"
                        value={customAmount}
                        onChange={(e) => setCustomAmount(e.target.value)}
                        className="bg-zinc-800 border-white/10 mt-1"
                      />
                    </div>
                  )}
                  <div className="mt-3 pt-3 border-t border-white/10 flex justify-between">
                    <span className="text-sm text-zinc-400">You are paying</span>
                    <span className="text-lg font-bold text-blue-400">${Number(getEffectiveAmount()).toFixed(2)}</span>
                  </div>
                </div>
              )}

              <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                <div className="flex items-center gap-2 text-emerald-400">
                  <Shield className="w-4 h-4" />
                  <span className="text-sm font-medium">Secure Payment</span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">Your payment is protected with SSL encryption</p>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold mb-4">Payment Method</h2>
              
              {/* Dedicated Paynow Direct Bill Payment Banner */}
              <div className="p-4 mb-5 rounded-xl bg-gradient-to-r from-blue-950/60 via-indigo-950/40 to-cyan-950/40 border border-blue-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs font-semibold tracking-wider uppercase text-blue-400">Official Paynow Portal</span>
                  </div>
                  <p className="text-sm font-medium text-white">Direct Online Bill Payment</p>
                  <p className="text-xs text-zinc-400">Pay directly with EcoCash, OneMoney, InnBucks, Visa & Mastercard on Paynow.</p>
                </div>
                <a
                  href={DEDICATED_PAYNOW_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold whitespace-nowrap transition-colors shadow-lg shadow-blue-500/20"
                >
                  Pay on Paynow
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>

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
              {(selectedMethod === 'ecocash' || selectedMethod === 'innbucks' || selectedMethod === 'paynow') && (
                <div className="mb-6 space-y-1.5">
                  <Label className="text-sm text-zinc-300">Mobile Money Phone Number</Label>
                  <PhoneInputWithCountry
                    value={phoneNumber}
                    onChange={(fullPhone) => setPhoneNumber(fullPhone)}
                    placeholder="e.g. 77 123 4567"
                  />
                  <p className="text-xs text-zinc-500">
                    EcoCash / InnBucks prompt will be dispatched to this number
                  </p>
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
