import { auth, currentUser } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export async function POST() {
  const { userId, getToken } = await auth();

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = await currentUser();
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 401 });
  }

  const email =
    user.emailAddresses.find((e) => e.id === user.primaryEmailAddressId)
      ?.emailAddress ?? "";
  const displayName =
    [user.firstName, user.lastName].filter(Boolean).join(" ") ||
    user.username ||
    email;

  const token = await getToken();
  if (!token) {
    return NextResponse.json(
      { error: "Failed to get token" },
      { status: 500 }
    );
  }

  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const res = await fetch(`${apiBaseUrl}/api/users/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email, display_name: displayName }),
  });

  if (!res.ok) {
    const detail = await res.text();
    return NextResponse.json(
      { error: "Sync failed", detail },
      { status: res.status }
    );
  }

  const data = await res.json();
  return NextResponse.json(data);
}
