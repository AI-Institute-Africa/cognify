import * as React from "react";
import { Lock, CreditCard } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";

function formatAmount(amount) {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (typeof num !== "number" || Number.isNaN(num)) return null;
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Shown when assignment/exam (or other gated) access is blocked due to an
 * unpaid minimum-monthly-payment balance.
 *
 * BRD 11: "the message shall clearly state the amount required to restore
 * access" — this component always renders the dollar figure prominently
 * (not buried in body copy) whenever `amountRequired` is provided.
 */
export default function AssessmentBlockedMessage({
  amountRequired,
  message,
  coursePrice,
  onPayNow,
  payLabel = "Make a Payment",
  className,
}) {
  const formatted = formatAmount(amountRequired);

  return (
    <Card
      className={cn("border-amber-500/30 bg-amber-500/5", className)}
      data-testid="assessment-blocked-message"
    >
      <CardContent className="p-6 flex flex-col items-center text-center gap-3">
        <div className="w-14 h-14 rounded-full bg-amber-500/15 flex items-center justify-center">
          <Lock className="w-7 h-7 text-amber-400" />
        </div>

        <h3 className="text-lg font-semibold text-amber-200">
          Assessment Access Restricted
        </h3>

        <p className="text-sm text-zinc-400 max-w-md">
          {message ||
            "This assignment or exam is locked until the required minimum payment has been made."}
        </p>

        {formatted !== null ? (
          <div
            className="mt-1 px-5 py-3 rounded-lg bg-amber-500/10 border border-amber-500/30"
            data-testid="assessment-blocked-amount"
          >
            <p className="text-[11px] text-amber-300/80 uppercase tracking-wide">
              Amount required to restore access
            </p>
            <p className="text-2xl font-bold text-amber-300">${formatted}</p>
          </div>
        ) : (
          <p className="text-xs text-zinc-600">
            Contact your organization administrator to find out how much is owed.
          </p>
        )}

        {typeof coursePrice === "number" && (
          <p className="text-xs text-zinc-600">
            Full course price: ${formatAmount(coursePrice)}
          </p>
        )}

        {onPayNow && (
          <Button
            type="button"
            onClick={onPayNow}
            className="mt-2 bg-amber-500 hover:bg-amber-600 text-black"
            data-testid="assessment-blocked-pay-btn"
          >
            <CreditCard className="w-4 h-4 mr-2" />
            {payLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
