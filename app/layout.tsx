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
  title: 'Vollmer Atlas — Follow a Family Thread',
  description:
    'Follow the Vollmer family tree one line at a time, with evidence and migration history close at hand.',
  openGraph: {
    title: 'Vollmer Atlas — Follow a Family Thread',
    description:
      'Follow 391 people one family line at a time, with preserved records and migration history.',
    images: [
      {
        url: '/og.png',
        width: 1734,
        height: 907,
        alt: 'Vollmer Atlas — One Family Line at a Time',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Vollmer Atlas — Follow a Family Thread',
    description:
      'Follow 391 people one family line at a time, with preserved records and migration history.',
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
