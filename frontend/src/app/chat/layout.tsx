import { Sidebar } from "@/components/layout/sidebar";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 bg-[#0B0B0B] overflow-hidden">{children}</main>
    </div>
  );
}
