import type { Metadata } from 'next';
import './globals.css';
import {PRODUCT_NAME} from '@/lib/product';
export const metadata: Metadata = { title: PRODUCT_NAME, description: 'Evidence-based invoice and expense review' };
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
