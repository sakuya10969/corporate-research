import { Box, Text } from "@mantine/core";

type Props = {
  title: string;
  children: React.ReactNode;
};

export function CompanyCard({ title, children }: Props) {
  return (
    <Box
      p="md"
      style={{
        backgroundColor: "#FFFFFF",
        border: "1px solid #E2E8F0",
        borderRadius: 8,
      }}
    >
      <Text fw={600} size="lg" mb="sm" c="#1E293B">
        {title}
      </Text>
      {children}
    </Box>
  );
}
