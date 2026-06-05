import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // /admin altındaki tüm rotaları koru
    if (pathname.startsWith("/admin")) {
        const token = request.cookies.get("token")?.value
            || request.headers.get("authorization")?.replace("Bearer ", "");

        // Token yoksa login'e yönlendir
        if (!token) {
            const loginUrl = new URL("/login", request.url);
            loginUrl.searchParams.set("redirect", pathname);
            return NextResponse.redirect(loginUrl);
        }
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/admin/:path*"],
};
