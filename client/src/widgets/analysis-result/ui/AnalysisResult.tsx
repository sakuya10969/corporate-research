"use client";

import { Alert, Anchor, List, Skeleton, Stack, Text } from "@mantine/core";
import { IconAlertTriangle } from "@tabler/icons-react";
import type { AnalysisResponse } from "@/shared/api";
import { CompanyCard } from "@/entities/company";

type Props = {
  data?: AnalysisResponse;
  isLoading: boolean;
  error?: Error | null;
};

function LoadingSkeleton() {
  return (
    <Stack gap="md">
      <Skeleton height={28} width="40%" />
      <Skeleton height={120} />
      <Skeleton height={120} />
      <Skeleton height={80} />
      <Skeleton height={60} />
    </Stack>
  );
}

export function AnalysisResult({ data, isLoading, error }: Props) {
  if (isLoading) return <LoadingSkeleton />;

  if (error) {
    return (
      <Alert
        icon={<IconAlertTriangle size={16} />}
        color="red"
        title="エラーが発生しました"
        styles={{ root: { backgroundColor: "#FEF2F2" } }}
      >
        <Text c="red" size="sm">
          {error.message || "分析処理に失敗しました。もう一度お試しください。"}
        </Text>
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Stack gap="md">
      <Text fw={700} size="xl" c="#1E293B">
        {data.company_name}
      </Text>

      <CompanyCard title="企業概要">
        <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
          {data.summary}
        </Text>
      </CompanyCard>

      <CompanyCard title="事業内容">
        <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
          {data.business_description}
        </Text>
      </CompanyCard>

      <CompanyCard title="主要な発見事項">
        <List size="sm" spacing="xs">
          {data.key_findings.map((finding) => (
            <List.Item key={finding} c="#1E293B">
              {finding}
            </List.Item>
          ))}
        </List>
      </CompanyCard>

      <CompanyCard title="参照ソース">
        <List size="sm" spacing="xs" listStyleType="none">
          {data.sources.map((source) => (
            <List.Item key={source.url}>
              <Anchor
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                size="sm"
                c="#2563EB"
              >
                {source.title}
              </Anchor>
            </List.Item>
          ))}
        </List>
      </CompanyCard>
    </Stack>
  );
}
