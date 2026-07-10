import { Progress, Typography } from "antd";

const { Text } = Typography;

interface ProgressBarProps {
  progress: number;
  message?: string;
  running?: boolean;
  failed?: boolean;
}

export default function ProgressBar({ progress, message, running, failed }: ProgressBarProps) {
  const normalizedProgress = Number.isFinite(progress)
    ? Math.max(0, Math.min(100, progress))
    : 0;
  const hasStarted = running || normalizedProgress > 0 || Boolean(message);

  if (!hasStarted) {
    return null;
  }

  const status = failed
    ? "exception"
    : running
      ? "active"
      : normalizedProgress >= 100
        ? "success"
        : "normal";

  return (
    <div className="progress-section">
      <Progress percent={Math.round(normalizedProgress)} status={status} size="small" />
      {message && (
        <Text type={failed ? "danger" : "secondary"} style={{ fontSize: 12 }}>
          {message}
        </Text>
      )}
    </div>
  );
}
