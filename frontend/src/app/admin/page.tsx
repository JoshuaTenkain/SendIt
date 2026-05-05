'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Package, Users, TruckIcon, DollarSign, Settings } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, removeToken } from '@/lib/auth';

export default function AdminPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('overview');
  const [couriers, setCouriers] = useState<any[]>([]);
  const [bookings, setBookings] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [couriersData, bookingsData, transactionsData, revenueData] = await Promise.all([
        api.admin.getCouriers(),
        api.admin.getBookings(),
        api.admin.getTransactions(),
        api.admin.getRevenue(),
      ]);
      setCouriers(couriersData);
      setBookings(bookingsData);
      setTransactions(transactionsData);
      setRevenue(revenueData);
    } catch (err: any) {
      if (err.message.includes('403')) {
        setError('Access denied. Admin privileges required.');
      } else {
        setError(err.message || 'Failed to load admin data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCourier = async (courierId: string, isEnabled: boolean) => {
    try {
      await api.admin.updateCourier(courierId, { is_enabled: !isEnabled });
      loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to update courier');
    }
  };

  const handleLogout = () => {
    removeToken();
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl">Loading admin dashboard...</div>
        </div>
      </div>
    );
  }

  if (error && error.includes('Access denied')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="card max-w-md text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
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
            <Link href="/admin" className="flex items-center gap-2">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-primary-600">SEND-IT Admin</span>
            </Link>
            <div className="flex gap-4">
              <Link href="/dashboard" className="btn btn-secondary">
                User Dashboard
              </Link>
              <button onClick={handleLogout} className="btn btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

        {error && !error.includes('Access denied') && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {/* Stats Overview */}
        {revenue && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="card">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary-100 rounded-lg">
                  <DollarSign className="h-6 w-6 text-primary-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Revenue</p>
                  <p className="text-2xl font-bold">R {parseFloat(revenue.total_revenue || 0).toFixed(2)}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Commission</p>
                  <p className="text-2xl font-bold">R {parseFloat(revenue.total_commission || 0).toFixed(2)}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Package className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Bookings</p>
                  <p className="text-2xl font-bold">{revenue.booking_count || 0}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <TruckIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Couriers</p>
                  <p className="text-2xl font-bold">{couriers.filter((c) => c.is_enabled).length}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex gap-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('couriers')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'couriers'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Couriers
            </button>
            <button
              onClick={() => setActiveTab('bookings')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'bookings'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Bookings
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'transactions'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Transactions
            </button>
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Recent Bookings</h2>
              {bookings.slice(0, 5).length === 0 ? (
                <p className="text-gray-600">No bookings yet</p>
              ) : (
                <div className="space-y-3">
                  {bookings.slice(0, 5).map((booking: any) => (
                    <div key={booking.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium">#{booking.id.slice(0, 8)}</p>
                        <p className="text-sm text-gray-600">{booking.courier_service_level}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">R {parseFloat(booking.price_total).toFixed(2)}</p>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            booking.status === 'paid'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {booking.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Courier Status</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {couriers.map((courier: any) => (
                  <div key={courier.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <p className="font-medium">{courier.name}</p>
                      <p className="text-sm text-gray-600">Commission: {courier.commission_pct}%</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        courier.is_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {courier.is_enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Couriers Tab */}
        {activeTab === 'couriers' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Manage Couriers</h2>
            <div className="space-y-4">
              {couriers.map((courier: any) => (
                <div key={courier.id} className="flex justify-between items-start p-4 border rounded-lg">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{courier.name}</h3>
                    <p className="text-sm text-gray-600 mb-2">Code: {courier.code}</p>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Base Markup:</span>
                        <span className="ml-2 font-medium">{courier.base_markup_pct}%</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Commission:</span>
                        <span className="ml-2 font-medium">{courier.commission_pct}%</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Rating:</span>
                        <span className="ml-2 font-medium">{courier.rating}/5</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggleCourier(courier.id, courier.is_enabled)}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      courier.is_enabled
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {courier.is_enabled ? 'Disable' : 'Enable'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bookings Tab */}
        {activeTab === 'bookings' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">All Bookings</h2>
            {bookings.length === 0 ? (
              <p className="text-gray-600">No bookings yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4">ID</th>
                      <th className="text-left py-3 px-4">Service</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">Price</th>
                      <th className="text-left py-3 px-4">Commission</th>
                      <th className="text-left py-3 px-4">Tracking</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map((booking: any) => (
                      <tr key={booking.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 font-mono text-sm">{booking.id.slice(0, 8)}</td>
                        <td className="py-3 px-4">{booking.courier_service_level}</td>
                        <td className="py-3 px-4">
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
                        </td>
                        <td className="py-3 px-4">R {parseFloat(booking.price_total).toFixed(2)}</td>
                        <td className="py-3 px-4">R {parseFloat(booking.commission_amount || 0).toFixed(2)}</td>
                        <td className="py-3 px-4 font-mono text-sm">{booking.tracking_reference || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Transactions Tab */}
        {activeTab === 'transactions' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">All Transactions</h2>
            {transactions.length === 0 ? (
              <p className="text-gray-600">No transactions yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4">ID</th>
                      <th className="text-left py-3 px-4">Booking</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">Amount</th>
                      <th className="text-left py-3 px-4">Gateway</th>
                      <th className="text-left py-3 px-4">Reference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((txn: any) => (
                      <tr key={txn.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 font-mono text-sm">{txn.id.slice(0, 8)}</td>
                        <td className="py-3 px-4 font-mono text-sm">{txn.booking_id.slice(0, 8)}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              txn.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : txn.status === 'pending'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {txn.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">R {parseFloat(txn.amount).toFixed(2)}</td>
                        <td className="py-3 px-4">{txn.payment_gateway}</td>
                        <td className="py-3 px-4 font-mono text-sm">{txn.gateway_reference || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
