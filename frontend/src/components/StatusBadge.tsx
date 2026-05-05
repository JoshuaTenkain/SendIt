interface StatusBadgeProps {
  status: string;
  type?: 'booking' | 'transaction' | 'shipment';
}

export default function StatusBadge({ status, type = 'booking' }: StatusBadgeProps) {
  const getStatusColor = () => {
    const normalizedStatus = status.toLowerCase().replace('_', ' ');
    
    if (type === 'booking') {
      switch (status) {
        case 'paid':
          return 'bg-green-100 text-green-800';
        case 'pending_payment':
          return 'bg-yellow-100 text-yellow-800';
        case 'in_transit':
          return 'bg-blue-100 text-blue-800';
        case 'delivered':
          return 'bg-purple-100 text-purple-800';
        case 'cancelled':
          return 'bg-red-100 text-red-800';
        default:
          return 'bg-gray-100 text-gray-800';
      }
    }
    
    if (type === 'transaction') {
      switch (status) {
        case 'completed':
          return 'bg-green-100 text-green-800';
        case 'pending':
          return 'bg-yellow-100 text-yellow-800';
        case 'failed':
          return 'bg-red-100 text-red-800';
        default:
          return 'bg-gray-100 text-gray-800';
      }
    }
    
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor()}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
