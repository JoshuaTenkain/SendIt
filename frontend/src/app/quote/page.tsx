'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Package, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

export default function QuotePage() {
  const router = useRouter();
  const [addresses, setAddresses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [quoteResult, setQuoteResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    pickup_address_id: '',
    delivery_address_id: '',
    weight_kg: '',
    length_cm: '',
    width_cm: '',
    height_cm: '',
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadAddresses();
  }, [router]);

  const loadAddresses = async () => {
    try {
      const data = await api.addresses.list();
      setAddresses(data);
    } catch (err) {
      console.error('Failed to load addresses', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        pickup_address_id: formData.pickup_address_id,
        delivery_address_id: formData.delivery_address_id,
        parcel: {
          weight_kg: parseFloat(formData.weight_kg),
          length_cm: parseFloat(formData.length_cm),
          width_cm: parseFloat(formData.width_cm),
          height_cm: parseFloat(formData.height_cm),
        },
      };

      const result = await api.quotes.create(payload);
      setQuoteResult(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate quote');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBooking = async (quote: any) => {
    try {
      const idempotencyKey = `${Date.now()}-${Math.random()}`;
      const booking = await api.bookings.create(
        {
          quote_id: quoteResult.id,
          courier_id: quote.courier_id,
          courier_service_level: quote.service_level,
        },
        idempotencyKey
      );
      router.push(`/bookings/${booking.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create booking');
    }
  };

  if (quoteResult) {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <Link href="/dashboard" className="flex items-center gap-2">
                <Package className="h-8 w-8 text-primary-600" />
                <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
              </Link>
            </div>
          </div>
        </nav>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button onClick={() => setQuoteResult(null)} className="flex items-center gap-2 text-primary-600 mb-6">
            <ArrowLeft className="h-4 w-4" />
            New Quote
          </button>

          <h1 className="text-3xl font-bold mb-8">Quote Results</h1>

          {quoteResult.results?.quotes?.length === 0 ? (
            <div className="card text-center py-12">
              <p className="text-gray-600">No quotes available for this route</p>
            </div>
          ) : (
            <div className="space-y-4">
              {quoteResult.results?.quotes?.map((quote: any, index: number) => (
                <div key={index} className="card hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-xl font-semibold">{quote.courier_name}</h3>
                      <p className="text-gray-600 text-sm mt-1">
                        Service: {quote.service_level}
                      </p>
                      <p className="text-gray-600 text-sm">
                        Delivery: {quote.estimated_delivery_days} days
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-primary-600">
                        R {parseFloat(quote.price_total).toFixed(2)}
                      </p>
                      <button
                        onClick={() => handleCreateBooking(quote)}
                        className="btn btn-primary mt-4"
                      >
                        Book Now
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Get a Quote</h1>

        {addresses.length === 0 && (
          <div className="card mb-6 bg-yellow-50 border-yellow-200">
            <p className="text-yellow-800">
              You need to add addresses before getting a quote.{' '}
              <Link href="/addresses" className="text-primary-600 underline">
                Add addresses
              </Link>
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="card">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {error}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Pickup Address</label>
              <select
                required
                value={formData.pickup_address_id}
                onChange={(e) => setFormData({ ...formData, pickup_address_id: e.target.value })}
                className="input"
              >
                <option value="">Select pickup address</option>
                {addresses.map((addr) => (
                  <option key={addr.id} value={addr.id}>
                    {addr.label || `${addr.line1}, ${addr.city}`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Delivery Address</label>
              <select
                required
                value={formData.delivery_address_id}
                onChange={(e) => setFormData({ ...formData, delivery_address_id: e.target.value })}
                className="input"
              >
                <option value="">Select delivery address</option>
                {addresses.map((addr) => (
                  <option key={addr.id} value={addr.id}>
                    {addr.label || `${addr.line1}, ${addr.city}`}
                  </option>
                ))}
              </select>
            </div>

            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">Parcel Details</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={formData.weight_kg}
                    onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
                    className="input"
                    placeholder="5.0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Length (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={formData.length_cm}
                    onChange={(e) => setFormData({ ...formData, length_cm: e.target.value })}
                    className="input"
                    placeholder="30"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Width (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={formData.width_cm}
                    onChange={(e) => setFormData({ ...formData, width_cm: e.target.value })}
                    className="input"
                    placeholder="20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Height (cm)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={formData.height_cm}
                    onChange={(e) => setFormData({ ...formData, height_cm: e.target.value })}
                    className="input"
                    placeholder="10"
                  />
                </div>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary w-full">
              {loading ? 'Getting Quotes...' : 'Get Quote'}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
