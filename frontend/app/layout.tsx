import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { APP_NAME, APP_TAGLINE } from "@/lib/copy";
import "./globals.css";

export const metadata: Metadata = {
  title: `${APP_NAME} — ${APP_TAGLINE.replace(/\.$/, "")}`,
  description:
    "Opišite šta želite da završite. NaŠalter predlaže proceduru, šta poneti i gde da odete.",
  icons: {
    icon: "/brand/nasalter-icon.png",
    apple: "/brand/nasalter-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sr" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var s=localStorage.getItem('nasalter-font-scale')||localStorage.getItem('putokaz-font-scale');if(s){document.documentElement.style.setProperty('--font-scale',s);}}catch(e){}})();",
          }}
        />
      </head>
      <body suppressHydrationWarning>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
