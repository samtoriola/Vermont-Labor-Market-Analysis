import './globals.css';

export const metadata = {
  title: 'Vermont Labor Market Overview',
  description:
    'Vermont employment structure, wage quality, employer demand, education pathways, VSCS program alignment and regional variation.',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* Strada deployable type stack: EB Garamond for Larken, DM Sans for body. */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=EB+Garamond:wght@500;600&display=swap"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
