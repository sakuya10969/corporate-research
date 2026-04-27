import { Container, Stack, Text, Title } from "@mantine/core";
import type { Metadata } from "next";
import { AnalysisResult } from "@/widgets/analysis-result";

type Props = { params: Promise<{ shareId: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { shareId } = await params;
  return {
    title: "企業分析レポート",
    description: `共有された企業分析レポート (${shareId})`,
    openGraph: { title: "企業分析レポート", description: "企業分析エージェントによる分析結果" },
  };
}

export default async function SharePage({ params }: Props) {
  const { shareId } = await params;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  let data = null;
  try {
    const res = await fetch(`${apiUrl}/api/share/${shareId}`, { cache: "no-store" });
    if (res.ok) data = await res.json();
  } catch {}

  return (
    <Container size={960} py="xl">
      <Stack gap="xl">
        <Stack gap="xs" ta="center">
          <Title order={2} c="#1E293B">企業分析レポート</Title>
          <Text c="#64748B" size="sm">このページは共有された分析結果です（読み取り専用）</Text>
        </Stack>
        <AnalysisResult data={data} isLoading={false} error={null} />
      </Stack>
    </Container>
  );
}
