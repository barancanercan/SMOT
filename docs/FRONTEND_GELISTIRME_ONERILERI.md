# Frontend Gelistirme Onerileri

> **Meclis Istihbarat Sistemi - Next.js Frontend Uzman Raporu**
>
> Tarih: Mart 2026 | Versiyon: 3.0

---

## Executive Summary

Frontend, Next.js 14 App Router ile modern bir yapidir ancak **component library yetersiz, state management tutarsiz ve error handling eksiktir**. recharts yuklu ama kullanilmiyor. Hizli bir iyilestirme ile kullanici deneyimi onemli olcude arttirilabilir.

**Mevcut Skor:** 4.5/10
**Hedef Skor:** 8/10 (6 ay sonra)

---

## Mevcut Durum Analizi

### Guclu Yanlar
| Alan | Detay | Dosya |
|------|-------|-------|
| Next.js 14 | App Router, modern mimari | - |
| React Query | Server state yonetimi | `package.json:16` |
| TypeScript | Tip guvenligi | - |
| Tailwind CSS | Utility-first styling | - |
| Lucide Icons | Tutarli ikonografi | - |

### Zayif Yanlar
| Alan | Sorun | Etki |
|------|-------|------|
| Custom Components | Sadece 2 component (Sidebar, MetricCard) | Kod tekrari |
| Error Handling | Error boundary yok | Kotu UX |
| Charts | recharts yuklu ama kullanilmiyor | 200KB bosa |
| State Management | React Query + useState karisik | Tutarsizlik |
| Accessibility | Temel a11y eksik | Erisim sorunu |

---

## Component Envanteri

### Mevcut Componentler
| Component | Dosya | Kullanim |
|-----------|-------|----------|
| `Sidebar` | `components/layout/sidebar.tsx` | Layout navigation |
| `MetricCard` | `components/features/metric-card.tsx` | Dashboard stats |

### Eksik Componentler
| Component | Aciklama | Oncelik |
|-----------|----------|---------|
| Button | Tutarli buton stilleri | P1 |
| Card | Genel kart component'i | P1 |
| Table | Veri tablosu | P1 |
| Modal | Dialog/popup | P1 |
| Toast | Bildirimler | P0 |
| Skeleton | Loading placeholders | P1 |
| ErrorBoundary | Hata yakalama | P0 |
| Select | Styled dropdown | P2 |
| Input | Form input | P2 |
| Badge | Status etiketleri | P2 |

---

## P0: Kritik Oncelik (Hemen Yapilmali)

### 1. React Query Standardizasyonu

**Problem:** Bazi sayfalar React Query, bazi sayfalar `useState + useEffect` kullaniyor.

**Dosya:** `frontend/src/app/reports/page.tsx:27-49` - useState kullanimi

**Mevcut (Tutarsiz):**
```tsx
// reports/page.tsx - useState kullanilmis
const [users, setUsers] = useState<User[]>([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
    fetchUsers();
}, []);

const fetchUsers = async () => {
    const data = await api.get<User[]>("/users");
    setUsers(data);
};
```

**Duzeltilmis (React Query):**
```tsx
// reports/page.tsx - React Query ile
import { useQuery, useMutation } from "@tanstack/react-query";

export default function ReportsPage() {
    const { data: users, isLoading, error } = useQuery({
        queryKey: ["users"],
        queryFn: () => api.get<User[]>("/users"),
    });

    const generateReportMutation = useMutation({
        mutationFn: (data: GenerateReportRequest) =>
            api.post<{ content: string }>("/reports/generate", data),
        onSuccess: (data) => {
            setReport(data.content);
        },
        onError: (error) => {
            setError("Rapor olusturulamadi");
        },
    });

    // Butun sayfalarda ayni pattern
}
```

**Tum Sayfalarda Uygula:**
- `page.tsx` (Dashboard) - OK, React Query kullaniyor
- `reports/page.tsx` - Guncellenmeli
- `analytics/page.tsx` - Kontrol edilmeli
- `tweets/page.tsx` - Kontrol edilmeli

**Effort:** Medium | **Impact:** High

---

### 2. Error Boundaries

**Problem:** Herhangi bir component hata firlatirsa tum uygulama coker.

**Cozum:**
```tsx
// components/error-boundary.tsx (yeni dosya)
"use client";

import { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("Error caught by boundary:", error, errorInfo);
        // Sentry/LogRocket'a gonder
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback || (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                    <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                        Bir hata olustu
                    </h2>
                    <p className="text-gray-500 mb-4">
                        {this.state.error?.message || "Beklenmeyen bir hata"}
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Sayfayi Yenile
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
```

**Layout'a Ekle:**
```tsx
// app/layout.tsx
import { ErrorBoundary } from "@/components/error-boundary";

export default function RootLayout({ children }) {
    return (
        <html lang="tr">
            <body>
                <ErrorBoundary>
                    <Providers>
                        {children}
                    </Providers>
                </ErrorBoundary>
            </body>
        </html>
    );
}
```

**Effort:** Low | **Impact:** Critical

---

## P1: Yuksek Oncelik (30 Gun Icinde)

