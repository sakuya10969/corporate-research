"use client";

import {
  Anchor,
  Badge,
  Button,
  Container,
  Group,
  Loader,
  NativeSelect,
  Stack,
  Table,
  Tabs,
  Text,
  Title,
} from "@mantine/core";
import { IconPlayerPlay, IconRefresh } from "@tabler/icons-react";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import type { AnalysisResponse, RunSummary } from "@/shared/api";
import {
  getGetCompanyApiCompaniesCompanyIdGetQueryKey,
  useGetCompanyApiCompaniesCompanyIdGet,
  useStartAnalysisApiCompaniesCompanyIdAnalysisRunsPost,
  useStartCrawlApiCompaniesCompanyIdCrawlPost,
} from "@/shared/api";

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  pending: { color: "yellow", label: "待機中" },
  crawling: { color: "blue", label: "クロール中" },
  extracting: { color: "cyan", label: "抽出中" },
  analyzing: { color: "indigo", label: "分析中" },
  completed: { color: "green", label: "完了" },
  failed: { color: "red", label: "失敗" },
  active: { color: "green", label: "完了" },
};

const TEMPLATES = [
  { value: "general", label: "一般分析" },
  { value: "investment", label: "投資分析" },
  { value: "sales", label: "営業分析" },
  { value: "hiring", label: "採用分析" },
  { value: "competitor", label: "競合分析" },
  { value: "risk", label: "リスク分析" },
];

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? { color: "gray", label: status };
  return (
    <Badge variant="light" color={config.color} size="sm">
      {config.label}
    </Badge>
  );
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function LatestResultSection({ result }: { result: AnalysisResponse }) {
  const profile = result.structured?.company_profile;
  return (
    <Stack gap="md">
      {result.summary?.overview && (
        <Stack gap="xs">
          <Text fw={600} size="sm" c="#1E293B">
            企業概要
          </Text>
          <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>
            {result.summary.overview}
          </Text>
        </Stack>
      )}

      {profile && (profile.founded || profile.ceo || profile.location) && (
        <Stack gap="xs">
          <Text fw={600} size="sm" c="#1E293B">
            基本情報
          </Text>
          <Stack gap={4}>
            {profile.founded && (
              <Group gap="sm">
                <Text size="sm" c="#64748B" w={80}>
                  設立
                </Text>
                <Text size="sm" c="#1E293B">
                  {profile.founded}
                </Text>
              </Group>
            )}
            {profile.ceo && (
              <Group gap="sm">
                <Text size="sm" c="#64748B" w={80}>
                  代表者
                </Text>
                <Text size="sm" c="#1E293B">
                  {profile.ceo}
                </Text>
              </Group>
            )}
            {profile.location && (
              <Group gap="sm">
                <Text size="sm" c="#64748B" w={80}>
                  所在地
                </Text>
                <Text size="sm" c="#1E293B">
                  {profile.location}
                </Text>
              </Group>
            )}
            {profile.employees && (
              <Group gap="sm">
                <Text size="sm" c="#64748B" w={80}>
                  従業員数
                </Text>
                <Text size="sm" c="#1E293B">
                  {profile.employees}
                </Text>
              </Group>
            )}
          </Stack>
        </Stack>
      )}

      {result.scores && (
        <Stack gap="xs">
          <Text fw={600} size="sm" c="#1E293B">
            スコア
          </Text>
          <Group gap="md">
            {result.scores.financial_health && (
              <Badge variant="light" color="blue" size="lg">
                財務 {result.scores.financial_health.score}
              </Badge>
            )}
            {result.scores.growth_potential && (
              <Badge variant="light" color="green" size="lg">
                成長性 {result.scores.growth_potential.score}
              </Badge>
            )}
            {result.scores.competitive_edge && (
              <Badge variant="light" color="violet" size="lg">
                競合優位 {result.scores.competitive_edge.score}
              </Badge>
            )}
            {result.scores.risk_level && (
              <Badge variant="light" color="orange" size="lg">
                リスク {result.scores.risk_level.score}
              </Badge>
            )}
            {result.scores.info_transparency && (
              <Badge variant="light" color="cyan" size="lg">
                透明性 {result.scores.info_transparency.score}
              </Badge>
            )}
          </Group>
        </Stack>
      )}

      {result.summary?.swot && (
        <Stack gap="xs">
          <Text fw={600} size="sm" c="#1E293B">
            SWOT
          </Text>
          <Group gap="md" align="flex-start">
            {(result.summary.swot.strengths ?? []).length > 0 && (
              <Stack gap={2}>
                <Text size="xs" c="#64748B">
                  強み
                </Text>
                {result.summary.swot.strengths?.slice(0, 3).map((s) => (
                  <Badge key={s} variant="light" color="green" size="sm">
                    {s}
                  </Badge>
                ))}
              </Stack>
            )}
            {(result.summary.swot.weaknesses ?? []).length > 0 && (
              <Stack gap={2}>
                <Text size="xs" c="#64748B">
                  弱み
                </Text>
                {result.summary.swot.weaknesses?.slice(0, 3).map((w) => (
                  <Badge key={w} variant="light" color="red" size="sm">
                    {w}
                  </Badge>
                ))}
              </Stack>
            )}
          </Group>
        </Stack>
      )}

      {result.analyzed_at && (
        <Text size="xs" c="#64748B">
          分析日時: {formatDate(result.analyzed_at)}
          {result.template &&
            result.template !== "general" &&
            ` / テンプレート: ${result.template}`}
        </Text>
      )}
    </Stack>
  );
}

