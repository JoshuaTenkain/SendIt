'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, Package } from 'lucide-react';

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams.get('booking_id');

  useEffect(() => {
    // Redirect to dashboard after 5 seconds
    const timer = setTimeout(() => {
      if (bookingId) {
        router.push(`/bookings/${bookingId}`);
      } else {
        router.push('/dashboard');
      }
    }, 5000);

    return () => clearTimeout(timer);
  }, [bookingId, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="card max-w-md text-center">
        <div className="flex justify-center mb-6">
          <CheckCircle className="h-20 w-20 text-green-600" />
        </div>
        
        <h1 className="text-3xl font-bold text-green-600 mb-4">Payment Successful!</h1>
        
        <p className="text-gray-700 mb-6">
          Your payment has been processed successfully. Your shipment will be created shortly.
        </p>

        {bookingId && (
          <p className="text-sm text-gray-600 mb-6">
            Booking ID: <span className="font-mono">{bookingId}</span>
          </p>
        )}

        <div className="space-y-3">
          {bookingId && (
            <Link href={`/bookings/${bookingId}`} className="btn btn-primary w-full">
              View Booking Details
            </Link>
          )}
          <Link href="/dashboard" className="btn btn-secondary w-full">
            Go to Dashboard
          </Link>
        </div>

        <p className="text-xs text-gray-500 mt-6">
          Redirecting automatically in 5 seconds...
        </p>
      </div>
    </div>
  );
}
