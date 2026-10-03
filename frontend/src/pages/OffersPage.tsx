/**
 * Offers management page.
 */

import { useState, useEffect } from 'react';
import api from '../services/api';
import type { Offer, OfferListResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import { Gift, Loader2, DollarSign, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';

export default function OffersPage() {
  const { user } = useAuth();
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOffers = async () => {
    setLoading(true);
    try {
      const { data } = await api.get<OfferListResponse>('/offers?page_size=50');
      setOffers(data.offers);
    } catch {
      setOffers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOffers(); }, []);

  const handleApprove = async (offerId: string) => {
    try {
      await api.post(`/offers/${offerId}/approve`);
      toast.success('Offer approved and sent');
      fetchOffers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const handleSend = async (offerId: string) => {
    try {
      await api.post(`/offers/${offerId}/send`);
      toast.success('Offer submitted for approval');
      fetchOffers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const handleRespond = async (offerId: string, accepted: boolean) => {
    try {
      await api.post(`/offers/${offerId}/respond`, { accepted });
      toast.success(accepted ? 'Offer accepted!' : 'Offer declined');
      fetchOffers();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Offers</h1>
        <p className="text-surface-500 mt-1">{offers.length} total</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : offers.length === 0 ? (
        <div className="text-center py-16 card">
          <Gift className="w-12 h-12 text-surface-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-surface-700">No offers yet</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {offers.map((offer) => (
            <div key={offer.id} className="card p-6 hover:border-primary-200">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-surface-900">{offer.job_title || 'Position'}</h3>
                  <p className="text-sm text-surface-500">{offer.candidate_name || 'Candidate'}</p>
                </div>
                <StatusBadge status={offer.status} />
              </div>

              {offer.compensation_details?.base_salary && (
                <div className="flex items-center gap-2 mb-4 p-3 bg-surface-50 rounded-xl">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-lg font-bold text-surface-900">
                      {formatCurrency(offer.compensation_details.base_salary)}
                    </p>
                    <p className="text-xs text-surface-500">Base Salary</p>
                  </div>
                  {offer.compensation_details.signing_bonus && (
                    <div className="ml-auto text-right">
                      <p className="text-sm font-semibold text-surface-700">
                        +{formatCurrency(offer.compensation_details.signing_bonus)}
                      </p>
                      <p className="text-xs text-surface-500">Signing Bonus</p>
                    </div>
                  )}
                </div>
              )}

              {offer.expires_at && (
                <p className="text-xs text-surface-500 mb-4">
                  Expires: {new Date(offer.expires_at).toLocaleDateString()}
                </p>
              )}

              <div className="flex gap-2">
                {user?.role !== 'candidate' && offer.status === 'draft' && (
                  <button onClick={() => handleSend(offer.id)} className="btn-primary text-xs !px-4 !py-2">
                    Submit for Approval
                  </button>
                )}
                {user?.role !== 'candidate' && offer.status === 'pending_approval' && (
                  <button onClick={() => handleApprove(offer.id)} className="btn-primary text-xs !px-4 !py-2">
                    <Check className="w-3 h-3" /> Approve & Send
                  </button>
                )}
                {user?.role === 'candidate' && offer.status === 'sent' && (
                  <>
                    <button onClick={() => handleRespond(offer.id, true)} className="btn-primary text-xs !px-4 !py-2">
                      <Check className="w-3 h-3" /> Accept
                    </button>
                    <button onClick={() => handleRespond(offer.id, false)} className="btn-danger text-xs !px-4 !py-2">
                      <X className="w-3 h-3" /> Decline
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