### 3. Component Library (15+ Component)

**Hedef:** Tutarli, yeniden kullanilabilir UI componentleri.

**Dizin Yapisi:**
```
frontend/src/components/
├── ui/
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── select.tsx
│   ├── table.tsx
│   ├── modal.tsx
│   ├── toast.tsx
│   ├── skeleton.tsx
│   ├── badge.tsx
│   ├── tabs.tsx
│   ├── dropdown.tsx
│   ├── avatar.tsx
│   ├── progress.tsx
│   ├── alert.tsx
│   └── tooltip.tsx
├── layout/
│   ├── sidebar.tsx
│   ├── header.tsx
│   └── page-wrapper.tsx
├── features/
│   ├── metric-card.tsx
│   ├── user-card.tsx
│   ├── tweet-card.tsx
│   └── report-viewer.tsx
└── error-boundary.tsx
```

**Button Component Ornegi:**
```tsx
// components/ui/button.tsx
import { forwardRef, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
    loading?: boolean;
}

const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50",
    ghost: "text-gray-700 hover:bg-gray-100",
    danger: "bg-red-600 text-white hover:bg-red-700",
};

const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => {
        return (
            <button
                ref={ref}
                disabled={disabled || loading}
                className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors",
                    "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    variantStyles[variant],
                    sizeStyles[size],
                    className
                )}
                {...props}
            >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {children}
            </button>
        );
    }
);
Button.displayName = "Button";
```

**Effort:** High | **Impact:** High

---

### 4. API Client Iyilestirmesi

**Problem:** Hata yonetimi yetersiz, tip guvenligi zayif.

**Dosya:** `frontend/src/lib/api.ts`

**Mevcut Kod:**
```tsx
async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(...);
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
}
```

**Iyilestirilmis Kod:**
```tsx
// lib/api.ts
export interface ApiError {
    status: number;
    message: string;
    details?: Record<string, unknown>;
}

export class ApiException extends Error {
    constructor(
        public readonly status: number,
        message: string,
        public readonly details?: Record<string, unknown>
    ) {
        super(message);
        this.name = "ApiException";
    }
}

class ApiClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = API_BASE_URL + API_PREFIX;
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            let errorMessage = `HTTP Error ${response.status}`;
            let details: Record<string, unknown> | undefined;

            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
                details = errorData;
            } catch {
                // JSON parse hatasi, default mesaj kullan
            }

            throw new ApiException(response.status, errorMessage, details);
        }

        // 204 No Content
        if (response.status === 204) {
            return undefined as T;
        }

        return response.json();
    }

    async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                ...this.getAuthHeaders(),
            },
            ...options,
        });

        return this.handleResponse<T>(response);
    }

    async post<T>(endpoint: string, data: unknown): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...this.getAuthHeaders(),
            },
            body: JSON.stringify(data),
        });

        return this.handleResponse<T>(response);
    }

    private getAuthHeaders(): Record<string, string> {
        const token = localStorage.getItem("auth_token");
        return token ? { Authorization: `Bearer ${token}` } : {};
    }
}

export const api = new ApiClient();
```

**Effort:** Low | **Impact:** Medium

---

### 5. Accessibility (A11y)

**Problem:** Temel erisebilirlik standartlari karsilanmiyor.

**Kontrol Listesi:**
| Alan | Durum | Duzeltme |
|------|-------|----------|
| Semantic HTML | [ ] | `div` yerine `button`, `nav`, `main` |
| Keyboard Navigation | [ ] | tabIndex, focus management |
| ARIA Labels | [ ] | aria-label, aria-describedby |
| Color Contrast | [ ] | 4.5:1 minimum oran |
| Focus Indicators | [ ] | focus-visible ring |
| Screen Reader | [ ] | sr-only sinifi |

**Ornek Duzeltmeler:**

```tsx
// Mevcut (Kotu)
<div onClick={handleClick}>Click me</div>

// Duzeltilmis
<button
    onClick={handleClick}
    aria-label="Rapor olustur"
    className="focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
>
    Click me
</button>
```

```tsx
// Loading state icin screen reader
<div aria-live="polite" aria-busy={isLoading}>
    {isLoading ? (
        <span className="sr-only">Yukleniyor...</span>
    ) : (
        <DataDisplay />
    )}
</div>
```

**Effort:** Medium | **Impact:** Medium

---

## P2: Orta Oncelik (60 Gun Icinde)

### 6. Toast Notifications

**Problem:** Islem sonuclari kullaniciya bildirilmiyor.

**Cozum - react-hot-toast:**
```tsx
// lib/toast.tsx
import toast, { Toaster } from "react-hot-toast";

export const notify = {
    success: (message: string) => toast.success(message),
    error: (message: string) => toast.error(message),
    loading: (message: string) => toast.loading(message),
    promise: <T,>(
        promise: Promise<T>,
        messages: { loading: string; success: string; error: string }
    ) => toast.promise(promise, messages),
};

// app/layout.tsx'e ekle
<Toaster position="top-right" />
```

