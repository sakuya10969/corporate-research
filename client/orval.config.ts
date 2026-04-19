import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "../server/openapi.json",
    },
    output: {
      target: "./src/shared/api/generated/client.ts",
      schemas: "./src/shared/api/generated/model",
      client: "react-query",
      httpClient: "axios",
      mode: "tags-split",
      override: {
        mutator: {
          path: "./src/shared/api/instance.ts",
          name: "customInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
