import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getFees, payFee } from '../services/api';
import { CreditCard, CheckCircle, Clock, AlertTriangle, DollarSign, Receipt } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

export default function FeesPage() {
  const { user } = useAuth();
  const [fees, setFees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [paymentDialog, setPaymentDialog] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadFees();
  }, []);

  const loadFees = async () => {
    try {
      const data = await getFees();
      setFees(data);
    } catch (error) {
      console.error('Failed to load fees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!paymentAmount || parseFloat(paymentAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    
    setProcessing(true);
    try {
      await payFee(paymentDialog.id, parseFloat(paymentAmount));
      toast.success('Payment processed successfully!');
      setPaymentDialog(null);
      setPaymentAmount('');
      loadFees();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Payment failed');
    } finally {
      setProcessing(false);
    }
  };

  const getStatusStyles = (status) => {
    switch (status) {
      case 'paid':
        return { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/30' };
      case 'pending':
        return { icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/30' };
      case 'overdue':
        return { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' };
      case 'partial':
        return { icon: DollarSign, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30' };
      default:
        return { icon: Clock, color: 'text-zinc-400', bg: 'bg-zinc-500/20', border: 'border-zinc-500/30' };
    }
  };

  const calculateTotals = () => {
    const total = fees.reduce((sum, f) => sum + f.amount, 0);
    const paid = fees.reduce((sum, f) => sum + (f.paid_amount || 0), 0);
    const pending = total - paid;
    return { total, paid, pending };
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  const totals = calculateTotals();

  return (
    <DashboardLayout>
      <Header 
        title="Fees & Payments"
        subtitle="Manage your fee payments"
      />
      
      <div className="p-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Total Fees</p>
                <h3 className="text-3xl font-bold mt-2">${totals.total.toLocaleString()}</h3>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Receipt className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Paid</p>
                <h3 className="text-3xl font-bold mt-2 text-emerald-400">${totals.paid.toLocaleString()}</h3>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Outstanding</p>
                <h3 className="text-3xl font-bold mt-2 text-amber-400">${totals.pending.toLocaleString()}</h3>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/20">
                <Clock className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </div>
        </div>
        
        {/* Progress */}
        <div className="glass-card p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Payment Progress</h3>
            <span className="text-sm text-zinc-500">
              {totals.total > 0 ? ((totals.paid / totals.total) * 100).toFixed(0) : 0}% Complete
            </span>
          </div>
          <Progress 
            value={totals.total > 0 ? (totals.paid / totals.total) * 100 : 0} 
            className="h-3 bg-zinc-800" 
          />
        </div>
        
        {/* Fee List */}
        {fees.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <CreditCard className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No fees found</h3>
            <p className="text-zinc-500">Your fee records will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {fees.map((fee, index) => {
              const status = getStatusStyles(fee.status);
              const StatusIcon = status.icon;
              const remaining = fee.amount - (fee.paid_amount || 0);
              const progress = ((fee.paid_amount || 0) / fee.amount) * 100;
              
              return (
                <div
                  key={fee.id}
                  className={`glass-card p-6 animate-fadeIn stagger-${(index % 5) + 1}`}
                  data-testid={`fee-card-${fee.id}`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl ${status.bg}`}>
                        <StatusIcon className={`w-6 h-6 ${status.color}`} />
                      </div>
                      <div>
                        <h4 className="font-semibold text-lg">{fee.fee_type}</h4>
                        <p className="text-sm text-zinc-500 mt-1">{fee.description || 'No description'}</p>
                        <p className="text-sm text-zinc-500 mt-1">
                          Due: {new Date(fee.due_date).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-2xl font-bold">${fee.amount.toLocaleString()}</p>
                        {fee.paid_amount > 0 && fee.status !== 'paid' && (
                          <p className="text-sm text-zinc-500">
                            ${remaining.toLocaleString()} remaining
                          </p>
                        )}
                      </div>
                      
                      <Badge variant="outline" className={`${status.bg} ${status.color} ${status.border}`}>
                        {fee.status.charAt(0).toUpperCase() + fee.status.slice(1)}
                      </Badge>
                      
                      {fee.status !== 'paid' && (
                        <Button
                          onClick={() => {
                            setPaymentDialog(fee);
                            setPaymentAmount(remaining.toString());
                          }}
                          data-testid={`pay-btn-${fee.id}`}
                          className="bg-blue-500 hover:bg-blue-600"
                        >
                          Pay Now
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {fee.paid_amount > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/5">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-zinc-500">Payment Progress</span>
                        <span className="text-blue-400">{progress.toFixed(0)}%</span>
                      </div>
                      <Progress value={progress} className="h-2 bg-zinc-800" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        
        {/* Payment Dialog */}
        <Dialog open={!!paymentDialog} onOpenChange={() => setPaymentDialog(null)}>
          <DialogContent className="bg-zinc-900 border-white/10">
            <DialogHeader>
              <DialogTitle>Make Payment</DialogTitle>
              <DialogDescription className="text-zinc-500">
                Enter the amount you want to pay for {paymentDialog?.fee_type}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                <div className="flex justify-between mb-2">
                  <span className="text-zinc-500">Total Amount</span>
                  <span className="font-semibold">${paymentDialog?.amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Remaining</span>
                  <span className="font-semibold text-amber-400">
                    ${((paymentDialog?.amount || 0) - (paymentDialog?.paid_amount || 0)).toLocaleString()}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Payment Amount</Label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="number"
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(e.target.value)}
                    data-testid="payment-amount-input"
                    className="pl-11 bg-zinc-800 border-white/10 h-12"
                    placeholder="0.00"
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="ghost" onClick={() => setPaymentDialog(null)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handlePayment} 
                  disabled={processing}
                  data-testid="confirm-payment-btn"
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  {processing ? 'Processing...' : 'Confirm Payment'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
