import { NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

// Protects all pages; API routes enforce their own auth + roles.
export async function middleware(req) {
  const t = req.cookies.get('token')?.value;
  try {
    await jwtVerify(t, new TextEncoder().encode(process.env.JWT_SECRET));
    return NextResponse.next();
  } catch {
    return NextResponse.redirect(new URL('/login', req.url));
  }
}
export const config = { matcher: ['/((?!api|login|_next|favicon.ico).*)'] };
