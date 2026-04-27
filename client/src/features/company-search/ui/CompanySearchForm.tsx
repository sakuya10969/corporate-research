"use client";

import {
  Autocomplete,
  Button,
  Group,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { IconRefresh, IconSearch } from "@tabler/icons-react";
import * as v from "valibot";
import { useEffect, useState } from "react";
import type { AnalysisResponse } from "@/shared/api";
import { useSearchCompanyApiSearchGet } from "@/shared/api";
import { companySearchSchema, type CompanySearchInput } from "../model/schema";

type Props = {
  onSubmit: (data: CompanySearchInput & { force_refresh?: boolean; template?: string }) => void;
  loading?: boolean;
  cachedResult?: AnalysisResponse;
};

const TEMPLATES = [
  { value: "general", label: "総合分析" },
  { value: "job_hunting", label: "就活・転職リサーチ" },
  { value: "investment", label: "投資リサーチ" },
  { value: "competitor", label: "競合調査" },
  { value: "partnership", label: "提携先調査" },
];

export function CompanySearchForm({ onSubmit, loading, cachedResult }: Props) {
  const [value, setValue] = useState("");
  const [template, setTemplate] = useState("general");
  const [error, setError] = useState<string | undefined>();
  const [debounced] = useDebouncedValue(value, 400);

  // 企業名検索（F-011）— URL形式でない場合のみ検索
  const isUrl = /^https?:\/\//.test(debounced);
  const { data: searchData } = useSearchCompanyApiSearchGet(
    { q: debounced },
    { query: { enabled: debounced.length >= 2 && !isUrl } }
  );
  const suggestions = (searchData?.results ?? []).map((r) => ({
    value: r.url,
    label: `${r.name} — ${r.url}`,
  }));

  const handleSubmit = (e: React.FormEvent, forceRefresh = false) => {
    e.preventDefault();
    const result = v.safeParse(companySearchSchema, { company_url: value });
    if (!result.success) {
      setError(result.issues[0]?.message);
      return;
    }
    setError(undefined);
    onSubmit({ ...result.output, force_refresh: forceRefresh, template });
  };

  const analyzedAt = cachedResult?.analyzed_at
    ? new Date(cachedResult.analyzed_at).toLocaleString("ja-JP")
    : null;

  return (
    <Stack gap="sm">
      {/* キャッシュ通知バナー（T-022）*/}
      {cachedResult?.is_cached && analyzedAt && (
        <Group
          justify="space-between"
          p="sm"
          style={{ background: "#EFF6FF", borderRadius: 8, border: "1px solid #BFDBFE" }}
        >
          <Text size="sm" c="#1D4ED8">
            前回分析: {analyzedAt}
          </Text>
          <Button
            size="xs"
            variant="light"
            color="blue"
            leftSection={<IconRefresh size={14} />}
            onClick={(e) => handleSubmit(e as unknown as React.FormEvent, true)}
            loading={loading}
          >
            最新情報で更新する
          </Button>
        </Group>
      )}

      <form onSubmit={(e) => handleSubmit(e)}>
        <Stack gap="xs">
          <Group align="flex-end" gap="sm">
            <Autocomplete
              label="企業URL または 企業名"
              placeholder="例: https://www.toyota.co.jp/ または トヨタ"
              value={value}
              onChange={setValue}
              data={suggestions}
              onOptionSubmit={(val) => setValue(val)}
              error={error}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <Select
              label="分析テンプレート"
              data={TEMPLATES}
              value={template}
              onChange={(v) => setTemplate(v ?? "general")}
              disabled={loading}
              w={180}
            />
            <Button
              type="submit"
              loading={loading}
              leftSection={<IconSearch size={16} />}
            >
              分析する
            </Button>
          </Group>
        </Stack>
      </form>
    </Stack>
  );
}
