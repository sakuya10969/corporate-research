"use client";

import { Container, Stack, Text, Title } from "@mantine/core";
import { CompanySearchForm } from "@/features/company-search";
import { AnalysisResult } from "@/widgets/analysis-result";
import { usePostAnalysisApiAnalysisPost } from "@/shared/api";

export default function Home() {
  const mutation = usePostAnalysisApiAnalysisPost();

  return (
    <Container size={960} py="xl">
      <Stack gap="xl">
        <Stack gap="xs" ta="center">
          <Title order={1} c="#1E293B">
            企業分析エージェント
          </Title>
          <Text c="#64748B" size="md">
            企業名を入力するだけで、公開情報を自動収集・分析します
          </Text>
        </Stack>

        <CompanySearchForm
          onSubmit={(data) => mutation.mutate({ data })}
          loading={mutation.isPending}
        />

        <AnalysisResult
          data={mutation.data}
          isLoading={mutation.isPending}
          error={mutation.error as Error | null}
        />
      </Stack>
    </Container>
  );
}
