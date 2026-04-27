import { clerkMiddleware } from "@clerk/nextjs/server";

// 現時点では保護対象ルートなし。
// 認証必須ページを追加する場合は createRouteMatcher で定義する。
// 例: const isProtectedRoute = createRouteMatcher(["/mypage(.*)"]);
export default clerkMiddleware();

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
