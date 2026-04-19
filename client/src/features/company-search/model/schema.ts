import * as v from "valibot";

export const companySearchSchema = v.object({
  company_url: v.pipe(
    v.string(),
    v.nonEmpty("企業URLを入力してください"),
    v.trim(),
    v.url("有効なURLを入力してください"),
    v.regex(/^https?:\/\//, "http:// または https:// で始まるURLを入力してください"),
  ),
});

export type CompanySearchInput = v.InferOutput<typeof companySearchSchema>;
