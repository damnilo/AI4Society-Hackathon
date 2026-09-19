import { APP_NAME } from "@/lib/copy";

type BrandLogoProps = {
  variant?: "sidebar" | "lockup";
};

export function BrandLogo({ variant = "sidebar" }: BrandLogoProps) {
  return (
    <img
      className={`brand-img brand-img-${variant}`}
      src="/brand/nasalter-lockup.png"
      alt={APP_NAME}
    />
  );
}
