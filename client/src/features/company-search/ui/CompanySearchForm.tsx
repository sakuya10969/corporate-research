"use client";

import { Button, Group, TextInput } from "@mantine/core";
import { IconSearch } from "@tabler/icons-react";
import * as v from "valibot";
import { useState } from "react";
import {
  companySearchSchema,
  type CompanySearchInput,
} from "../model/schema";

type Props = {
  onSubmit: (data: CompanySearchInput) => void;
  loading?: boolean;
};

export function CompanySearchForm({ onSubmit, loading }: Props) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | undefined>();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const result = v.safeParse(companySearchSchema, { company_name: value });
    if (!result.success) {
      setError(result.issues[0]?.message);
      return;
    }
    setError(undefined);
    onSubmit(result.output);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Group align="flex-end" gap="sm">
        <TextInput
          label="企業名"
          placeholder="例: トヨタ自動車"
          value={value}
          onChange={(e) => setValue(e.currentTarget.value)}
          error={error}
          disabled={loading}
          style={{ flex: 1 }}
        />
        <Button
          type="submit"
          loading={loading}
          leftSection={<IconSearch size={16} />}
        >
          分析する
        </Button>
      </Group>
    </form>
  );
}
