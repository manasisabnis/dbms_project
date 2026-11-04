import './globals.css';
import Nav from '@/components/Nav';
export const metadata = { title: 'Legal Case Citation Evolution Analyzer' };
export default function Root({ children }) {
  return (<html lang="en"><body><Nav /><main>{children}</main></body></html>);
}
