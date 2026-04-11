
import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "FRANK OS",
  description: "Enterprise command surface"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
