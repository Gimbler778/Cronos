import "./globals.css";

export const metadata = { title: "Cronos", description: "College timetable optimizer" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
