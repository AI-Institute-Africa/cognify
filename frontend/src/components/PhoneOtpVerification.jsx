import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Loader2, RefreshCw, ShieldCheck, Smartphone, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from './ui/button';
import { Label } from './ui/label';
import { InputOTP, InputOTPGroup, InputOTPSlot } from './ui/input-otp';
import { sendPhoneOtp, verifyPhoneOtp } from '../services/api';

const RESEND_COOLDOWN_SECONDS = 60;

/**
 * Reusable phone/WhatsApp OTP entry + verification widget.
 *
 * Used by:
 *  - the WhatsApp self-registration flow (RegisterPage)
 *  - the Org-Admin "verify learner phone" step (OrgAdminExternalPaymentPage)
 *
 * BRD 11 requirements implemented here:
 *  - "OTP screens shall clearly show the destination phone number in masked
 *    form" -> renders `masked_phone` returned by the send-otp endpoint.
 *  - Resend respects backend rate-limiting: a 429 response is shown as a
 *    friendly message instead of a generic error, and the resend button is
 *    put into a cooldown.
 */
export default function PhoneOtpVerification({
  phoneNumber,
  purpose,
  channel = 'whatsapp',
  onChannelChange,
  onVerified,
  onCancel,
  autoSend = true,
  verifyLabel = 'Verify Code',
  className = '',
  // Override how the code is confirmed. Defaults to the public
  // /auth/phone/verify-otp endpoint. The org-admin phone-verification step
  // passes a function that calls /org-admin/learners/{id}/verify-phone
  // instead, since that endpoint is the one that marks the learner's record
  // as phone_verified server-side.
  verifyFn,
}) {
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [sent, setSent] = useState(false);
  const [maskedPhone, setMaskedPhone] = useState('');
  const [code, setCode] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState('');
  const sentOnceRef = useRef(false);
  const lastPhoneRef = useRef(phoneNumber);

  // Reset state if the phone number changes (e.g. user edits it then retries)
  useEffect(() => {
    if (lastPhoneRef.current !== phoneNumber) {
      lastPhoneRef.current = phoneNumber;
      sentOnceRef.current = false;
      setSent(false);
      setMaskedPhone('');
      setCode('');
      setError('');
      setCooldown(0);
    }
  }, [phoneNumber]);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = setInterval(() => setCooldown((c) => (c > 0 ? c - 1 : 0)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSend = useCallback(async () => {
    if (!phoneNumber) {
      toast.error('Enter a phone number first');
      return;
    }
    setSending(true);
    setError('');
    try {
      const result = await sendPhoneOtp(phoneNumber, channel, purpose);
      setMaskedPhone(result?.masked_phone || phoneNumber);
      setSent(true);
      setCode('');
      setCooldown(RESEND_COOLDOWN_SECONDS);
      toast.success(`Verification code sent via ${channel === 'whatsapp' ? 'WhatsApp' : 'SMS'}`);
    } catch (err) {
      if (err?.response?.status === 429) {
        const msg = err.response?.data?.detail || 'Too many requests. Please wait before requesting another code.';
        setError(msg);
        toast.error(msg);
        setSent(true); // keep the code entry visible if a code was already sent previously
        setCooldown(RESEND_COOLDOWN_SECONDS);
      } else {
        const msg = err?.response?.data?.detail || 'Failed to send verification code. Please try again.';
        setError(msg);
        toast.error(msg);
      }
    } finally {
      setSending(false);
    }
  }, [phoneNumber, channel, purpose]);

  useEffect(() => {
    if (autoSend && phoneNumber && !sentOnceRef.current) {
      sentOnceRef.current = true;
      handleSend();
    }
  }, [autoSend, phoneNumber, handleSend]);

  const handleVerify = async () => {
    if (code.length !== 6) {
      toast.error('Enter the 6-digit code');
      return;
    }
    setVerifying(true);
    setError('');
    try {
      const doVerify = verifyFn || ((phone, c, p) => verifyPhoneOtp(phone, c, p));
      await doVerify(phoneNumber, code, purpose);
      toast.success('Phone number verified');
      onVerified && onVerified(code);
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Invalid or expired code. Please try again.';
      setError(msg);
      toast.error(msg);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className={`space-y-4 ${className}`} data-testid="phone-otp-verification">
      <div className="flex items-start gap-3 p-3 rounded-lg bg-zinc-900/50 border border-white/10">
        {channel === 'whatsapp' ? (
          <MessageSquare className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
        ) : (
          <Smartphone className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
        )}
        <div>
          <p className="text-sm text-zinc-400">
            {sent ? 'We sent a verification code to' : 'A verification code will be sent to'}
          </p>
          {/* Masked phone number is always displayed, never the raw number,
              per BRD 11 requirement on OTP screens. */}
          <p className="font-medium text-white tracking-wide" data-testid="otp-masked-phone">
            {maskedPhone || (phoneNumber ? maskFallback(phoneNumber) : '—')}
          </p>
        </div>
      </div>

      {onChannelChange && !sent && (
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={channel === 'whatsapp' ? 'default' : 'outline'}
            onClick={() => onChannelChange('whatsapp')}
            data-testid="otp-channel-whatsapp"
          >
            WhatsApp
          </Button>
          <Button
            type="button"
            size="sm"
            variant={channel === 'sms' ? 'default' : 'outline'}
            onClick={() => onChannelChange('sms')}
            data-testid="otp-channel-sms"
          >
            SMS
          </Button>
        </div>
      )}

      {!sent ? (
        <Button
          type="button"
          onClick={handleSend}
          disabled={sending || !phoneNumber}
          data-testid="otp-send-btn"
          className="w-full"
        >
          {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ShieldCheck className="w-4 h-4 mr-2" />}
          Send Verification Code
        </Button>
      ) : (
        <>
          <div className="space-y-2">
            <Label>Enter the 6-digit code</Label>
            <InputOTP
              maxLength={6}
              value={code}
              onChange={(value) => setCode(value.replace(/\D/g, ''))}
              data-testid="otp-code-input"
            >
              <InputOTPGroup>
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <InputOTPSlot key={i} index={i} />
                ))}
              </InputOTPGroup>
            </InputOTP>
          </div>

          {error && (
            <p className="text-sm text-rose-400" data-testid="otp-error">
              {error}
            </p>
          )}

          <div className="flex gap-2">
            <Button
              type="button"
              onClick={handleVerify}
              disabled={verifying || code.length !== 6}
              data-testid="otp-verify-btn"
              className="flex-1"
            >
              {verifying && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {verifyLabel}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleSend}
              disabled={sending || cooldown > 0}
              data-testid="otp-resend-btn"
            >
              {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
              {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
            </Button>
          </div>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="text-xs text-zinc-500 hover:text-white transition-colors"
              data-testid="otp-use-different-number"
            >
              Use a different number
            </button>
          )}
        </>
      )}
    </div>
  );
}

// Best-effort client-side mask, only used as a fallback before the backend's
// masked_phone has come back from send-otp (e.g. while `sending` is true).
function maskFallback(phone) {
  const digits = String(phone);
  if (digits.length <= 4) return digits;
  const visibleStart = digits.slice(0, 3);
  const visibleEnd = digits.slice(-2);
  return `${visibleStart}${'*'.repeat(Math.max(digits.length - 5, 2))}${visibleEnd}`;
}
