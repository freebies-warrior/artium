"use client";

import * as React from "react";

export type ButtonProps =
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "ghost";
    size?: "sm" | "md" | "lg";
    fullWidth?: boolean;
  };

export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center font-semibold rounded-xl transition " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background " +
    "disabled:opacity-50 disabled:pointer-events-none cursor-pointer";

  const sizes: Record<NonNullable<ButtonProps["size"]>, string> = {
    sm: "h-9 px-4 text-sm",
    md: "h-11 px-6 text-sm",
    lg: "h-12 px-8 text-base",
  };

  const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
    primary: "bg-purple-600 text-white hover:bg-purple-700 active:scale-[0.99]",
    secondary: "bg-purple-500/20 text-purple-200 hover:bg-purple-500/30",
    ghost: "bg-transparent text-purple-300 hover:bg-purple-500/20",
  };

  const widthClass = fullWidth ? "w-full" : "";

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${widthClass} ${className}`}
      {...props}
    />
  );
}
