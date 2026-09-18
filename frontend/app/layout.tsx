import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Putokaz — vodič kroz procedure",
  description:
    "Opisite šta želite da završite. Putokaz predlaže proceduru, šta poneti i gde da odete.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sr">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
