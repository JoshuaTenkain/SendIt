'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function PaymentNotifyPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard after a short delay
    const timer = setTimeout(() => {
      router.push('/dashboard');
    }, 2000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="card max-w-md text-center">
        <div className="flex justify-center mb-6">
          <Loader2 className="h-20 w-20 text-primary-600 animate-spin" />
        </div>
        
        <h1 className="text-2xl font-bold mb-4">Processing Payment...</h1>
        
        <p className="text-gray-700">
          Please wait while we confirm your payment.
        </p>
      </div>
    </div>
  );
}
