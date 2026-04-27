"use client";

import { Anchor, Container, Group, Stack, Text, Title } from "@mantine/core";
import { CompanySearchForm } from "@/features/company-search";
import { AnalysisResult } from "@/widgets/analysis-result";
import { usePostAnalysisApiAnalysisPost } from "@/shared/api";

export default function Home() {
  const mutation = usePostAnalysisApiAnalysisPost();

  return (
    <Container size={960} py="xl">
      <Stack gap="xl">
        <Stack gap="xs" ta="center">
          <Title order={1} c="#1E293B">企業分析エージェント</Title>
          <Text c="#64748B" size="md">
            企業URLを入力するだけで、公開情報を自動収集・分析します
          </Text>
        </Stack>

        <CompanySearchForm
          onSubmit={(data) =>
            mutation.mutate({
              data: {
                company_url: data.company_url,
                force_refresh: data.force_refresh ?? false,
                template: (data.template as "general") ?? "general",
              },
            })
          }
          loading={mutation.isPending}
          cachedResult={mutation.data}
        />

        <AnalysisResult
          data={mutation.data}
          isLoading={mutation.isPending}
          error={mutation.error as Error | null}
        />

        <Group justify="center" gap="md">
          <Anchor href="/compare" size="sm" c="#2563EB">複数企業を比較する →</Anchor>
        </Group>
      </Stack>
    </Container>
  );
}
