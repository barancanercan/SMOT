import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  description?: string;
  className?: string;
}

export function MetricCard({
  title,
  value,
  icon,
  description,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-gray-200 p-6 shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {description && (
            <p className="text-sm text-gray-400 mt-1">{description}</p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-blue-50 rounded-lg text-blue-600">{icon}</div>
        )}
      </div>
    </div>
  );
}
