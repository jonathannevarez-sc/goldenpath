import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "{{SERVICE_NAME}}",
  description: "Shop service on the Golden Path",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}