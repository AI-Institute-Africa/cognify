import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import PhoneOtpVerification from '../PhoneOtpVerification';
import { sendPhoneOtp, verifyPhoneOtp } from '../../services/api';

jest.mock('../../services/api', () => ({
  sendPhoneOtp: jest.fn(),
  verifyPhoneOtp: jest.fn(),
}));

jest.mock('sonner', () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

describe('PhoneOtpVerification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sends a code automatically and shows the masked phone number returned by the backend', async () => {
    sendPhoneOtp.mockResolvedValueOnce({ masked_phone: '+26****89', expires_in_minutes: 10 });

    render(<PhoneOtpVerification phoneNumber="+263771234589" purpose="registration" />);

    await waitFor(() =>
      expect(sendPhoneOtp).toHaveBeenCalledWith('+263771234589', 'whatsapp', 'registration')
    );

    const maskedPhone = await screen.findByTestId('otp-masked-phone');
    expect(maskedPhone).toHaveTextContent('+26****89');
    // The raw, unmasked phone number must never be shown once the backend's
    // masked form is available (BRD 11).
    expect(screen.queryByText('+263771234589')).not.toBeInTheDocument();
  });

  it('shows a friendly rate-limit message and disables resend when the backend returns 429', async () => {
    // Simulate the backend's rate limit kicking in on the very first send
    // (e.g. the learner already requested a code moments ago in another tab).
    sendPhoneOtp.mockRejectedValueOnce({
      response: { status: 429, data: { detail: 'Please wait before requesting another code' } },
    });

    render(<PhoneOtpVerification phoneNumber="+263771234589" purpose="registration" />);

    const errorEl = await screen.findByTestId('otp-error');
    expect(errorEl).toHaveTextContent('Please wait before requesting another code');

    const resendBtn = screen.getByTestId('otp-resend-btn');
    expect(resendBtn).toBeDisabled();
    expect(resendBtn).toHaveTextContent(/Resend in \d+s/);
  });

  it('verifies the entered code and calls onVerified on success', async () => {
    sendPhoneOtp.mockResolvedValueOnce({ masked_phone: '+26****89' });
    verifyPhoneOtp.mockResolvedValueOnce({ success: true });
    const onVerified = jest.fn();

    render(
      <PhoneOtpVerification phoneNumber="+263771234589" purpose="registration" onVerified={onVerified} />
    );

    const input = await screen.findByTestId('otp-code-input');
    const user = userEvent.setup();
    await user.type(input, '123456');

    await user.click(screen.getByTestId('otp-verify-btn'));

    await waitFor(() =>
      expect(verifyPhoneOtp).toHaveBeenCalledWith('+263771234589', '123456', 'registration')
    );
    expect(onVerified).toHaveBeenCalledWith('123456');
  });

  it('shows an error message when verification fails', async () => {
    sendPhoneOtp.mockResolvedValueOnce({ masked_phone: '+26****89' });
    verifyPhoneOtp.mockRejectedValueOnce({ response: { data: { detail: 'Incorrect code' } } });

    render(<PhoneOtpVerification phoneNumber="+263771234589" purpose="registration" />);

    const input = await screen.findByTestId('otp-code-input');
    const user = userEvent.setup();
    await user.type(input, '000000');
    await user.click(screen.getByTestId('otp-verify-btn'));

    expect(await screen.findByTestId('otp-error')).toHaveTextContent('Incorrect code');
  });

  it('uses a custom verifyFn when provided (org-admin verification flow)', async () => {
    sendPhoneOtp.mockResolvedValueOnce({ masked_phone: '+26****89' });
    const customVerify = jest.fn().mockResolvedValueOnce({ success: true });
    const onVerified = jest.fn();

    render(
      <PhoneOtpVerification
        phoneNumber="+263771234589"
        purpose="admin_verification"
        verifyFn={customVerify}
        onVerified={onVerified}
      />
    );

    const input = await screen.findByTestId('otp-code-input');
    const user = userEvent.setup();
    await user.type(input, '654321');
    await user.click(screen.getByTestId('otp-verify-btn'));

    await waitFor(() =>
      expect(customVerify).toHaveBeenCalledWith('+263771234589', '654321', 'admin_verification')
    );
    // The public verify-otp endpoint must NOT be called when an override is given.
    expect(verifyPhoneOtp).not.toHaveBeenCalled();
    expect(onVerified).toHaveBeenCalledWith('654321');
  });
});
