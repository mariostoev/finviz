import "./globals.css";

export const metadata = {
  title: "Finviz AI Trade Radar",
  description: "Finviz-powered stock scanner with AI-assisted trade idea summaries",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