function RunHistorySection({ runs }: { runs: RunSummary[] }) {
  if (runs.length === 0) {
    return (
      <Text size="sm" c="#64748B">
        分析履歴がありません
      </Text>
    );
  }

  const typeLabel: Record<string, string> = {
    initial: "初回分析",
    refresh: "差分更新",
    deep_analysis: "Deep Analysis",
    crawl_only: "クロールのみ",
  };
  const statusColor: Record<string, string> = {
    completed: "green",
    failed: "red",
    running: "blue",
    pending: "gray",
  };

  return (
    <Table striped highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>種別</Table.Th>
          <Table.Th>ステータス</Table.Th>
          <Table.Th>テンプレート</Table.Th>
          <Table.Th>開始日時</Table.Th>
          <Table.Th>所要時間</Table.Th>
          <Table.Th>エラー</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {runs.map((run) => (
          <Table.Tr key={run.run_id}>
            <Table.Td>
              <Badge variant="light" size="sm">
                {typeLabel[run.run_type] ?? run.run_type}
              </Badge>
            </Table.Td>
            <Table.Td>
              <Badge
                variant="light"
                color={statusColor[run.status] ?? "gray"}
                size="sm"
              >
                {run.status}
              </Badge>
            </Table.Td>
            <Table.Td>
              <Text size="sm">{run.template}</Text>
            </Table.Td>
            <Table.Td>
              <Text size="sm">{formatDate(run.started_at)}</Text>
            </Table.Td>
            <Table.Td>
              <Text size="sm">
                {run.duration_ms
                  ? `${(run.duration_ms / 1000).toFixed(1)}s`
                  : "—"}
              </Text>
            </Table.Td>
            <Table.Td>
              {run.error_message && (
                <Text size="xs" c="red" lineClamp={1}>
                  {run.error_message}
                </Text>
              )}
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const queryClient = useQueryClient();
  const [template, setTemplate] = useState("general");

  const { data, isLoading } = useGetCompanyApiCompaniesCompanyIdGet(companyId);

  const invalidateCompany = () => {
    queryClient.invalidateQueries({
      queryKey: getGetCompanyApiCompaniesCompanyIdGetQueryKey(companyId),
    });
  };

  const crawlMutation = useStartCrawlApiCompaniesCompanyIdCrawlPost({
    mutation: { onSuccess: invalidateCompany },
  });

  const analysisMutation =
    useStartAnalysisApiCompaniesCompanyIdAnalysisRunsPost({
      mutation: { onSuccess: invalidateCompany },
    });

  const handleCrawl = () => {
    crawlMutation.mutate({ companyId });
  };

  const handleAnalysis = () => {
    analysisMutation.mutate({
      companyId,
      data: { template, force_refresh: false },
    });
  };

  const handleForceRefresh = () => {
    analysisMutation.mutate({
      companyId,
      data: { template: "general", force_refresh: true },
    });
  };

  if (isLoading) {
    return (
      <Container size={1100} py="xl">
        <Group justify="center" py="xl">
          <Loader size="md" />
        </Group>
      </Container>
    );
  }

  if (!data) {
    return (
      <Container size={1100} py="xl">
        <Text c="red" ta="center">
          企業情報の取得に失敗しました
        </Text>
      </Container>
    );
  }

  const isProcessing = [
    "pending",
    "crawling",
    "extracting",
    "analyzing",
  ].includes(data.status);

  return (
    <Container size={1100} py="xl">
      <Stack gap="xl">
        {/* ヘッダー: 企業基本情報 */}
        <Stack gap="xs">
          <Group justify="space-between" align="flex-start">
            <Stack gap={4}>
              <Title order={1} c="#1E293B">
                {data.display_name || data.normalized_url}
              </Title>
              <Anchor
                href={data.primary_url}
                target="_blank"
                rel="noopener noreferrer"
                size="sm"
                c="#2563EB"
              >
                {data.primary_url}
              </Anchor>
            </Stack>
            <StatusBadge status={data.status} />
          </Group>

          <Group gap="lg">
            <Text size="sm" c="#64748B">
              最終クロール: {formatDate(data.last_page_crawl_at)}
            </Text>
            <Text size="sm" c="#64748B">
              最終分析: {formatDate(data.last_analyzed_at)}
            </Text>
            <Text size="sm" c="#64748B">
              分析回数: {data.analysis_count}
            </Text>
          </Group>
        </Stack>

        {/* アクションボタン */}
        <Group gap="sm">
          <Button
            variant="light"
            leftSection={<IconRefresh size={16} />}
            onClick={handleCrawl}
            loading={crawlMutation.isPending}
            disabled={isProcessing}
          >
            再クロール
          </Button>
          <Button
            variant="light"
            color="orange"
            leftSection={<IconRefresh size={16} />}
            onClick={handleForceRefresh}
            loading={analysisMutation.isPending}
            disabled={isProcessing}
          >
            再分析（フルリフレッシュ）
          </Button>
        </Group>

        {/* Deep Analysis フォーム */}
        <Stack
          gap="sm"
          p="md"
          style={{ border: "1px solid #E2E8F0", borderRadius: 8 }}
        >
          <Text fw={600} size="sm" c="#1E293B">
            Deep Analysis（テンプレート別分析）
          </Text>
          <Text size="xs" c="#64748B">
            蓄積済みデータを使用して、テンプレートを変えて再分析します。
          </Text>
          <Group gap="sm">
            <NativeSelect
              value={template}
              onChange={(e) => setTemplate(e.currentTarget.value)}
              data={TEMPLATES}
              style={{ width: 200 }}
              disabled={analysisMutation.isPending}
            />
            <Button
              leftSection={<IconPlayerPlay size={16} />}
              onClick={handleAnalysis}
              loading={analysisMutation.isPending}
              disabled={isProcessing || data.status === "pending"}
            >
              分析実行
            </Button>
          </Group>
          {data.status === "pending" && (
            <Text size="xs" c="orange">
              クロールが完了するまで Deep Analysis は実行できません。
            </Text>
          )}
        </Stack>

        {(crawlMutation.isError || analysisMutation.isError) && (
          <Text c="red" size="sm">
            操作に失敗しました。しばらくしてから再試行してください。
          </Text>
        )}

        {/* タブ: 最新結果 / 分析履歴 */}
        <Tabs defaultValue="result">
          <Tabs.List>
            <Tabs.Tab value="result">最新分析結果</Tabs.Tab>
            <Tabs.Tab value="history">分析履歴</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="result" pt="md">
            {data.latest_result ? (
              <LatestResultSection result={data.latest_result} />
            ) : (
              <Text size="sm" c="#64748B">
                {isProcessing
                  ? "分析処理中です。しばらくお待ちください。"
                  : "分析結果がまだありません。"}
              </Text>
            )}
          </Tabs.Panel>

          <Tabs.Panel value="history" pt="md">
            <RunHistorySection runs={data.recent_runs ?? []} />
          </Tabs.Panel>
        </Tabs>

        <Group justify="center" gap="md">
          <Anchor href="/companies" size="sm" c="#2563EB">
            ← 企業一覧に戻る
          </Anchor>
        </Group>
      </Stack>
    </Container>
  );
}