**Kullanim:**
```tsx
// reports/page.tsx
const generateReport = async () => {
    notify.promise(
        api.post("/reports/generate", { username }),
        {
            loading: "Rapor olusturuluyor...",
            success: "Rapor hazir!",
            error: "Rapor olusturulamadi",
        }
    );
};
```

**Gerekli Paket:**
```
npm install react-hot-toast
```

**Effort:** Low | **Impact:** High

---

### 7. Chart Visualizations (recharts)

**Problem:** recharts v2.10.0 yuklu ama hicbir yerde kullanilmiyor.

**Dosya:** `frontend/package.json:17`

**Kullanim Alanlari:**
1. Dashboard - Zaman serisi grafikleri (followers, tweets)
2. Analytics - Parti karsilastirma bar chart
3. Reports - Engagement pie chart

**Ornek Implementasyon:**
```tsx
// components/charts/followers-chart.tsx
"use client";

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

interface DataPoint {
    date: string;
    followers: number;
}

interface FollowersChartProps {
    data: DataPoint[];
}

export function FollowersChart({ data }: FollowersChartProps) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString("tr-TR")}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleDateString("tr-TR")}
                    formatter={(value: number) => [value.toLocaleString(), "Takipci"]}
                />
                <Line
                    type="monotone"
                    dataKey="followers"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
```

```tsx
// components/charts/party-bar-chart.tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function PartyBarChart({ data }) {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
                <XAxis dataKey="party" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="member_count" fill="#2563eb" />
                <Bar dataKey="total_tweets" fill="#10b981" />
            </BarChart>
        </ResponsiveContainer>
    );
}
```

**Effort:** Medium | **Impact:** High

---

## P3: Gelecek Planlamasi (90+ Gun)

### 8. Performance Optimization

**Hedefler:**
| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| LCP | ? | <2.5s |
| FID | ? | <100ms |
| CLS | ? | <0.1 |

**Optimizasyonlar:**
```tsx
// Dynamic imports
const FollowersChart = dynamic(() => import("@/components/charts/followers-chart"), {
    loading: () => <Skeleton className="h-[300px]" />,
    ssr: false,
});

// Image optimization
import Image from "next/image";
<Image
    src={avatarUrl}
    alt={name}
    width={40}
    height={40}
    loading="lazy"
/>

// Route prefetching
import Link from "next/link";
<Link href="/reports" prefetch={true}>Raporlar</Link>
```

**Effort:** Medium | **Impact:** Medium

---

### 9. Code Splitting

**Mevcut:** Tum kod tek bundle'da

**Hedef:** Route-based code splitting + feature-based lazy loading

```tsx
// Lazy loaded features
const ReportViewer = lazy(() => import("@/components/features/report-viewer"));

// Route segments (automatic with App Router)
app/
├── (dashboard)/
│   ├── page.tsx          // Bundle 1
│   └── layout.tsx
├── reports/
│   ├── page.tsx          // Bundle 2
│   └── [username]/
│       └── page.tsx      // Bundle 3
└── analytics/
    └── page.tsx          // Bundle 4
```

**Effort:** Low | **Impact:** Medium

---

## Implementasyon Yol Haritasi

```
Hafta 1-2:
├── P0.1: React Query standardizasyonu (tum sayfalar)
├── P0.2: Error Boundary ekleme
└── P2.6: Toast notifications (quick win)

Hafta 3-4:
├── P1.3: Button, Card, Table componentleri
├── P1.4: API client iyilestirmesi
└── P1.5: Temel a11y duzeltmeleri

Hafta 5-8:
├── P1.3: Kalan UI componentleri (Modal, Select, Input vb)
├── P2.7: Chart visualizations
└── P1.5: A11y audit ve duzeltmeler

Hafta 9-12:
├── P3.8: Performance optimization
├── P3.9: Code splitting
└── Test coverage
```

---

## Basari Metrikleri

| KPI | Mevcut | 30 Gun | 60 Gun | 90 Gun |
|-----|--------|--------|--------|--------|
| Custom Components | 2 | 8 | 15 | 20 |
| React Query Usage | 1 sayfa | 3 sayfa | 5 sayfa | Tum sayfalar |
| Lighthouse Performance | ? | 70 | 80 | 90 |
| Lighthouse Accessibility | ? | 70 | 85 | 95 |
| Bundle Size | ? | -10% | -20% | -25% |
| Error Boundary Coverage | 0% | 50% | 80% | 100% |

---

## Referans Dosyalar

| Dosya | Satir | Aciklama |
|-------|-------|----------|
| `frontend/src/app/page.tsx` | 9-12 | React Query kullanimi (iyi ornek) |
| `frontend/src/app/reports/page.tsx` | 27-49 | useState kullanimi (tutarsiz) |
| `frontend/src/components/layout/sidebar.tsx` | - | Mevcut navigation |
| `frontend/src/components/features/metric-card.tsx` | - | Mevcut card component |
| `frontend/src/lib/api.ts` | - | API client (iyilestirilmeli) |
| `frontend/package.json` | 17 | recharts dependency (kullanilmiyor) |

---

*Bu rapor Meclis Istihbarat Sistemi v3.0 kod tabanina dayanmaktadir.*
