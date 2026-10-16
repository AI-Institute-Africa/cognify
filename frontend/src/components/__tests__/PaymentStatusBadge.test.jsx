import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import PaymentStatusBadge, { PAYMENT_STATUS_LABELS } from '../PaymentStatusBadge';

describe('PaymentStatusBadge', () => {
  it('renders all 6 payment_status values with their expected labels', () => {
    Object.entries(PAYMENT_STATUS_LABELS).forEach(([status, label]) => {
      const { unmount } = render(<PaymentStatusBadge status={status} />);
      expect(screen.getByTestId(`payment-status-badge-${status}`)).toHaveTextContent(label);
      unmount();
    });
  });

  it('is case-insensitive and tolerant of hyphens/spaces', () => {
    render(<PaymentStatusBadge status="Partially-Paid" />);
    expect(screen.getByTestId('payment-status-badge-partially_paid')).toHaveTextContent('Partially Paid');
  });

  it('falls back to "Unpaid" for an unknown/missing status', () => {
    render(<PaymentStatusBadge status="not_a_real_status" />);
    expect(screen.getByTestId('payment-status-badge-unpaid')).toHaveTextContent('Unpaid');

    const { container } = render(<PaymentStatusBadge />);
    expect(container).toHaveTextContent('Unpaid');
  });

  it('gives distinct, non-overlapping color classes for overdue vs current', () => {
    render(<PaymentStatusBadge status="overdue" />);
    render(<PaymentStatusBadge status="current" />);
    const overdue = screen.getByTestId('payment-status-badge-overdue');
    const current = screen.getByTestId('payment-status-badge-current');
    expect(overdue.className).not.toEqual(current.className);
    expect(overdue.className).toMatch(/rose/);
    expect(current.className).toMatch(/emerald/);
  });
});
