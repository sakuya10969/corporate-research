import * as v from "valibot";

export const companySearchSchema = v.object({
  company_name: v.pipe(
    v.string(),
    v.nonEmpty("企業名を入力してください"),
    v.trim(),
    v.minLength(1, "企業名を入力してください"),
    v.regex(/\S/, "空白のみの入力はできません"),
  ),
});

export type CompanySearchInput = v.InferOutput<typeof companySearchSchema>;
