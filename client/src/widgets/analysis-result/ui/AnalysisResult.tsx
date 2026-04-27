"use client";

import {
  Alert,
  Anchor,
  Badge,
  Button,
  Group,
  List,
  Menu,
  Skeleton,
  Stack,
  Tabs,
  Text,
  Textarea,
} from "@mantine/core";
import {
  IconAlertTriangle,
  IconCheck,
  IconCopy,
  IconDownload,
  IconMessage,
  IconShare,
} from "@tabler/icons-react";
import { useState } from "react";
import type { AnalysisResponse, RunSummary } from "@/shared/api";
import { useCreateShareApiAnalysisResultIdSharePost } from "@/shared/api/generated/share/share";
import {
  useGetCompanyRunsApiCompaniesCompanyIdRunsGet,
  usePostDeepResearchApiCompaniesCompanyIdDeepResearchPost,
} from "@/shared/api/generated/companies/companies";
import { CompanyCard } from "@/entities/company";
import { env } from "@/shared/config/env";

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
      <Skeleton height={80} />
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// ダウンロードボタン（T-026）
// ---------------------------------------------------------------------------
function DownloadMenu({ resultId }: { resultId: string }) {
  const [loading, setLoading] = useState<"pdf" | "docx" | null>(null);

  const handleDownload = async (format: "pdf" | "docx") => {
    setLoading(format);
    try {
      const res = await fetch(
        `${env.apiUrl}/api/analysis/${resultId}/download?format=${format}`
      );
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(null);
    }
  };

  return (
    <Menu shadow="md" width={160}>
      <Menu.Target>
        <Button
          size="xs"
          variant="light"
          leftSection={<IconDownload size={14} />}
          loading={loading !== null}
        >
          ダウンロード
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item onClick={() => handleDownload("pdf")}>PDF (.pdf)</Menu.Item>
        <Menu.Item onClick={() => handleDownload("docx")}>Word (.docx)</Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}

// ---------------------------------------------------------------------------
// シェアボタン（T-035）
// ---------------------------------------------------------------------------
function ShareButton({ resultId }: { resultId: string }) {
  const [copied, setCopied] = useState(false);
  const shareMutation = useCreateShareApiAnalysisResultIdSharePost();

  const handleShare = async () => {
    const res = await shareMutation.mutateAsync({ resultId });
    const shareUrl = `${window.location.origin}/share/${res.share_id}`;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      size="xs"
      variant="light"
      leftSection={copied ? <IconCheck size={14} /> : <IconShare size={14} />}
      onClick={handleShare}
      loading={shareMutation.isPending}
      color={copied ? "green" : "blue"}
    >
      {copied ? "コピーしました" : "シェア"}
    </Button>
  );
}

// ---------------------------------------------------------------------------
// 分析履歴タブ（T-024）
// ---------------------------------------------------------------------------
function HistoryTab({ companyId }: { companyId: string }) {
  const { data, isLoading } = useGetCompanyRunsApiCompaniesCompanyIdRunsGet(companyId);

  if (isLoading) return <Skeleton height={80} />;
  if (!data?.runs?.length) return <Text size="sm" c="#64748B">履歴がありません</Text>;

  const typeLabel: Record<string, string> = {
    initial: "初回分析",
    refresh: "差分更新",
    deep_research: "深掘り",
  };
  const statusColor: Record<string, string> = {
    completed: "green",
    failed: "red",
    running: "blue",
    pending: "gray",
  };

  return (
    <Stack gap="xs">
      {data.runs.map((run: RunSummary) => (
        <Group key={String(run.run_id)} justify="space-between" p="xs" style={{ border: "1px solid #E2E8F0", borderRadius: 8 }}>
          <Stack gap={2}>
            <Group gap="xs">
              <Badge size="xs" variant="light">{typeLabel[run.run_type] ?? run.run_type}</Badge>
              <Badge size="xs" color={statusColor[run.status] ?? "gray"}>{run.status}</Badge>
              {run.template && run.template !== "general" && (
                <Badge size="xs" variant="outline" color="violet">{run.template}</Badge>
              )}
            </Group>
            <Text size="xs" c="#64748B">
              {run.started_at ? new Date(run.started_at).toLocaleString("ja-JP") : "—"}
              {run.duration_ms ? ` (${(run.duration_ms / 1000).toFixed(1)}s)` : ""}
            </Text>
            {run.error_message && (
              <Text size="xs" c="red">{run.error_message}</Text>
            )}
          </Stack>
        </Group>
      ))}
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// 深掘り質問UI（T-031）
// ---------------------------------------------------------------------------
function DeepResearchPanel({ companyId, resultId }: { companyId: string; resultId: string }) {
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const deepMutation = usePostDeepResearchApiCompaniesCompanyIdDeepResearchPost();

  const handleAsk = async () => {
    if (!question.trim()) return;
    const q = question.trim();
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    const res = await deepMutation.mutateAsync({
      companyId,
      data: { question: q, result_id: resultId, session_id: sessionId },
    });
    setSessionId(String(res.session_id ?? ""));
    setMessages((prev) => [...prev, { role: "assistant", content: String(res.answer ?? "") }]);
  };

  return (
    <Stack gap="sm">
      {messages.map((m, i) => (
        <Stack key={i} gap={2} align={m.role === "user" ? "flex-end" : "flex-start"}>
          <Text size="xs" c="#64748B">{m.role === "user" ? "あなた" : "AI"}</Text>
          <Text
            size="sm"
            p="xs"
            style={{
              background: m.role === "user" ? "#EFF6FF" : "#F8FAFC",
              borderRadius: 8,
              maxWidth: "85%",
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
            }}
          >
            {m.content}
          </Text>
        </Stack>
      ))}
      <Group gap="xs" align="flex-end">
        <Textarea
          placeholder="質問を入力してください（例: この会社の強みの本質は何か）"
          value={question}
          onChange={(e) => setQuestion(e.currentTarget.value)}
          disabled={deepMutation.isPending}
          style={{ flex: 1 }}
          autosize
          minRows={2}
        />
        <Button
          leftSection={<IconMessage size={16} />}
          onClick={handleAsk}
          loading={deepMutation.isPending}
          disabled={!question.trim()}
        >
          送信
        </Button>
      </Group>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// スコアカード（T-033）
// ---------------------------------------------------------------------------
function ScoreCard({ scores }: { scores: NonNullable<AnalysisResponse["scores"]> }) {
  const items = [
    { key: "financial_health", label: "財務健全性" },
    { key: "growth_potential", label: "成長性" },
    { key: "competitive_edge", label: "競合優位性" },
    { key: "risk_level", label: "リスク度" },
    { key: "info_transparency", label: "情報透明性" },
  ] as const;

  return (
    <CompanyCard title="スコアサマリー">
      <Stack gap="xs">
        {items.map(({ key, label }) => {
          const item = scores[key];
          if (!item) return null;
          return (
            <Group key={key} justify="space-between">
              <Text size="sm" c="#64748B" w={120}>{label}</Text>
              <Group gap="xs">
                <div style={{ width: 120, height: 8, background: "#E2E8F0", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${item.score}%`, height: "100%", background: "#2563EB", borderRadius: 4 }} />
                </div>
                <Text size="sm" fw={600} c="#1E293B" w={36}>{item.score}</Text>
              </Group>
              {item.reason && (
                <Text size="xs" c="#64748B" style={{ flex: 1 }}>{item.reason}</Text>
              )}
            </Group>
          );
        })}
      </Stack>
    </CompanyCard>
  );
}

// ---------------------------------------------------------------------------
// メインコンポーネント
// ---------------------------------------------------------------------------
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

  const { structured, summary, scores } = data;
  const profile = structured?.company_profile;
  const displayName = profile?.name || data.company_url;
  const resultId = data.result_id ? String(data.result_id) : null;
  const companyId = data.company_id ? String(data.company_id) : null;

  return (
    <Tabs defaultValue="result">
      <Tabs.List mb="md">
        <Tabs.Tab value="result">分析結果</Tabs.Tab>
        {companyId && <Tabs.Tab value="history">分析履歴</Tabs.Tab>}
        {companyId && resultId && <Tabs.Tab value="deep">深掘り分析</Tabs.Tab>}
      </Tabs.List>

      {/* 分析結果タブ */}
      <Tabs.Panel value="result">
        <Stack gap="md">
          {/* ヘッダー */}
          <Group justify="space-between" align="flex-start">
            <Stack gap={4}>
              <Text fw={700} size="xl" c="#1E293B">{displayName}</Text>
              <Anchor href={data.company_url} target="_blank" rel="noopener noreferrer" size="sm" c="#2563EB">
                {data.company_url}
              </Anchor>
              {data.analyzed_at && (
                <Text size="xs" c="#64748B">
                  分析日時: {new Date(data.analyzed_at).toLocaleString("ja-JP")}
                  {data.template && data.template !== "general" && ` / テンプレート: ${data.template}`}
                </Text>
              )}
            </Stack>
            <Group gap="xs">
              {resultId && <DownloadMenu resultId={resultId} />}
              {resultId && <ShareButton resultId={resultId} />}
            </Group>
          </Group>

          {/* スコア（T-033）*/}
          {scores && <ScoreCard scores={scores} />}

          {/* 企業概要 */}
          {summary?.overview && (
            <CompanyCard title="企業概要">
              <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>{summary.overview}</Text>
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
              <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>{summary.business_model}</Text>
            </CompanyCard>
          )}

          {/* 事業領域 */}
          {structured?.business_domains && structured.business_domains.length > 0 && (
            <CompanyCard title="事業領域">
              <Group gap="xs">
                {structured.business_domains.map((d) => (
                  <Badge key={d} variant="light" color="blue" size="md">{d}</Badge>
                ))}
              </Group>
            </CompanyCard>
          )}

          {/* プロダクト */}
          {structured?.products && structured.products.length > 0 && (
            <CompanyCard title="プロダクト・サービス">
              <List size="sm" spacing="xs">
                {structured.products.map((p) => <List.Item key={p} c="#1E293B">{p}</List.Item>)}
              </List>
            </CompanyCard>
          )}

          {/* 財務情報 */}
          {structured?.financials && (structured.financials.revenue || structured.financials.operating_income) && (
            <CompanyCard title="財務情報">
              <Stack gap={4}>
                {structured.financials.revenue && <ProfileRow label="売上高" value={structured.financials.revenue} />}
                {structured.financials.operating_income && <ProfileRow label="営業利益" value={structured.financials.operating_income} />}
                {structured.financials.net_income && <ProfileRow label="純利益" value={structured.financials.net_income} />}
                {structured.financials.growth_rate && <ProfileRow label="成長率" value={structured.financials.growth_rate} />}
              </Stack>
            </CompanyCard>
          )}

          {/* SWOT */}
          {summary?.swot && (
            <CompanyCard title="SWOT分析">
              <Stack gap="sm">
                {(summary.swot.strengths ?? []).length > 0 && <SwotSection label="強み (Strengths)" items={summary.swot.strengths ?? []} />}
                {(summary.swot.weaknesses ?? []).length > 0 && <SwotSection label="弱み (Weaknesses)" items={summary.swot.weaknesses ?? []} />}
                {(summary.swot.opportunities ?? []).length > 0 && <SwotSection label="機会 (Opportunities)" items={summary.swot.opportunities ?? []} />}
                {(summary.swot.threats ?? []).length > 0 && <SwotSection label="脅威 (Threats)" items={summary.swot.threats ?? []} />}
              </Stack>
            </CompanyCard>
          )}

          {/* リスク */}
          {summary?.risks && summary.risks.length > 0 && (
            <CompanyCard title="リスク要因">
              <List size="sm" spacing="xs">
                {summary.risks.map((r) => <List.Item key={r} c="#1E293B">{r}</List.Item>)}
              </List>
            </CompanyCard>
          )}

          {/* 競合 */}
          {summary?.competitors && summary.competitors.length > 0 && (
            <CompanyCard title="競合企業（推定）">
              <Group gap="xs">
                {summary.competitors.map((c) => <Badge key={c} variant="light" color="gray" size="md">{c}</Badge>)}
              </Group>
            </CompanyCard>
          )}

          {/* 展望 */}
          {summary?.outlook && (
            <CompanyCard title="今後の展望">
              <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7 }}>{summary.outlook}</Text>
            </CompanyCard>
          )}

          {/* ニュース */}
          {structured?.news && structured.news.length > 0 && (
            <CompanyCard title="ニュース">
              <Stack gap="xs">
                {structured.news.map((item) => (
                  <Stack key={item.title} gap={2}>
                    <Group gap="xs">
                      <Text size="sm" fw={500} c="#1E293B">{item.title}</Text>
                      {item.date && <Text size="xs" c="#64748B">{item.date}</Text>}
                    </Group>
                    {item.summary && <Text size="xs" c="#64748B">{item.summary}</Text>}
                  </Stack>
                ))}
              </Stack>
            </CompanyCard>
          )}

          {/* 差分レポート（T-029）*/}
          {data.diff_report && (
            <CompanyCard title="差分レポート">
              <Alert color="blue" variant="light" mb="xs">前回分析からの変更点</Alert>
              <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                {data.diff_report}
              </Text>
            </CompanyCard>
          )}

          {/* 参照ソース */}
          <CompanyCard title="参照ソース">
            <List size="sm" spacing="xs" listStyleType="none">
              {data.sources.map((s) => (
                <List.Item key={s.url}>
                  <Group gap="xs">
                    <Anchor href={s.url} target="_blank" rel="noopener noreferrer" size="sm" c="#2563EB">
                      {s.title}
                    </Anchor>
                    {s.category && s.category !== "その他" && (
                      <Badge variant="light" color="blue" size="xs">{s.category}</Badge>
                    )}
                  </Group>
                </List.Item>
              ))}
            </List>
          </CompanyCard>

          {/* Markdownレポート */}
          {data.markdown_page && (
            <CompanyCard title="Markdownレポート">
              <details>
                <summary style={{ cursor: "pointer", color: "#64748B", fontSize: 14 }}>
                  レポート全文を表示
                </summary>
                <Text size="sm" c="#1E293B" style={{ lineHeight: 1.7, whiteSpace: "pre-wrap", marginTop: 8 }}>
                  {data.markdown_page}
                </Text>
              </details>
            </CompanyCard>
          )}
        </Stack>
      </Tabs.Panel>

      {/* 分析履歴タブ（T-024）*/}
      {companyId && (
        <Tabs.Panel value="history">
          <HistoryTab companyId={companyId} />
        </Tabs.Panel>
      )}

      {/* 深掘り分析タブ（T-031）*/}
      {companyId && resultId && (
        <Tabs.Panel value="deep">
          <DeepResearchPanel companyId={companyId} resultId={resultId} />
        </Tabs.Panel>
      )}
    </Tabs>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <Group gap="sm">
      <Text size="sm" c="#64748B" w={80}>{label}</Text>
      <Text size="sm" c="#1E293B">{value}</Text>
    </Group>
  );
}

function SwotSection({ label, items }: { label: string; items: string[] }) {
  return (
    <Stack gap={2}>
      <Text size="sm" fw={500} c="#1E293B">{label}</Text>
      <List size="sm" spacing={2}>
        {items.map((item) => <List.Item key={item} c="#1E293B">{item}</List.Item>)}
      </List>
    </Stack>
  );
}
