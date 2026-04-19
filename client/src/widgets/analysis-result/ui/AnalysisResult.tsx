"use client";

import {
  Alert,
  Anchor,
  Badge,
  Group,
  List,
  Skeleton,
  Stack,
  Text,
} from "@mantine/core";
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
      <Skeleton height={100} />
      <Skeleton height={100} />
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

  const { structured, summary } = data;
  const profile = structured?.company_profile;

  return (
    <Stack gap="md">
      <Text fw={700} size="xl" c="#1E293B">
        {data.company_name}
      </Text>

      {/* 企業概要サマリー */}
      {summary?.overview && (
        <CompanyCard title="企業概要">
          <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
            {summary.overview}
          </Text>
        </CompanyCard>
      )}

      {/* 企業プロフィール */}
      {profile && (profile.name || profile.founded || profile.ceo || profile.location) && (
        <CompanyCard title="企業プロフィール">
          <Stack gap={4}>
            {profile.name && <ProfileRow label="社名" value={profile.name} />}
            {profile.founded && <ProfileRow label="設立" value={profile.founded} />}
            {profile.ceo && <ProfileRow label="代表者" value={profile.ceo} />}
            {profile.location && <ProfileRow label="所在地" value={profile.location} />}
            {profile.employees && <ProfileRow label="従業員数" value={profile.employees} />}
            {profile.capital && <ProfileRow label="資本金" value={profile.capital} />}
          </Stack>
        </CompanyCard>
      )}

      {/* 事業モデル */}
      {summary?.business_model && (
        <CompanyCard title="事業モデル">
          <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
            {summary.business_model}
          </Text>
        </CompanyCard>
      )}

      {/* 事業領域 */}
      {structured?.business_domains && structured.business_domains.length > 0 && (
        <CompanyCard title="事業領域">
          <Group gap="xs">
            {structured.business_domains.map((domain) => (
              <Badge key={domain} variant="light" color="blue" size="md">
                {domain}
              </Badge>
            ))}
          </Group>
        </CompanyCard>
      )}

      {/* プロダクト・サービス */}
      {structured?.products && structured.products.length > 0 && (
        <CompanyCard title="プロダクト・サービス">
          <List size="sm" spacing="xs">
            {structured.products.map((product) => (
              <List.Item key={product} c="#1E293B">
                {product}
              </List.Item>
            ))}
          </List>
        </CompanyCard>
      )}

      {/* 財務情報 */}
      {structured?.financials &&
        (structured.financials.revenue || structured.financials.operating_income) && (
          <CompanyCard title="財務情報">
            <Stack gap={4}>
              {structured.financials.revenue && (
                <ProfileRow label="売上高" value={structured.financials.revenue} />
              )}
              {structured.financials.operating_income && (
                <ProfileRow label="営業利益" value={structured.financials.operating_income} />
              )}
              {structured.financials.net_income && (
                <ProfileRow label="純利益" value={structured.financials.net_income} />
              )}
              {structured.financials.growth_rate && (
                <ProfileRow label="成長率" value={structured.financials.growth_rate} />
              )}
            </Stack>
          </CompanyCard>
        )}

      {/* SWOT分析 */}
      {summary?.swot && (
        <CompanyCard title="SWOT分析">
          <Stack gap="sm">
            {summary.swot.strengths && summary.swot.strengths.length > 0 && (
              <SwotSection label="強み (Strengths)" items={summary.swot.strengths} />
            )}
            {summary.swot.weaknesses && summary.swot.weaknesses.length > 0 && (
              <SwotSection label="弱み (Weaknesses)" items={summary.swot.weaknesses} />
            )}
            {summary.swot.opportunities && summary.swot.opportunities.length > 0 && (
              <SwotSection label="機会 (Opportunities)" items={summary.swot.opportunities} />
            )}
            {summary.swot.threats && summary.swot.threats.length > 0 && (
              <SwotSection label="脅威 (Threats)" items={summary.swot.threats} />
            )}
          </Stack>
        </CompanyCard>
      )}

      {/* リスク要因 */}
      {summary?.risks && summary.risks.length > 0 && (
        <CompanyCard title="リスク要因">
          <List size="sm" spacing="xs">
            {summary.risks.map((risk) => (
              <List.Item key={risk} c="#1E293B">
                {risk}
              </List.Item>
            ))}
          </List>
        </CompanyCard>
      )}

      {/* 競合企業 */}
      {summary?.competitors && summary.competitors.length > 0 && (
        <CompanyCard title="競合企業（推定）">
          <Group gap="xs">
            {summary.competitors.map((comp) => (
              <Badge key={comp} variant="light" color="gray" size="md">
                {comp}
              </Badge>
            ))}
          </Group>
        </CompanyCard>
      )}

      {/* 今後の展望 */}
      {summary?.outlook && (
        <CompanyCard title="今後の展望">
          <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
            {summary.outlook}
          </Text>
        </CompanyCard>
      )}

      {/* ニュース */}
      {structured?.news && structured.news.length > 0 && (
        <CompanyCard title="ニュース">
          <Stack gap="xs">
            {structured.news.map((item) => (
              <Stack key={item.title} gap={2}>
                <Group gap="xs">
                  <Text size="sm" fw={500} c="#1E293B">
                    {item.title}
                  </Text>
                  {item.date && (
                    <Text size="xs" c="#64748B">
                      {item.date}
                    </Text>
                  )}
                </Group>
                {item.summary && (
                  <Text size="xs" c="#64748B">
                    {item.summary}
                  </Text>
                )}
              </Stack>
            ))}
          </Stack>
        </CompanyCard>
      )}

      {/* 参照ソース */}
      <CompanyCard title="参照ソース">
        <List size="sm" spacing="xs" listStyleType="none">
          {data.sources.map((source) => (
            <List.Item key={source.url}>
              <Group gap="xs">
                <Anchor
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  size="sm"
                  c="#2563EB"
                >
                  {source.title}
                </Anchor>
                {source.category && source.category !== "その他" && (
                  <Badge variant="light" color="blue" size="xs">
                    {source.category}
                  </Badge>
                )}
              </Group>
            </List.Item>
          ))}
        </List>
      </CompanyCard>
    </Stack>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <Group gap="sm">
      <Text size="sm" c="#64748B" w={80}>
        {label}
      </Text>
      <Text size="sm" c="#1E293B">
        {value}
      </Text>
    </Group>
  );
}

function SwotSection({ label, items }: { label: string; items: string[] }) {
  return (
    <Stack gap={2}>
      <Text size="sm" fw={500} c="#1E293B">
        {label}
      </Text>
      <List size="sm" spacing={2}>
        {items.map((item) => (
          <List.Item key={item} c="#1E293B">
            {item}
          </List.Item>
        ))}
      </List>
    </Stack>
  );
}
