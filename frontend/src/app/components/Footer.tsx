import { AlertCircle } from 'lucide-react';

export function Footer() {
  return (
    <div className="border-t border-border bg-amber-50/50 px-6 py-3">
      <div className="flex items-center gap-2 text-sm text-amber-800">
        <AlertCircle className="w-4 h-4 shrink-0" />
        <span>
          This is not legal advice. For professional help, consult a lawyer.
        </span>
      </div>
    </div>
  );
}
