export function HubLogo({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1.2" fill="white" />
      <rect x="9" y="1" width="6" height="6" rx="1.2" fill="white" fillOpacity="0.45" />
      <rect x="1" y="9" width="6" height="6" rx="1.2" fill="white" fillOpacity="0.45" />
      <rect x="9" y="9" width="6" height="6" rx="1.2" fill="white" />
    </svg>
  )
}
