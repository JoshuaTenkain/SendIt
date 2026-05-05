'use client';

import { useState } from 'react';
import { Package, TruckIcon, DollarSign, Clock } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [code, setCode] = useState('');
  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <Package className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-primary-600">SEND-IT</span>
            </div>
            <div className="flex gap-4">
              <Link href="/login" className="btn btn-secondary">
                Login
              </Link>
              <Link href="/signup" className="btn btn-primary">
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <section className="bg-gradient-to-b from-primary-50 to-white py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Compare. Book. Ship.
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get instant quotes from multiple courier providers and choose the best option for your shipment.
            </p>
            <Link href="/get-quote" className="btn btn-primary text-lg px-8 py-3">
              Get a Quote — no sign up
            </Link>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const c = code.trim().toUpperCase();
                if (c) router.push(`/track/${c}`);
              }}
              className="mt-8 flex gap-2 max-w-md mx-auto"
            >
              <input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Track a shipment — e.g. ABC123DEF456"
                className="input flex-1"
              />
              <button type="submit" className="btn btn-secondary">Track</button>
            </form>
          </div>
        </section>

        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
            <div className="grid md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Package className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Enter Details</h3>
                <p className="text-gray-600 text-sm">Provide parcel and address information</p>
              </div>
              <div className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <DollarSign className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Compare Quotes</h3>
                <p className="text-gray-600 text-sm">See prices from multiple couriers</p>
              </div>
              <div className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TruckIcon className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Book & Pay</h3>
                <p className="text-gray-600 text-sm">Secure online payment</p>
              </div>
              <div className="text-center">
                <div className="bg-primary-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Clock className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="font-semibold mb-2">Track Shipment</h3>
                <p className="text-gray-600 text-sm">Real-time tracking updates</p>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-gray-100 py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to ship?</h2>
            <p className="text-gray-600 mb-8">Get started with your first quote today</p>
            <Link href="/signup" className="btn btn-primary text-lg px-8 py-3">
              Create Account
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2026 SEND-IT. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
