import type { ButtonHTMLAttributes, ReactNode } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "danger" | "ghost";
}

export function Button({ children, variant = "primary", className = "", ...props }: ButtonProps) {
  return <button className={`button button-${variant} ${className}`.trim()} {...props}>{children}</button>;
}
