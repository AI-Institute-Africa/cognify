import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import AssessmentBlockedMessage from '../AssessmentBlockedMessage';

describe('AssessmentBlockedMessage', () => {
  it('clearly states the exact dollar amount required to restore access', () => {
    render(<AssessmentBlockedMessage amountRequired={42.5} />);
    const amountBlock = screen.getByTestId('assessment-blocked-amount');
    expect(amountBlock).toHaveTextContent('$42.50');
  });

  it('formats whole-dollar amounts with two decimal places', () => {
    render(<AssessmentBlockedMessage amountRequired={20} />);
    expect(screen.getByTestId('assessment-blocked-amount')).toHaveTextContent('$20.00');
  });

  it('shows a fallback explanation when no amount is provided', () => {
    render(<AssessmentBlockedMessage />);
    expect(screen.queryByTestId('assessment-blocked-amount')).not.toBeInTheDocument();
    expect(screen.getByText(/contact your organization administrator/i)).toBeInTheDocument();
  });

  it('renders a custom message when provided', () => {
    render(<AssessmentBlockedMessage amountRequired={15} message="Pay $15 to unlock your exam." />);
    expect(screen.getByText('Pay $15 to unlock your exam.')).toBeInTheDocument();
  });

  it('invokes onPayNow when the pay button is clicked', async () => {
    const user = userEvent.setup();
    const onPayNow = jest.fn();
    render(<AssessmentBlockedMessage amountRequired={10} onPayNow={onPayNow} />);
    await user.click(screen.getByTestId('assessment-blocked-pay-btn'));
    expect(onPayNow).toHaveBeenCalledTimes(1);
  });

  it('does not render a pay button when onPayNow is not provided', () => {
    render(<AssessmentBlockedMessage amountRequired={10} />);
    expect(screen.queryByTestId('assessment-blocked-pay-btn')).not.toBeInTheDocument();
  });
});
