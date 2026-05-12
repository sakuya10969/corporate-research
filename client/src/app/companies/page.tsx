"use client";

import {
  Anchor,
  Badge,
  Button,
  Container,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { CompanyResponse } from "@/shared/api";
import {
  getListCompaniesApiCompaniesGetQueryKey,
  useListCompaniesApiCompaniesGet,
  useRegisterCompanyApiCompaniesPost,
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

export default function CompaniesPage() {
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useListCompaniesApiCompaniesGet();
  const registerMutation = useRegisterCompanyApiCompaniesPost({
    mutation: {
      onSuccess: () => {
        setUrl("");
        queryClient.invalidateQueries({
          queryKey: getListCompaniesApiCompaniesGetQueryKey(),
        });
      },
    },
  });

  const handleRegister = () => {
    const trimmed = url.trim();
    if (!trimmed || !/^https?:\/\//.test(trimmed)) return;
    registerMutation.mutate({ data: { url: trimmed } });
  };

  const companies: CompanyResponse[] = data?.companies ?? [];

  return (
    <Container size={1100} py="xl">
      <Stack gap="xl">
        <Stack gap="xs" ta="center">
          <Title order={1} c="#1E293B">
            企業一覧
          </Title>
          <Text c="#64748B" size="md">
            登録済み企業の管理と新規企業の登録
          </Text>
        </Stack>

        {/* 企業登録フォーム */}
        <Group gap="sm">
          <TextInput
            placeholder="https://www.example.co.jp/"
            value={url}
            onChange={(e) => setUrl(e.currentTarget.value)}
            style={{ flex: 1 }}
            disabled={registerMutation.isPending}
          />
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={handleRegister}
            loading={registerMutation.isPending}
            disabled={!url.trim() || !/^https?:\/\//.test(url.trim())}
          >
            企業を登録
          </Button>
        </Group>

        {registerMutation.isError && (
          <Text c="red" size="sm">
            登録に失敗しました。URLを確認してください。
          </Text>
        )}

        {/* 企業一覧テーブル */}
        {isLoading ? (
          <Group justify="center" py="xl">
            <Loader size="md" />
          </Group>
        ) : companies.length === 0 ? (
          <Text c="#64748B" ta="center" py="xl">
            登録済みの企業はありません
          </Text>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>企業名</Table.Th>
                <Table.Th>URL</Table.Th>
                <Table.Th>ステータス</Table.Th>
                <Table.Th>最終分析日時</Table.Th>
                <Table.Th>分析回数</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {companies.map((company) => (
                <Table.Tr key={company.company_id}>
                  <Table.Td>
                    <Anchor
                      href={`/companies/${company.company_id}`}
                      size="sm"
                      c="#2563EB"
                    >
                      {company.display_name || company.normalized_url}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="#64748B" lineClamp={1}>
                      {company.primary_url}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <StatusBadge status={company.status} />
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {formatDate(company.last_analyzed_at)}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" ta="center">
                      {company.analysis_count}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}

        <Group justify="center" gap="md">
          <Anchor href="/" size="sm" c="#2563EB">
            ← トップページに戻る
          </Anchor>
        </Group>
      </Stack>
    </Container>
  );
}
