"use client";

import {
  Badge,
  Button,
  Container,
  Group,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import { useState } from "react";
import { usePostCompareApiComparePost } from "@/shared/api";
import type { AnalysisResponse } from "@/shared/api";
import { CompanyCard } from "@/entities/company";

export default function ComparePage() {
  const [urls, setUrls] = useState(["", ""]);
  const mutation = usePostCompareApiComparePost();

  const addUrl = () => { if (urls.length < 3) setUrls([...urls, ""]); };
  const removeUrl = (i: number) => setUrls(urls.filter((_, idx) => idx !== i));
  const updateUrl = (i: number, v: string) => setUrls(urls.map((u, idx) => idx === i ? v : u));

  const handleCompare = () => {
    const valid = urls.filter((u) => /^https?:\/\//.test(u));
    if (valid.length < 2) return;
    mutation.mutate({ data: { urls: valid } });
  };

  const results: AnalysisResponse[] = mutation.data?.results ?? [];

  return (
    <Container size={1200} py="xl">
      <Stack gap="xl">
        <Stack gap="xs" ta="center">
          <Title order={1} c="#1E293B">複数企業比較</Title>
          <Text c="#64748B">最大3社の企業を並べて比較分析します</Text>
        </Stack>

        <Stack gap="sm">
          {urls.map((url, i) => (
            <Group key={i} gap="sm">
              <TextInput
                placeholder={`企業URL ${i + 1}`}
                value={url}
                onChange={(e) => updateUrl(i, e.currentTarget.value)}
                style={{ flex: 1 }}
                disabled={mutation.isPending}
              />
              {urls.length > 2 && (
                <Button variant="subtle" color="red" size="sm" onClick={() => removeUrl(i)}>
                  <IconTrash size={16} />
                </Button>
              )}
            </Group>
          ))}
          <Group gap="sm">
            {urls.length < 3 && (
              <Button variant="light" leftSection={<IconPlus size={16} />} onClick={addUrl} size="sm">
                企業を追加
              </Button>
            )}
            <Button onClick={handleCompare} loading={mutation.isPending} disabled={urls.filter((u) => /^https?:\/\//.test(u)).length < 2}>
              比較分析する
            </Button>
          </Group>
        </Stack>

        {/* 比較サマリー */}
        {mutation.data?.comparison_summary && (
          <CompanyCard title="比較サマリー">
            <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
              {mutation.data.comparison_summary}
            </Text>
          </CompanyCard>
        )}

        {/* 横並び比較テーブル */}
        {results.length > 0 && (
          <Stack gap="md">
            {/* 企業名ヘッダー */}
            <Group grow gap="md">
              {results.map((r) => (
                <CompanyCard key={r.company_url} title={r.structured?.company_profile?.name || r.company_url}>
                  <Text size="xs" c="#2563EB">{r.company_url}</Text>
                </CompanyCard>
              ))}
            </Group>

            {/* 事業領域 */}
            <Group grow gap="md" align="flex-start">
              {results.map((r) => (
                <CompanyCard key={r.company_url} title="事業領域">
                  <Group gap="xs">
                    {(r.structured?.business_domains ?? []).map((d) => (
                      <Badge key={d} variant="light" color="blue" size="sm">{d}</Badge>
                    ))}
                  </Group>
                </CompanyCard>
              ))}
            </Group>

            {/* 財務情報 */}
            <Group grow gap="md" align="flex-start">
              {results.map((r) => (
                <CompanyCard key={r.company_url} title="財務情報">
                  <Stack gap={2}>
                    {r.structured?.financials?.revenue && <Text size="sm">売上: {r.structured.financials.revenue}</Text>}
                    {r.structured?.financials?.growth_rate && <Text size="sm">成長率: {r.structured.financials.growth_rate}</Text>}
                  </Stack>
                </CompanyCard>
              ))}
            </Group>

            {/* SWOT */}
            <Group grow gap="md" align="flex-start">
              {results.map((r) => (
                <CompanyCard key={r.company_url} title="SWOT">
                  <Stack gap="xs">
                    {(r.summary?.swot?.strengths ?? []).slice(0, 3).map((s) => (
                      <Badge key={s} variant="light" color="green" size="sm">{s}</Badge>
                    ))}
                    {(r.summary?.swot?.weaknesses ?? []).slice(0, 2).map((w) => (
                      <Badge key={w} variant="light" color="red" size="sm">{w}</Badge>
                    ))}
                  </Stack>
                </CompanyCard>
              ))}
            </Group>
          </Stack>
        )}
      </Stack>
    </Container>
  );
}
