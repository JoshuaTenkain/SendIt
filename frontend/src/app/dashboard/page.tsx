'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Package, Plus, TruckIcon, MapPin, Settings, LogOut } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, removeToken } from '@/lib/auth';

export default function DashboardPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [bookingsData] = await Promise.all([
        api.bookings.list(),
      ]);
      setBookings(bookingsData);
    } catch (error) {
      console.error('Failed to load data', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    removeToken();
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/addresses" className="text-gray-600 hover:text-gray-900 flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                <span className="hidden sm:inline">Addresses</span>
              </Link>
              <Link href="/quote" className="btn btn-primary">
                <Plus className="h-4 w-4 inline mr-2" />
                New Quote
              </Link>
              <button onClick={handleLogout} className="btn btn-secondary flex items-center gap-2">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">My Bookings</h1>

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : bookings.length === 0 ? (
          <div className="card text-center py-12">
            <TruckIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No bookings yet</h2>
            <p className="text-gray-600 mb-6">Get started by creating your first quote</p>
            <Link href="/quote" className="btn btn-primary">
              Create Quote
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {bookings.map((booking: any) => (
              <div key={booking.id} className="card hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-gray-500">
                        Booking #{booking.id.slice(0, 8)}
                      </span>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          booking.status === 'paid'
                            ? 'bg-green-100 text-green-800'
                            : booking.status === 'pending_payment'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {booking.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mb-1">
                      Service: {booking.courier_service_level}
                    </p>
                    {booking.tracking_reference && (
                      <p className="text-gray-600 text-sm">
                        Tracking: {booking.tracking_reference}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary-600">
                      R {parseFloat(booking.price_total).toFixed(2)}
                    </p>
                    <Link
                      href={`/bookings/${booking.id}`}
                      className="text-sm text-primary-600 hover:text-primary-700 mt-2 inline-block"
                    >
                      View Details →
                    </Link>
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
