import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = ["/", "/login", "/register"];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Herkese açık sayfalara izin ver
    if (publicPaths.includes(pathname)) {
        return NextResponse.next();
    }

    // Diğer tüm rotaları koru
    const token = request.cookies.get("access_token")?.value;

    // Token yoksa login'e yönlendir
    if (!token) {
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("redirect", pathname);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
