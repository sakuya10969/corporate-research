import type { Metadata } from "next";
import "./globals.css";
import "@mantine/core/styles.css";
import {
  ColorSchemeScript,
  MantineProvider,
  createTheme,
  mantineHtmlProps,
} from "@mantine/core";
import { QueryProvider } from "./query-provider";
import { ClerkProvider } from "@clerk/nextjs";
import { jaJP } from "@clerk/localizations";

const theme = createTheme({
  primaryColor: "blue",
  defaultRadius: "md",
  colors: {
    blue: [
      "#EFF6FF",
      "#DBEAFE",
      "#BFDBFE",
      "#93C5FD",
      "#60A5FA",
      "#3B82F6",
      "#2563EB",
      "#1D4ED8",
      "#1E40AF",
      "#1E3A8A",
    ],
  },
});

export const metadata: Metadata = {
  title: "企業分析エージェント",
  description: "企業名を入力するだけで、公開情報を自動収集・分析します",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider localization={jaJP}>
      <html lang="ja" {...mantineHtmlProps}>
        <head>
          <ColorSchemeScript forceColorScheme="light" />
        </head>
        <body style={{ backgroundColor: "#FFFFFF" }}>
          <MantineProvider theme={theme} forceColorScheme="light">
            <QueryProvider>{children}</QueryProvider>
          </MantineProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
