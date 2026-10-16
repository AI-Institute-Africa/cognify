// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom does not implement document.elementFromPoint, which the `input-otp`
// library (used by components/ui/input-otp.jsx) polls on a timer to detect
// password-manager badges overlapping the field. Without this stub, that
// timer throws asynchronously during OTP-related tests.
if (typeof document !== 'undefined' && typeof document.elementFromPoint !== 'function') {
  document.elementFromPoint = () => null;
}
