import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Lineage — The Vollmer Family Archive',
  description:
    'Explore the Vollmer family tree, its evidence, and generations of movement across the map.',
  openGraph: {
    title: 'Lineage — The Vollmer Family Archive',
    description:
      'Explore 308 people, preserved records, and generations of family movement.',
    images: [{ url: '/og.png', width: 1731, height: 909, alt: 'Lineage — The Vollmer Family Archive' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Lineage — The Vollmer Family Archive',
    description:
      'Explore 308 people, preserved records, and generations of family movement.',
    images: ['/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
