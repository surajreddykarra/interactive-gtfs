import type { Metadata } from 'next';
import { TransitProvider } from '@/context/TransitContext';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://interactive-gtfs.vercel.app'),
  title: 'Hyderabad Transit Map',
  description: 'Interactive visualization of Hyderabad public transit - Metro, MMTS, and City Bus',
  keywords: ['Hyderabad', 'transit', 'metro', 'MMTS', 'bus', 'GTFS', 'map'],
  icons: {
    icon: '/icon.svg',
  },
  openGraph: {
    title: 'Hyderabad Transit Map',
    description: 'Interactive visualization of Hyderabad public transit - Metro, MMTS, and City Bus',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Hyderabad Transit Map',
      },
    ],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Hyderabad Transit Map',
    description: 'Interactive visualization of Hyderabad public transit - Metro, MMTS, and City Bus',
    images: ['/og-image.png'],
    creator: '@jarusionn',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css"
        />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css"
        />
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
      </head>
      <body className="font-sans dark:bg-black dark:text-white">
        <TransitProvider>
          {children}
        </TransitProvider>
      </body>
    </html>
  );
}
