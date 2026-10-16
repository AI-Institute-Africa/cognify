import * as React from "react";
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils";
import { Badge } from "./ui/badge";

// The 6 payment_status values returned by the backend enrollment/payment
// endpoints (BRD section 15 reporting + section 11 UX requirements).
// Keys are normalized to lower_snake_case to match the API contract.
export const PAYMENT_STATUS_LABELS = {
  unpaid: "Unpaid",
  current: "Current",
  partially_paid: "Partially Paid",
  payment_due: "Payment Due",
  overdue: "Overdue",
  completed: "Completed",
};

// Distinct, semantically-meaningful colors for each status so admins can
// scan a table and immediately see who needs attention (overdue/due) vs
// who is fine (current/completed).
const paymentStatusBadgeVariants = cva(
  "capitalize whitespace-nowrap",
  {
    variants: {
      status: {
        unpaid: "border-transparent bg-zinc-500/20 text-zinc-300",
        current: "border-transparent bg-emerald-500/20 text-emerald-300",
        partially_paid: "border-transparent bg-blue-500/20 text-blue-300",
        payment_due: "border-transparent bg-amber-500/20 text-amber-300",
        overdue: "border-transparent bg-rose-500/20 text-rose-300",
        completed: "border-transparent bg-violet-500/20 text-violet-300",
      },
    },
    defaultVariants: {
      status: "unpaid",
    },
  }
);

function normalizeStatus(status) {
  if (!status) return "unpaid";
  const key = String(status).toLowerCase().trim().replace(/[\s-]+/g, "_");
  return PAYMENT_STATUS_LABELS[key] ? key : "unpaid";
}

/**
 * Reusable payment status badge for enrollment payment_status values:
 * unpaid | current | partially_paid | payment_due | overdue | completed
 */
function PaymentStatusBadge({ status, className, ...props }) {
  const key = normalizeStatus(status);
  return (
    <Badge
      data-testid={`payment-status-badge-${key}`}
      className={cn(paymentStatusBadgeVariants({ status: key }), className)}
      {...props}
    >
      {PAYMENT_STATUS_LABELS[key]}
    </Badge>
  );
}

export { PaymentStatusBadge, paymentStatusBadgeVariants };
export default PaymentStatusBadge;
