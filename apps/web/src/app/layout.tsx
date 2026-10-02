import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'AP Review Desk', description: 'Synthetic finance screening workspace' };
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
