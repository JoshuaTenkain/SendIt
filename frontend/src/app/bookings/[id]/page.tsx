'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Package, ArrowLeft, CreditCard, MapPin, Calendar, TruckIcon } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated } from '@/lib/auth';

export default function BookingDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<any>(null);
  const [tracking, setTracking] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [paymentLoading, setPaymentLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadBooking();
  }, [bookingId, router]);

  const loadBooking = async () => {
    try {
      const [bookingData, trackingData] = await Promise.all([
        api.bookings.get(bookingId),
        api.tracking.get(bookingId).catch(() => []),
      ]);
      setBooking(bookingData);
      setTracking(trackingData);
    } catch (err: any) {
      setError(err.message || 'Failed to load booking');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    setPaymentLoading(true);
    try {
      const paymentData = await api.bookings.initiatePayment(bookingId);
      
      // Redirect to PayFast payment page
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = paymentData.payment_url;
      
      Object.keys(paymentData.payment_data).forEach((key) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = paymentData.payment_data[key];
        form.appendChild(input);
      });
      
      document.body.appendChild(form);
      form.submit();
    } catch (err: any) {
      setError(err.message || 'Failed to initiate payment');
      setPaymentLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl">Loading booking details...</div>
        </div>
      </div>
    );
  }

  if (error && !booking) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="card max-w-md text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-700 mb-6">{error}</p>
          <Link href="/dashboard" className="btn btn-primary">
            Back to Dashboard
          </Link>
        </div>
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

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link href="/dashboard" className="flex items-center gap-2 text-primary-600 mb-6">
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>

        <h1 className="text-3xl font-bold mb-8">Booking Details</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {/* Status Banner */}
        <div className={`card mb-6 ${
          booking.status === 'paid' ? 'bg-green-50 border-green-200' :
          booking.status === 'pending_payment' ? 'bg-yellow-50 border-yellow-200' :
          'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold mb-2">
                Status: <span className="capitalize">{booking.status.replace('_', ' ')}</span>
              </h2>
              <p className="text-gray-700">
                {booking.status === 'pending_payment' && 'Payment required to complete your booking'}
                {booking.status === 'paid' && 'Payment confirmed - shipment will be created soon'}
                {booking.status === 'in_transit' && 'Your parcel is on its way'}
                {booking.status === 'delivered' && 'Your parcel has been delivered'}
              </p>
            </div>
            {booking.status === 'pending_payment' && (
              <button
                onClick={handlePayment}
                disabled={paymentLoading}
                className="btn btn-primary flex items-center gap-2"
              >
                <CreditCard className="h-4 w-4" />
                {paymentLoading ? 'Processing...' : 'Pay Now'}
              </button>
            )}
          </div>
        </div>

        {/* Booking Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Package className="h-5 w-5" />
              Booking Information
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Booking ID</p>
                <p className="font-mono text-sm">{booking.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Service Level</p>
                <p className="font-medium">{booking.courier_service_level}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Tracking Reference</p>
                <p className="font-mono text-sm">{booking.tracking_reference || 'Not available yet'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Created</p>
                <p className="text-sm">{new Date(booking.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Pricing
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Base Price</span>
                <span className="font-medium">R {parseFloat(booking.price_base).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">VAT</span>
                <span className="font-medium">R {parseFloat(booking.price_vat).toFixed(2)}</span>
              </div>
              <div className="border-t pt-3 flex justify-between">
                <span className="font-semibold">Total</span>
                <span className="text-2xl font-bold text-primary-600">
                  R {parseFloat(booking.price_total).toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tracking Information */}
        {tracking.length > 0 && (
          <div className="card mb-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TruckIcon className="h-5 w-5" />
              Tracking History
            </h3>
            <div className="space-y-4">
              {tracking.map((event: any, index: number) => (
                <div key={event.id} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${
                      index === 0 ? 'bg-primary-600' : 'bg-gray-300'
                    }`} />
                    {index < tracking.length - 1 && (
                      <div className="w-0.5 h-full bg-gray-300 my-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className="font-medium">{event.status}</p>
                    <p className="text-sm text-gray-600">{event.location || 'Unknown location'}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                    {event.description && (
                      <p className="text-sm text-gray-700 mt-1">{event.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quote Details */}
        {booking.quote && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Route Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-2">Pickup Address</p>
                <div className="text-sm">
                  <p>{booking.quote.pickup_address.line1}</p>
                  {booking.quote.pickup_address.line2 && <p>{booking.quote.pickup_address.line2}</p>}
                  <p>{booking.quote.pickup_address.city}, {booking.quote.pickup_address.postal_code}</p>
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-2">Delivery Address</p>
                <div className="text-sm">
                  <p>{booking.quote.delivery_address.line1}</p>
                  {booking.quote.delivery_address.line2 && <p>{booking.quote.delivery_address.line2}</p>}
                  <p>{booking.quote.delivery_address.city}, {booking.quote.delivery_address.postal_code}</p>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t">
              <p className="text-sm font-semibold text-gray-600 mb-2">Parcel Details</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Weight</p>
                  <p className="font-medium">{booking.quote.parcel.weight_kg} kg</p>
                </div>
                <div>
                  <p className="text-gray-600">Length</p>
                  <p className="font-medium">{booking.quote.parcel.length_cm} cm</p>
                </div>
                <div>
                  <p className="text-gray-600">Width</p>
                  <p className="font-medium">{booking.quote.parcel.width_cm} cm</p>
                </div>
                <div>
                  <p className="text-gray-600">Height</p>
                  <p className="font-medium">{booking.quote.parcel.height_cm} cm</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
