import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import {
  Search, UserPlus, Loader2, Phone, Mail, CheckCircle2, ArrowLeft,
  Smartphone, Landmark, ShieldCheck, ShieldAlert, Wallet, Receipt, XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

import PaymentStatusBadge from '../components/PaymentStatusBadge';
import PhoneOtpVerification from '../components/PhoneOtpVerification';
import {
  orgAdminSearchLearners,
  orgAdminCreateLearner,
  orgAdminVerifyLearnerPhone,
  orgAdminRecordManualPayment,
  orgAdminVoidPayment,
  getOrgCourses,
} from '../services/api';

const STEPS = ['search', 'verify', 'payment', 'result'];

/**
 * Multi-step "Record External Payment" workflow for Organisation Admins.
 *
 * BRD 11 requirements implemented:
 *  (a) learner search (phone/email/ID) with a "create new learner" fallback
 *  (b) phone verification step, reusing the shared OTP component
 *  (c) course + payment-method selection — EcoCash is visually distinct
 *      from online gateway methods
 *  (d) amount/date/reference/notes entry
 *  (e) result screen with PaymentStatusBadge + a clear "NOT an online
 *      gateway payment" indicator
 *
 * Exported both as the embeddable `ExternalPaymentWorkflow` (used inside a
 * tab on OrgAdminDashboardPage) and as a standalone routed page below.
 */
export function ExternalPaymentWorkflow() {
  const [step, setStep] = useState('search');

  // ---- Step 1: search ----
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null); // null = not searched yet
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newLearner, setNewLearner] = useState({ full_name: '', email: '', phone_number: '', password: '' });
  const [creatingLearner, setCreatingLearner] = useState(false);

  const [selectedLearner, setSelectedLearner] = useState(null);

  // ---- Step 2: verify ----
  const [otpChannel, setOtpChannel] = useState('whatsapp');

  // ---- Step 3: payment details ----
  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [method, setMethod] = useState('ecocash'); // 'ecocash' | 'other_manual'
  const [amount, setAmount] = useState('');
  const [paymentDate, setPaymentDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // ---- Step 4: result ----
  const [result, setResult] = useState(null);
  const [voidReason, setVoidReason] = useState('');
  const [voiding, setVoiding] = useState(false);

  useEffect(() => {
    if (step === 'payment' && courses.length === 0 && !loadingCourses) {
      loadCourses();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const loadCourses = async () => {
    setLoadingCourses(true);
    try {
      const data = await getOrgCourses();
      setCourses(Array.isArray(data) ? data : data?.courses || []);
    } catch (err) {
      toast.error('Failed to load courses for this organisation');
    } finally {
      setLoadingCourses(false);
    }
  };

  const resetAll = () => {
    setStep('search');
    setQuery('');
    setSearchResults(null);
    setShowCreateForm(false);
    setNewLearner({ full_name: '', email: '', phone_number: '', password: '' });
    setSelectedLearner(null);
    setSelectedCourseId('');
    setMethod('ecocash');
    setAmount('');
    setReference('');
    setNotes('');
    setResult(null);
    setVoidReason('');
  };

  // ---------------- Step 1: Search ----------------
  const handleSearch = async (e) => {
    e?.preventDefault?.();
    if (!query.trim()) {
      toast.error('Enter a phone number, email, or user ID to search');
      return;
    }
    setSearching(true);
    try {
      const results = await orgAdminSearchLearners(query.trim());
      setSearchResults(Array.isArray(results) ? results : []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Search failed');
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const pickLearner = (learner) => {
    setSelectedLearner(learner);
    if (learner.phone_number && !learner.phone_verified) {
      setStep('verify');
    } else {
      setStep('payment');
    }
  };

  const handleCreateLearner = async (e) => {
    e.preventDefault();
    if (!newLearner.full_name || !newLearner.password || (!newLearner.email && !newLearner.phone_number)) {
      toast.error('Full name, password, and at least one of email/phone are required');
      return;
    }
    setCreatingLearner(true);
    try {
      const created = await orgAdminCreateLearner(newLearner);
      toast.success('Learner created');
      pickLearner(created);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create learner');
    } finally {
      setCreatingLearner(false);
    }
  };

  // ---------------- Step 2: Verify phone ----------------
  const adminVerify = useCallback(
    (phoneNumber, code) => orgAdminVerifyLearnerPhone(selectedLearner.id, phoneNumber, code),
    [selectedLearner]
  );

  const handlePhoneVerified = () => {
    setSelectedLearner((prev) => (prev ? { ...prev, phone_verified: true } : prev));
    setStep('payment');
  };

  // ---------------- Step 3: Payment ----------------
  const handleSubmitPayment = async (e) => {
    e.preventDefault();
    if (!selectedCourseId) {
      toast.error('Select a course');
      return;
    }
    const amountNum = parseFloat(amount);
    if (!amountNum || amountNum <= 0) {
      toast.error('Enter a valid payment amount');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        learner_id: selectedLearner.id,
        course_id: selectedCourseId,
        amount: amountNum,
        method,
        payment_date: paymentDate || undefined,
        reference: reference || undefined,
        notes: notes || undefined,
      };
      const response = await orgAdminRecordManualPayment(payload);
      setResult(response);
      setStep('result');
      toast.success('Payment recorded successfully');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVoid = async () => {
    if (!result?.payment?.id) return;
    if (!voidReason.trim()) {
      toast.error('Enter a reason for voiding this payment');
      return;
    }
    setVoiding(true);
    try {
      const voidResult = await orgAdminVoidPayment(result.payment.id, voidReason.trim());
      toast.success('Payment voided');
      setResult((prev) => ({ ...prev, payment: { ...prev.payment, status: voidResult.status || 'voided' } }));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to void payment');
    } finally {
      setVoiding(false);
    }
  };

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  return (
    <div className="space-y-6" data-testid="external-payment-workflow">
      {/* Step indicator */}
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        {STEPS.map((s, i) => (
          <React.Fragment key={s}>
            <span className={`px-2 py-1 rounded-full capitalize ${step === s ? 'bg-emerald-500/20 text-emerald-300' : 'bg-zinc-800 text-zinc-500'}`}>
              {i + 1}. {s === 'verify' ? 'Verify Phone' : s}
            </span>
            {i < STEPS.length - 1 && <span>&rarr;</span>}
          </React.Fragment>
        ))}
      </div>

      {/* ---------------- STEP 1: SEARCH ---------------- */}
      {step === 'search' && (
        <div className="glass-card p-6 space-y-5">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-emerald-400" /> Find Learner
          </h3>
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search by phone, email, or user ID"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              data-testid="learner-search-input"
              className="bg-zinc-900/50 border-white/10"
            />
            <Button type="submit" disabled={searching} data-testid="learner-search-btn">
              {searching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
              Search
            </Button>
          </form>

          {searchResults !== null && (
            <div className="space-y-2">
              {searchResults.length > 0 ? (
                searchResults.map((learner) => (
                  <button
                    type="button"
                    key={learner.id}
                    onClick={() => pickLearner(learner)}
                    data-testid={`learner-result-${learner.id}`}
                    className="w-full text-left p-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-800 border border-white/10 flex items-center justify-between transition-colors"
                  >
                    <div>
                      <p className="font-medium">{learner.full_name}</p>
                      <p className="text-xs text-zinc-500 flex items-center gap-3 mt-0.5">
                        {learner.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{learner.email}</span>}
                        {learner.phone_number && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{learner.phone_number}</span>}
                      </p>
                    </div>
                    {learner.phone_verified ? (
                      <Badge className="bg-emerald-500/20 text-emerald-300"><ShieldCheck className="w-3 h-3 mr-1" />Verified</Badge>
                    ) : (
                      <Badge className="bg-amber-500/20 text-amber-300"><ShieldAlert className="w-3 h-3 mr-1" />Unverified</Badge>
                    )}
                  </button>
                ))
              ) : (
                <div className="p-4 rounded-lg bg-zinc-900/40 border border-dashed border-white/10 text-center">
                  <p className="text-sm text-zinc-400 mb-3">No learner matched &quot;{query}&quot;.</p>
                  {!showCreateForm && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setShowCreateForm(true);
                        setNewLearner((prev) => ({
                          ...prev,
                          phone_number: /\d{5,}/.test(query) ? query : '',
                          email: query.includes('@') ? query : '',
                        }));
                      }}
                      data-testid="create-learner-fallback-btn"
                    >
                      <UserPlus className="w-4 h-4 mr-2" /> Create New Learner
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}

          {showCreateForm && (
            <form onSubmit={handleCreateLearner} className="space-y-3 p-4 rounded-lg bg-zinc-900/40 border border-white/10" data-testid="create-learner-form">
              <h4 className="font-medium text-sm text-zinc-300">New Learner Details</h4>
              <div>
                <Label className="text-zinc-400 text-xs">Full Name</Label>
                <Input value={newLearner.full_name} onChange={(e) => setNewLearner({ ...newLearner, full_name: e.target.value })}
                  className="bg-zinc-900/50 border-white/10 mt-1" data-testid="new-learner-name" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-zinc-400 text-xs">Email (optional)</Label>
                  <Input type="email" value={newLearner.email} onChange={(e) => setNewLearner({ ...newLearner, email: e.target.value })}
                    className="bg-zinc-900/50 border-white/10 mt-1" data-testid="new-learner-email" />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Phone Number (optional)</Label>
                  <Input value={newLearner.phone_number} onChange={(e) => setNewLearner({ ...newLearner, phone_number: e.target.value })}
                    className="bg-zinc-900/50 border-white/10 mt-1" data-testid="new-learner-phone" />
                </div>
              </div>
              <div>
                <Label className="text-zinc-400 text-xs">Temporary Password</Label>
                <Input type="password" value={newLearner.password} onChange={(e) => setNewLearner({ ...newLearner, password: e.target.value })}
                  className="bg-zinc-900/50 border-white/10 mt-1" data-testid="new-learner-password" />
              </div>
              <div className="flex gap-2 justify-end pt-1">
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
                <Button type="submit" disabled={creatingLearner} data-testid="create-learner-submit">
                  {creatingLearner && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Create Learner
                </Button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* ---------------- STEP 2: VERIFY PHONE ---------------- */}
      {step === 'verify' && selectedLearner && (
        <div className="glass-card p-6 space-y-5">
          <button type="button" onClick={() => setStep('search')} className="text-xs text-zinc-500 hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" /> Back to search
          </button>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" /> Verify {selectedLearner.full_name}&apos;s Phone
          </h3>
          <PhoneOtpVerification
            phoneNumber={selectedLearner.phone_number}
            purpose="admin_verification"
            channel={otpChannel}
            onChannelChange={setOtpChannel}
            verifyFn={adminVerify}
            onVerified={handlePhoneVerified}
            onCancel={() => setStep('search')}
            verifyLabel="Verify & Continue"
            autoSend={false}
          />
        </div>
      )}

      {/* ---------------- STEP 3: PAYMENT DETAILS ---------------- */}
      {step === 'payment' && selectedLearner && (
        <div className="glass-card p-6 space-y-6">
          <button type="button" onClick={() => setStep('search')} className="text-xs text-zinc-500 hover:text-white flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" /> Back to search
          </button>

          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">{selectedLearner.full_name}</h3>
            <Badge className="bg-emerald-500/20 text-emerald-300"><ShieldCheck className="w-3 h-3 mr-1" />Phone Verified</Badge>
          </div>

          <form onSubmit={handleSubmitPayment} className="space-y-5">
            <div>
              <Label className="text-zinc-400">Course</Label>
              {loadingCourses ? (
                <div className="flex items-center gap-2 text-sm text-zinc-500 mt-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading courses...</div>
              ) : (
                <Select value={selectedCourseId} onValueChange={setSelectedCourseId}>
                  <SelectTrigger data-testid="payment-course-select" className="bg-zinc-900/50 border-white/10 mt-1">
                    <SelectValue placeholder="Select a course" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10">
                    {courses.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.title || c.name} {c.price ? `— $${c.price}` : ''}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Payment method — EcoCash is visually distinct from online
                gateway methods, per BRD 11. */}
            <div>
              <Label className="text-zinc-400 mb-2 block">Payment Method</Label>
              <RadioGroup value={method} onValueChange={setMethod} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label
                  htmlFor="method-ecocash"
                  className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors ${
                    method === 'ecocash' ? 'border-emerald-500 bg-emerald-500/10' : 'border-white/10 bg-zinc-900/40 hover:border-emerald-500/40'
                  }`}
                  data-testid="method-option-ecocash"
                >
                  <RadioGroupItem value="ecocash" id="method-ecocash" className="mt-1" />
                  <div>
                    <div className="flex items-center gap-2 font-medium text-emerald-300">
                      <Smartphone className="w-4 h-4" /> EcoCash (Mobile Money)
                    </div>
                    <p className="text-xs text-zinc-500 mt-1">Offline/manual record — not an online gateway charge.</p>
                  </div>
                </label>
                <label
                  htmlFor="method-other"
                  className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors ${
                    method === 'other_manual' ? 'border-blue-500 bg-blue-500/10' : 'border-white/10 bg-zinc-900/40 hover:border-blue-500/40'
                  }`}
                  data-testid="method-option-other"
                >
                  <RadioGroupItem value="other_manual" id="method-other" className="mt-1" />
                  <div>
                    <div className="flex items-center gap-2 font-medium text-blue-300">
                      <Landmark className="w-4 h-4" /> Other Manual / Offline
                    </div>
                    <p className="text-xs text-zinc-500 mt-1">Cash, bank deposit, or other offline payment.</p>
                  </div>
                </label>
              </RadioGroup>
              <p className="text-[11px] text-amber-400/80 mt-2 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3" /> These are offline/manual payments — distinct from card/online gateway checkout.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-400">Amount ($)</Label>
                <Input type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)}
                  className="bg-zinc-900/50 border-white/10 mt-1" data-testid="payment-amount-input" />
                {selectedCourse?.price != null && (
                  <p className="text-xs text-zinc-600 mt-1">Full course price: ${selectedCourse.price}</p>
                )}
              </div>
              <div>
                <Label className="text-zinc-400">Payment Date</Label>
                <Input type="date" value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)}
                  className="bg-zinc-900/50 border-white/10 mt-1" data-testid="payment-date-input" />
              </div>
            </div>

            <div>
              <Label className="text-zinc-400">Reference (optional)</Label>
              <Input value={reference} onChange={(e) => setReference(e.target.value)}
                placeholder="EcoCash transaction ID, receipt #, etc."
                className="bg-zinc-900/50 border-white/10 mt-1" data-testid="payment-reference-input" />
            </div>

            <div>
              <Label className="text-zinc-400">Notes (optional)</Label>
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="bg-zinc-900/50 border-white/10 mt-1" rows={3} data-testid="payment-notes-input" />
            </div>

            <Button type="submit" disabled={submitting} className="w-full bg-emerald-500 hover:bg-emerald-600" data-testid="payment-submit-btn">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Receipt className="w-4 h-4 mr-2" />}
              Record Payment
            </Button>
          </form>
        </div>
      )}

      {/* ---------------- STEP 4: RESULT ---------------- */}
      {step === 'result' && result && (
        <div className="glass-card p-6 space-y-5" data-testid="payment-result-screen">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Payment Recorded</h3>
              <p className="text-sm text-zinc-500">For {selectedLearner?.full_name}</p>
            </div>
          </div>

          {/* Clear indicator this was NOT an online gateway payment */}
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2 text-amber-300 text-sm" data-testid="not-online-gateway-indicator">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            This was recorded as an <strong>offline / manual payment</strong> ({method === 'ecocash' ? 'EcoCash' : 'Other Manual'}) — it was NOT processed through an online payment gateway.
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-white/10">
              <p className="text-xs text-zinc-500">Amount</p>
              <p className="text-xl font-bold">${result.payment?.amount ?? amount}</p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-white/10">
              <p className="text-xs text-zinc-500 mb-1">Enrollment Status</p>
              <PaymentStatusBadge status={result.enrollment?.payment_status} />
            </div>
          </div>

          {typeof result.minimum_monthly_payment === 'number' && (
            <p className="text-sm text-zinc-400">
              Minimum monthly payment for this course: <strong>${result.minimum_monthly_payment}</strong>
            </p>
          )}

          <div className="flex items-center gap-2 text-sm">
            {result.assessment_access_activated ? (
              <Badge className="bg-emerald-500/20 text-emerald-300"><CheckCircle2 className="w-3 h-3 mr-1" />Assessment access activated</Badge>
            ) : (
              <Badge className="bg-zinc-700 text-zinc-300">Assessment access not yet activated</Badge>
            )}
          </div>

          {/* Void payment */}
          {result.payment?.id && result.payment?.status !== 'voided' && (
            <div className="pt-3 border-t border-white/10 space-y-2">
              <Label className="text-zinc-400 text-xs">Void this payment (mistakes happen)</Label>
              <div className="flex gap-2">
                <Input value={voidReason} onChange={(e) => setVoidReason(e.target.value)} placeholder="Reason for voiding"
                  className="bg-zinc-900/50 border-white/10" data-testid="void-reason-input" />
                <Button type="button" variant="outline" className="border-rose-500/30 text-rose-300" onClick={handleVoid} disabled={voiding} data-testid="void-payment-btn">
                  {voiding ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          )}
          {result.payment?.status === 'voided' && (
            <Badge className="bg-rose-500/20 text-rose-300">Payment voided</Badge>
          )}

          <Button type="button" variant="outline" className="w-full border-white/10" onClick={resetAll} data-testid="record-another-payment-btn">
            <Wallet className="w-4 h-4 mr-2" /> Record Another Payment
          </Button>
        </div>
      )}
    </div>
  );
}

export default function OrgAdminExternalPaymentPage() {
  return (
    <DashboardLayout>
      <Header title="Record External Payment" subtitle="EcoCash & offline / manual payments" />
      <div className="p-4 lg:p-8 max-w-3xl mx-auto">
        <ExternalPaymentWorkflow />
      </div>
    </DashboardLayout>
  );
}
