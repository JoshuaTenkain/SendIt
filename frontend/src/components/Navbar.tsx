import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Package, Plus, MapPin, LogOut, User, Settings } from 'lucide-react';
import { removeToken } from '@/lib/auth';

interface NavbarProps {
  showActions?: boolean;
  isAdmin?: boolean;
}

export default function Navbar({ showActions = true, isAdmin = false }: NavbarProps) {
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    router.push('/');
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link href={isAdmin ? "/admin" : "/dashboard"} className="flex items-center gap-2">
            <Package className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-primary-600">
              SEND-IT {isAdmin && <span className="text-sm">Admin</span>}
            </span>
          </Link>
          
          {showActions && (
            <div className="flex items-center gap-4">
              {!isAdmin && (
                <>
                  <Link href="/addresses" className="text-gray-600 hover:text-gray-900 flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    <span className="hidden sm:inline">Addresses</span>
                  </Link>
                  <Link href="/quote" className="btn btn-primary">
                    <Plus className="h-4 w-4 inline mr-2" />
                    <span className="hidden sm:inline">New Quote</span>
                  </Link>
                </>
              )}
              
              {isAdmin && (
                <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline">User Portal</span>
                </Link>
              )}
              
              <button onClick={handleLogout} className="btn btn-secondary flex items-center gap-2">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
