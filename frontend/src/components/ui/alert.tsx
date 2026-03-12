import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  CheckCircle,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";

type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertProps {
  children: ReactNode;
  variant?: AlertVariant;
  title?: string;
  onClose?: () => void;
  className?: string;
}

const variantStyles: Record<AlertVariant, string> = {
  info: "bg-blue-50 border-blue-200 text-blue-800",
  success: "bg-green-50 border-green-200 text-green-800",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
  error: "bg-red-50 border-red-200 text-red-800",
};

const variantIcons: Record<AlertVariant, ReactNode> = {
  info: <Info className="h-5 w-5 text-blue-500" />,
  success: <CheckCircle className="h-5 w-5 text-green-500" />,
  warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
  error: <AlertCircle className="h-5 w-5 text-red-500" />,
};

export function Alert({
  children,
  variant = "info",
  title,
  onClose,
  className,
}: AlertProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border",
        variantStyles[variant],
        className
      )}
      role="alert"
    >
      <div className="flex-shrink-0">{variantIcons[variant]}</div>
      <div className="flex-1 min-w-0">
        {title && <h4 className="font-medium mb-1">{title}</h4>}
        <div className="text-sm">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 p-1 rounded hover:bg-black/10 transition-colors"
          aria-label="Kapat"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

// Inline alert for form errors
interface InlineAlertProps {
  message: string;
  className?: string;
}

export function InlineError({ message, className }: InlineAlertProps) {
  return (
    <p className={cn("flex items-center gap-1 text-sm text-red-600", className)}>
      <AlertCircle className="h-4 w-4" />
      {message}
    </p>
  );
}

export function InlineSuccess({ message, className }: InlineAlertProps) {
  return (
    <p
      className={cn(
        "flex items-center gap-1 text-sm text-green-600",
        className
      )}
    >
      <CheckCircle className="h-4 w-4" />
      {message}
    </p>
  );
}
