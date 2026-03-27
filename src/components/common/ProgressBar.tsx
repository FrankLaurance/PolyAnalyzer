import { Progress, Typography } from "antd";

const { Text } = Typography;

interface ProgressBarProps {
  progress: number;
  message?: string;
  running?: boolean;
}

export default function ProgressBar({ progress, message, running }: ProgressBarProps) {
  const status = running ? "active" : progress >= 100 ? "success" : "normal";

  return (
    <div className="progress-section">
      <Progress percent={Math.round(progress)} status={status} size="small" />
      {message && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {message}
        </Text>
      )}
    </div>
  );
}
