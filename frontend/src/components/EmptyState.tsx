import { LucideIcon } from 'lucide-react';
import Link from 'next/link';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="card text-center py-12">
      <Icon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-gray-600 mb-6">{description}</p>
      {actionLabel && (
        <>
          {actionHref ? (
            <Link href={actionHref} className="btn btn-primary">
              {actionLabel}
            </Link>
          ) : (
            <button onClick={onAction} className="btn btn-primary">
              {actionLabel}
            </button>
          )}
        </>
      )}
    </div>
  );
}
