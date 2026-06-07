import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // /panel altındaki tüm rotaları koru
    if (pathname.startsWith("/panel")) {
        const token = request.cookies.get("access_token")?.value
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
    matcher: ["/panel/:path*"],
};
